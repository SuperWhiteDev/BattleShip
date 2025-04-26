import socket
from threading import Thread
from time import sleep, time
from commands import Commands
from settings import (
    ADMIN_FILE_TERMINAL_FILE,
    LOGGING_ADMIN_FILE_TERMINAL,
    ADMIN_SOCKET_TERMINAL_PORT,
    ADMIN_SOCKET_MAX_CONNECTIONS,
    LOGGING_ADMIN_SOCKET_TERMINAL,
)
from log import Log
from auth import Authentication


class Admin:
    def __init__(self, server) -> None:
        """
        Initializes an Admin instance for the given server.
        
        :param server: The server object which this admin instance will manage.
        """
        self.server = server

    def _handle_command(self, command: str) -> str:
        """
        Processes a given command by dispatching it to the corresponding handler in the Commands module.
        
        :param command: The raw command string entered by an administrator.
        :return: A string output that reflects the result of the command execution.
        """
        lower_command = command.lower()
        if lower_command == "help":
            output = Commands.help(self.server, command)
        elif lower_command == "users":
            output = Commands.users_list(self.server, command)
        elif lower_command.startswith("user"):
            output = Commands.user(self.server, command)
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
        elif lower_command.startswith("session"):
            output = Commands.session(self.server, command)
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
            found = False
            for user_command, func in self.server.user_commands.items():
                if lower_command.startswith(user_command.lower()):
                    found = True
                    output = Commands.call(func, command)
            if not found:
                output = f'Unknown command: "{command}". Enter "help" to see commands list.'

        return output if output is not None else f'Error: while handling command "{command}"!'

    @Log.log_logger.catch
    def run_admin_terminal(self) -> None:
        """
        Runs the command-line (terminal) admin interface.
        
        This method continuously waits for input from the admin via the terminal.
        It also includes an authentication routine which re-prompts for credentials every 300 seconds.
        Received commands are processed using _handle_command, and the output is printed.
        """
        # Inner function to perform authentication using standard input/output.
        def auth():
            if Authentication.is_available():
                # Loop until authentication is successful.
                while not Authentication.login(print, input):
                    pass
            else:
                # If login is not available, perform registration.
                Authentication.register(print, input)

        sleep(3)  # Small delay to allow the system to initialize before starting authentication
        auth()  # Authenticate administrator before processing commands

        last_time = time()  # Timestamp for periodic reauthentication

        while not self.server.is_stopped():
            try:
                # Read command from the terminal input and strip extra whitespace
                command = input("").strip()

                # Re-authenticate if 300 seconds have passed since the last auth check
                if time() - last_time >= 300:
                    auth()

                last_time = time()

                # Process the command and print out the response
                print(self._handle_command(command))
            except Exception:
                # In case of any exception (e.g., input error), continue the loop
                continue

    @Log.log_logger.catch
    def run_file_terminal(self) -> None:
        """
        Runs the file-based admin interface.
        
        This interface monitors a designated file for admin commands.
        Commands are read from the file, processed, and the responses are appended
        to the file (each response line is prefixed with '>').
        It also supports authentication similar to the terminal version.
        """
        # Initialize the file terminal by clearing any existing contents.
        def init():
            open(ADMIN_FILE_TERMINAL_FILE, "w").close()

        # Function to read new lines from the command file.
        def read() -> list[str]:
            try:
                with open(ADMIN_FILE_TERMINAL_FILE, "r") as f:
                    f.seek(read.position)
                    lines = f.readlines()
                    read.position = f.tell()  # Update the file pointer position
                    return lines
            except FileNotFoundError:
                init()
                return []

        # Function to write a given string to the file, prefixing each line with '>'.
        def out(string: str) -> None:
            with open(ADMIN_FILE_TERMINAL_FILE, "a") as f:
                for line in string.split("\n"):
                    f.write(">" + line + "\n")

        # Inner authentication routine using file input/output
        def auth():
            def custom_input(string: str) -> str:
                out(string)
                while not self.server.is_stopped():
                    lines = read()
                    for line in lines:
                        # Return the first input line that is not prefixed by '>'
                        if not line.startswith(">"):
                            return line.strip()
                    sleep(0.1)
                return ""

            if Authentication.is_available():
                while not Authentication.login(out, custom_input):
                    pass
            else:
                Authentication.register(out, custom_input)

        # Initialize file reading pointer
        read.position = 0
        init()  # Clear the file terminal file at startup
        auth()  # Authenticate before processing commands

        last_time = time()  # Timestamp for periodic reauthentication

        while not self.server.is_stopped():
            sleep(0.5)  # Polling delay to avoid busy-waiting
            try:
                lines = read()
                for line in lines:
                    # Process only lines that are not output lines (without '>').
                    if not line.startswith(">"):
                        if time() - last_time >= 300:
                            auth()

                        last_time = time()

                        line = line.strip()

                        if LOGGING_ADMIN_FILE_TERMINAL:
                            Log.warning(f'Executing the "{line}" command with the file terminal.')

                        # Process command and output the result back into the file.
                        out(self._handle_command(line))
            except Exception as e:
                Log.exception("An error occurred while executing the commands in the file terminal", e)
                continue

    @Log.log_logger.catch
    def run_socket_terminal(self) -> None:
        """
        Runs the socket-based admin interface.
        
        This interface listens on a dedicated port for incoming connections.
        Each connection spawns a new handler thread that performs authentication and then
        processes incoming commands from the client, returning the result via the socket.
        """
        # Inner function to handle an individual client connection.
        def connection_handler(client_socket, client_address):
            # Inner authentication function for socket connection.
            def auth():
                def custom_input(string):
                    # Waits for the client to send input over the socket
                    while not self.server.is_stopped():
                        inp = client_socket.recv(1024).decode("UTF-8")
                        return inp
                    return ""

                if Authentication.is_available():
                    # Loop until authentication over the socket is successful.
                    while not Authentication.login(
                        lambda string: client_socket.send(string.encode("UTF-8")), custom_input
                    ):
                        pass
                else:
                    # Perform registration if login is not available.
                    Authentication.register(
                        lambda string: client_socket.send(string.encode("UTF-8")), custom_input
                    )

            auth()  # Authenticate the client upon connection

            last_time = time()  # Timestamp for periodic reauthentication

            Log.warning(f'Socket Terminal - New connection opened. Client IP: "{client_address[0]}:{client_address[1]}"')
            try:
                while not self.server.is_stopped():
                    # Wait for command sent from client over the socket
                    command = client_socket.recv(1024).decode("UTF-8").strip()
                    if not command:
                        break

                    # Re-authenticate if needed (every 300 seconds)
                    if time() - last_time >= 300:
                        auth()

                    last_time = time()

                    if LOGGING_ADMIN_SOCKET_TERMINAL:
                        Log.warning(f'Executing the "{command}" command with the socket terminal.')
                    
                    # Process the command and send the response encoded as UTF-8
                    client_socket.send(self._handle_command(command).encode("UTF-8"))
            except Exception:
                # Exception in the client handling loop is caught silently
                pass
            finally:
                if client_socket:
                    client_socket.close()
                Log.warning(f'Socket Terminal - connection with "{client_address[0]}:{client_address[1]}" has been closed.')

        # Create a TCP/IP socket for the socket terminal
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", ADMIN_SOCKET_TERMINAL_PORT))
            s.listen(ADMIN_SOCKET_MAX_CONNECTIONS)
            s.settimeout(1.0)  # Timeout on accept to allow checking for server stop condition

            while not self.server.is_stopped():
                try:
                    client_socket, client_address = s.accept()
                    # Start a new daemon thread for each client connection
                    Thread(
                        target=connection_handler,
                        args=(client_socket, client_address),
                        daemon=True,
                    ).start()
                except socket.timeout:
                    # Timeout exception; retry accepting connections
                    continue
                except Exception as e:
                    Log.exception("An error occurred while executing the commands in the socket terminal", e)
                    continue
