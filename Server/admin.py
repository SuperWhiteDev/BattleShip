import socket
from threading import Thread
from time import sleep, time
from commands import Commands
from settings import ADMIN_FILE_TERMINAL_FILE, LOGGING_ADMIN_FILE_TERMINAL, ADMIN_SOCKET_TERMINAL_PORT, ADMIN_SOCKET_MAX_CONNECTIONS, LOGGING_ADMIN_SOCKET_TERMINAL
from log import Log
from auth import Authentication

class Admin:
    def __init__(self, server) -> None:
        self.server = server

    def _handle_command(self, command : str) -> str:
        lower_command = command.lower()
        if lower_command == "help":
            output = Commands.help(self.server, command)
        elif lower_command == "users":
            output = Commands.users_list(self.server, command)
        elif lower_command == "ban-list":
            output = Commands.ban_list(self.server, command)
        elif lower_command == "white-list":
            output = Commands.white_list(self.server, command)
        elif lower_command == "sessions":
            output = Commands.sessions_list(self.server, command)
        elif lower_command.startswith("ban"):
            output = Commands.ban_user(self.server, command)
        elif lower_command.startswith("unban"):
            output = Commands.unban_user(self.server, command)
        elif lower_command.startswith("disconnect"):
            output = Commands.disconnect_user(self.server, command)
        elif lower_command.startswith("stop-session"):
            output = Commands.stop_session(self.server, command)
        elif lower_command == "delete-data":
            output = Commands.delete_data(self.server, command)
        elif lower_command == "all-users":
            output = Commands.all_users(self.server, command)
        elif lower_command.startswith("delete-user"):
            output = Commands.delete_user(self.server, command)
        elif lower_command.startswith("add-admin-user"):
            output = Commands.add_admin_user(self.server, command)
        elif lower_command == "stop":
            output = Commands.stop_server(self.server, command)
        elif lower_command == "restart":
            output = Commands.restart_server(self.server, command)
        else:
            output = f"Unknown command: \"{command}\". Enter \"help\" to see commands list."
            
        if output:
            return output
        else:
            return f"Error: while handling command \"{command}\"!"

    @Log.log_logger.catch
    def run_admin_terminal(self) -> None:    
        """
        Фугкция для обработки команд администратора.
        """
        def auth():
            if Authentication.is_available():
                while not Authentication.login(print, input):
                    pass
            else:
                Authentication.register(print, input)
        
        sleep(3)
        auth()

        last_time = time()

        while not self.server.is_stopped():
            try:
                command = input("").strip()

                if time() - last_time >= 300:
                    auth()

                last_time = time()
                
                print(self._handle_command(command))
            except Exception:
                continue
       
    @Log.log_logger.catch
    def run_file_terminal(self) -> None:
        def init():
            open(ADMIN_FILE_TERMINAL_FILE, "w").close()
        def read() -> list[str]:
            try:
                with open(ADMIN_FILE_TERMINAL_FILE, "r") as f:
                    f.seek(read.position)
                    lines = f.readlines()
                    read.position = f.tell()
                    return lines
            except FileNotFoundError:
                init()
                return []
        def out(string : str) -> None:
            with open(ADMIN_FILE_TERMINAL_FILE, "a") as f:
                for line in string.split("\n"):
                    f.write(">" + line + "\n")
        def auth():
            def custom_input(string : str) -> str:
                out(string)
                while not self.server.is_stopped():
                    lines = read()
                    for line in lines:
                        if not line.startswith(">"):
                            return line.strip()
                    sleep(0.1)
                return ""
            if Authentication.is_available():
                while not Authentication.login(out, custom_input):
                    pass
            else:
                Authentication.register(out, custom_input)

        read.position = 0

        init()

        auth()

        last_time = time()

        while not self.server.is_stopped():
            sleep(0.5)
            try:
                lines = read()
                for line in lines:
                    if not line.startswith(">"):
                        if time() - last_time >= 300:
                            auth()

                        last_time = time()
                
                        line = line.strip()

                        if LOGGING_ADMIN_FILE_TERMINAL:
                            Log.warning(f"Executing the \"{line}\" command with the file terminal.")

                        out(self._handle_command(line))
            except Exception as e:
                Log.exception("An error occurred while executing the commands in the file terminal", e)
                continue

    @Log.log_logger.catch
    def run_socket_terminal(self) -> None:
        def connection_handler(client_socket, client_address):
            def auth():
                def custom_input(string):
                    while not self.server.is_stopped():
                        inp = client_socket.recv(1024).decode("UTF-8")
                        return inp
                    return ""
                if Authentication.is_available():
                    while not Authentication.login(lambda string: client_socket.send(string.encode("UTF-8")), custom_input):
                        pass
                else:
                    Authentication.register(lambda string: client_socket.send(string.encode("UTF-8")), custom_input)

            auth()

            last_time = time()

            Log.warning(f"Socket Terminal - New connection opened. Client IP: \"{client_address[0]}:{client_address[1]}\"")
            try:
                while not self.server.is_stopped():
                    command = client_socket.recv(1024).decode("UTF-8").strip()
                    if not command:
                        break

                    if time() - last_time >= 300:
                        auth()

                    last_time = time()

                    if LOGGING_ADMIN_SOCKET_TERMINAL:
                        Log.warning(f"Executing the \"{command}\" command with the socket terminal.")
                    client_socket.send(self._handle_command(command).encode("UTF-8"))
            except Exception:
                pass
            finally:
                if client_socket:
                    client_socket.close()
                Log.warning(f"Socket Terminal - connection with \"{client_address[0]}:{client_address[1]}\" has been closed.")
            

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:     
            s.bind(("localhost", ADMIN_SOCKET_TERMINAL_PORT))
            s.listen(ADMIN_SOCKET_MAX_CONNECTIONS)
            s.settimeout(1.0)
        
            while not self.server.is_stopped():
                try:
                    client_socket, client_address = s.accept()
                    Thread(target=connection_handler, args=(client_socket, client_address), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    Log.exception("An error occurred while executing the commands in the socket terminal", e)
                    continue


        
            
            