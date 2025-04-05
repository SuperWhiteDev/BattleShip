import socket
import os
from threading import Thread
from time import sleep
from log import Log
from settings import *
from user import User
from admin import Admin
from data import Data

class Server:
    @Log.log_logger.catch
    def __init__(self) -> None:
        Log.init()
        Log.info("Server initialization...")

        self.server_running = False
        self.server_stop = False
        self.is_initialized = False

        try:
            self.server_data = Data()
        except Exception as e:      
            Log.exception("Failed to initialize server", e)
            return

        for _ in range(INIT_ATTEMPTS):
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((HOST, PORT))
                self.server_socket.listen(MAX_USERS)
                self.server_socket.settimeout(1.0)
            except OSError as e:
                sleep(1.0)
                Log.exception("Failed to initialize server", e)
                continue
            else:
                self.is_initialized = True

                Log.info("The server has been initialized successfully.")
                break
    
    @Log.log_logger.catch
    def init_admin_interface(self):
        self.admin = Admin(self)
        
        if ADMIN_TERMINAL:
            Thread(target=self.admin.run_admin_terminal, daemon=True).start()
            Log.info("Terminal Admin Interface has been succefully started.")

        if ADMIN_FILE_TERMINAL:
            Thread(target=self.admin.run_file_terminal, daemon=True).start()
            Log.info(f"File Terminal Admin Interface has been succefully started. You can use it by path \"{os.path.join(os.path.dirname(os.path.abspath(__file__)), ADMIN_FILE_TERMINAL_FILE)}\"")
        if ADMIN_SOCKET_TERMINAL:
            Thread(target=self.admin.run_socket_terminal, daemon=True).start()
            Log.info(f"Socket Terminal Admin Interface has been succefully started. It is listening localhost:{ADMIN_SOCKET_TERMINAL_PORT}.")

    @Log.log_logger.catch
    def run(self) -> None:
        if not self.is_initialized:
            return
        
        self.server_running = True
        
        self.init_admin_interface()

        Log.info("The server has been started successfully.")

        server_ip, server_port = self.server_socket.getsockname()
        Log.info(f"Server is running at {server_ip}:{server_port}.") 

        self.server_request_handler()   
    
    @Log.log_logger.catch
    def server_request_handler(self):
        try:
            Log.log_logger.info("Waiting for a connection request from users.")

            while not self.server_stop and self.server_running:
                try:
                    conn, addr = self.server_socket.accept()
                    
                    if len(User.get_users(self)) < MAX_USERS:
                        user = User(self, conn, addr)
                        user.handle_user()
                    else:
                        Log.warning("The connection request was rejected because the maximum number of users has been reached.")
                        conn.send("REACHED_USERS_LIMIT".encode("UTF-8"))
                        sleep(0.01)
                        conn.close()
                except socket.timeout:
                    continue
                except OSError:
                    break
                except Exception as e:
                    Log.exception("An exception occurred while processing user connection requests", e)
        except Exception as e:
            pass
        finally:
            Log.info("Shutting down the server...")

            users = list(User.get_users(self))
            for user in users:
                user.disconnect_user()

            del self.server_data

            self.server_socket.close()
            
            self.server_running = False

            return False

        return True

    def initialized(self) -> bool:
        return self.is_initialized    
    
    def stop(self):
        self.server_stop = True

    def is_running(self) -> bool:
        return self.server_running
    
    def is_stopped(self) -> bool:
        return self.server_stop or not self.server_running
    
def main():
    server = Server()
    
    if server.initialized():
        server.run()

    #sleep(2.0)

if __name__ == "__main__":
    main()