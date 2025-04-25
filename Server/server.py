#!/usr/bin/env python3
import socket
import os
from threading import Thread
from time import sleep
from log import Log
from settings import (
    INIT_ATTEMPTS,
    HOST,
    PORT,
    MAX_USERS,
    ADMIN_TERMINAL,
    ADMIN_FILE_TERMINAL,
    ADMIN_FILE_TERMINAL_FILE,
    ADMIN_SOCKET_TERMINAL,
    ADMIN_SOCKET_TERMINAL_PORT,
)
from user import User
from admin import Admin
from data import Data

class Server:
    @Log.log_logger.catch
    def __init__(self) -> None:
        """
        Server constructor that performs initial setup:
        - Initializes logging.
        - Sets initial server state flags.
        - Loads server-specific data.
        - Attempts to bind a listening socket with a retry mechanism.
        
        The retry loop (based on INIT_ATTEMPTS) prevents abrupt failures if the socket
        is temporarily unavailable, ensuring graceful startup under adverse conditions.
        """
        Log.init()
        Log.info("Server initialization...")

        self.server_running = False   # Indicates ongoing server activity
        self.server_stop = False      # Flag for requesting server shutdown
        self.is_initialized = False   # Marks successful initialization

        # Attempt to load any necessary data for the server
        try:
            self.server_data = Data()
        except Exception as e:
            Log.exception("Failed to initialize server", e)
            return

        # Try binding the server socket repeatedly, handling potential OS/port issues
        for _ in range(INIT_ATTEMPTS):
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((HOST, PORT))
                self.server_socket.listen(MAX_USERS)
                # Setting a timeout allows periodic checks for shutdown signals without blocking indefinitely
                self.server_socket.settimeout(1.0)
            except OSError as e:
                sleep(1.0)  # Provide a pause before retrying to avoid rapid-fire failures
                Log.exception("Failed to initialize server", e)
                continue
            else:
                self.is_initialized = True
                Log.info("The server has been initialized successfully.")
                break

    @Log.log_logger.catch
    def init_admin_interface(self):
        """
        Initializes various administrative interfaces for managing the server.
        These interfaces enable different remote or local management channels (terminal, file-based, or socket-based)
        all running concurrently on separate threads, allowing for asynchronous admin control without blocking the main server loop.
        """
        self.admin = Admin(self)

        # Launch a command-line admin interface if enabled, suitable for live server management.
        if ADMIN_TERMINAL:
            Thread(target=self.admin.run_admin_terminal, daemon=True).start()
            Log.info("Terminal Admin Interface has been successfully started.")

        # File-based interface to read commands from a file; useful for scripted or external admin commands.
        if ADMIN_FILE_TERMINAL:
            Thread(target=self.admin.run_file_terminal, daemon=True).start()
            Log.info(
                f'File Terminal Admin Interface has been successfully started. You can use it by path "{os.path.join(os.path.dirname(os.path.abspath(__file__)), ADMIN_FILE_TERMINAL_FILE)}"'
            )

        # Socket-based admin interface to manage the server over a network connection on a dedicated port.
        if ADMIN_SOCKET_TERMINAL:
            Thread(target=self.admin.run_socket_terminal, daemon=True).start()
            Log.info(
                f"Socket Terminal Admin Interface has been successfully started. It is listening on localhost:{ADMIN_SOCKET_TERMINAL_PORT}."
            )

    @Log.log_logger.catch
    def run(self) -> None:
        """
        Primary entry point to start the server's operational cycle.
        If initialization succeeded, it sets the running flag, starts admin interfaces,
        logs the bound address, and enters the main request-handling loop.
        """
        if not self.is_initialized:
            return

        self.server_running = True

        # Initiate interfaces that support different types of administrative control.
        self.init_admin_interface()

        Log.info("The server has been started successfully.")

        # Log the actual IP and port the server is using (could be different based on system configurations)
        server_ip, server_port = self.server_socket.getsockname()
        Log.info(f"Server is running at {server_ip}:{server_port}.")

        # Begin accepting incoming user connections in a loop.
        self.server_request_handler()

    @Log.log_logger.catch
    def server_request_handler(self):
        """
        Main loop to accept and handle incoming connection requests from clients.
        Uses a non-blocking loop by periodically timing out when no connection is available,
        so it can properly respond to shutdown requests.
        Upon accepting a connection, it instantiates a User object that encapsulates individual session handling.
        The finally block ensures clean shutdown by disconnecting all active users and releasing resources.
        """
        try:
            Log.log_logger.info("Waiting for a connection request from users.")

            while not self.server_stop and self.server_running:
                try:
                    # Accept a new connection request; will raise a timeout if no new connection is made.
                    conn, addr = self.server_socket.accept()

                    # Create a new user session instance for further handling
                    user = User(self, conn, addr)
                    user.handle_user()
                except socket.timeout:
                    # Timeout allows the loop to re-check shutdown conditions on each iteration.
                    continue
                except OSError:
                    # An OS error is indicative of a severe issue; break out of the loop.
                    break
                except Exception as e:
                    Log.exception(
                        "An exception occurred while processing user connection requests",
                        e,
                    )
        except Exception:
            pass
        finally:
            Log.info("Shutting down the server...")

            # Retrieve all active users and disconnect them gracefully
            users = list(User.get_users(self))
            for user in users:
                user.disconnect_user()

            # Clean up server data and close the socket to free up the port
            del self.server_data
            self.server_socket.close()
            self.server_running = False

            # Returning False here could signal a halted state externally if needed.
            return False

    def initialized(self) -> bool:
        """
        Indicates whether the server completed its startup sequence.
        Useful to ensure clients or external scripts do not attempt to run an uninitialized server.
        """
        return self.is_initialized

    def stop(self):
        """
        Sets the shutdown flag for the server, triggering graceful termination in the request handler loop.
        """
        self.server_stop = True

    def is_running(self) -> bool:
        """
        Returns True if the server is actively running.
        """
        return self.server_running

    def is_stopped(self) -> bool:
        """
        Determines if the server is stopped or in the process of shutting down.
        """
        return self.server_stop or not self.server_running

def main():
    """
    Main entry point of the application.
    Instantiates the server and, if initialization was successful, starts its operation.
    """
    server = Server()

    if server.initialized():
        server.run()

if __name__ == "__main__":
    main()
