from socket import socket
from enum import Enum
from typing import Optional
from queue import Queue
from threading import Thread
from contextlib import suppress
from settings import MAX_USERS, MAX_USER_NAME_LENGTH, DEBUG
from network import Network
from packet import Packet
from log import Log
from game_session import Session

class User:
    # Enum for representing different states of a user's connection and required operations.
    class UserConnectionStatus(Enum):
        CONNECTED = 1                 # User has successfully connected and passed initial checks.
        DISCONNECTED = 2              # User has been disconnected from the server.
        BANNED = 3                    # User is banned and should be rejected at connection.
        REACHED_USERS_LIMIT = 4       # The server has reached the maximum allowed concurrent users.
        REGISTER_REQUIRED = 5         # User must register; no previous account exists.
        AUTHORIZATION_REQUIRED = 6    # User must be authorized (e.g., via password verification).
        FIND_NEW_SESSION = 8          # Request from the user to initiate a new game session search.
        LEAVE_SESSION = 9             # Request from the user to leave the current game session.

    # Global registry mapping each server instance to a set of its User objects.
    users = {}  # key: Server, value: set[Users]

    # A queue to hold players waiting for a game session assignment.
    waiting_players = Queue()

    @staticmethod
    def append_user_in_list(server, user) -> None:
        """
        Register the user with the given server.
        This global mapping helps efficiently track all connected users and is useful for operations
        like broadcasting messages or enforcing limits.
        """
        if server in User.users:
            User.users[server].add(user)
        else:
            User.users[server] = set((user,))

    @staticmethod
    def remove_user_from_list(server, user) -> None:
        """
        Cleanly remove a user from the server's registry.
        This will help prevent stale references and memory leaks when users disconnect.
        """
        if server in User.users:
            if user in User.users[server]:
                User.users[server].remove(user)

    @staticmethod
    def get_users(server):
        """
        Safely retrieve all users connected to a specific server.
        Returns an empty set if no users are registered under this server.
        """
        try:
            return User.users[server]
        except KeyError:
            return set()

    @staticmethod
    def get_user_by_name(server, name: str):
        """
        Locate a user by their name in a case-insensitive manner.
        This is crucial for enforcing unique usernames and handling login requests.
        """
        for i, user in enumerate(User.get_users(server)):
            if name.lower() == user.name.lower():
                return user
        return None

    @Log.log_logger.catch
    def __init__(self, server, conn: socket, addr) -> None:
        """
        When a new client connects:
        - Initialize a network wrapper for handling asynchronous communication.
        - Set the initial authorization state and session-related flags.
        - Enforce maximum user limits by checking the server's user registry.
        - Perform a handshake expecting a USERNAME_AND_ID packet to establish identity.
        - Validate uniqueness and the allowed length for the provided username.
        - Check against the blacklist before finalizing the connection.
        """
        self.server = server

        # Instantiate the network abstraction, handing over the low-level connection,
        # and specify callbacks for handling messages and disconnection events.
        self.net = Network(conn, addr, self._handle_user, self.on_disconnect)
        self.net.set_connected()

        # The user starts as unauthorized; they must either login or register.
        self.is_authorised = False

        # Session management: the user might be waiting to join a game session.
        self.session = None
        self.is_looking_for_session = True

        # Enforce global maximum users: if exceeded, immediately refuse the connection.
        if len(User.get_users(self.server)) > MAX_USERS:
            Log.warning(
                "The connection request was rejected because the maximum number of users has been reached."
            )
            self.net.send(
                Packet(
                    Packet.Code.ERROR,
                    {"error_code": Network.Errors.REACHED_USERS_LIMIT.value},
                )
            )
            self.disconnect_user()
            return

        # The initial handshake: expect a USERNAME_AND_ID packet from the client.
        response = self.net.get()
        if response.code == Packet.Code.USERNAME_AND_ID:
            self.name: str = response.data["name"]
            self.id: str = response.data["uid"]

            # Initialize a user-specific logger for contextual debugging and tracing.
            self.logger = Log.User(self.net.ip, self.name)

            # Enforce unique usernames to avoid conflicts during session control.
            if User.get_user_by_name(self.server, self.name):
                self.logger.error("A user with the same name already exists.")
                self.net.send(
                    Packet(
                        Packet.Code.ERROR,
                        {"error_code": Network.Errors.NAME_ALREADY_IN_USE.value},
                    )
                )
                self.disconnect_user()
                return

            # Validate the username length to prevent resource abuse or UI issues.
            if len(self.name) >= MAX_USER_NAME_LENGTH:
                self.logger.error(
                    f"Username exceeds the maximum length of {MAX_USER_NAME_LENGTH} characters."
                )
                self.net.send(
                    Packet(
                        Packet.Code.ERROR,
                        {"error_code": Network.Errors.NAME_TOO_LONG.value},
                    )
                )
                self.disconnect_user()
                return

            # Successfully register the user in the global registry.
            User.append_user_in_list(self.server, self)
            self.logger.info(f'New user connected IP: "{self.net.ip}".')

            # Immediately check if the user is blacklisted to prevent banned users from accessing the server.
            if self.is_in_black_list():
                self.logger.error("Disconnecting user because is in black list.")
                self.disconnect_user(True)
                return

            # Inform the client that the connection is established.
            self.net.send(
                Packet(Packet.Code.STATUS, self.UserConnectionStatus.CONNECTED.value)
            )
        else:
            # If handshake data is incorrect or incomplete, cut the connection.
            self.disconnect_user()

    def is_in_black_list(self):
        black_list = self.server.server_data.black_list.get()

        for user in black_list:
            if user["user_name"] == self.name or user["user_id"] == self.id:
                return True
        return False

    def is_registred(self) -> bool:
        if not self.is_authorised:
            if self.server.server_data.users.find(self.name):
                return True
            else:
                return False
        else:
            return True

    def is_logged(self):
        if not self.is_authorised:
            user = self.server.server_data.users.find(self.name)
            if user:
                if user["last_login_id"] == self.id:
                    self.is_authorised = True
                    return True
                else:
                    return False
        return True

    def get_ip_address(self):
        return self.net.ip

    def _loggin(self):
        """
        Execute an authentication loop by requesting a password from the client.
        Up to three attempts are allowed—this helps protect against brute forcing while offering a user-friendly window.
        On success, the login details are updated; failure results in disconnecting the connection.
        """
        user = self.server.server_data.users.find(self.name)
        if user:
            # Notify the client that a password is required.
            self.net.send(
                Packet(
                    Packet.Code.STATUS,
                    self.UserConnectionStatus.AUTHORIZATION_REQUIRED.value,
                )
            )

            attemptions = 0
            while attemptions <= 3:
                response = self.net.get()
                if (
                    response.code == Packet.Code.PASSWORD
                    and "password" in response.data
                ):
                    password = response.data["password"]

                    if password == user["password"]:
                        self.is_authorised = True
                        self.server.server_data.users.update_login(self.name, self.id)
                        self.logger.info("The user has successfully logged in")
                        self.net.send(Packet(Packet.Code.OK))
                        return True
                    else:
                        self.net.send(Packet(Packet.Code.ERROR))
                else:
                    return False
                attemptions += 1

        self.disconnect_user()
        return False

    def _register(self):
        """
        Handle the user registration process:
         - Instruct the client to provide a password via a packet.
         - Allow multiple attempts for resilience against transient errors.
         - Upon success, persist the new user data and mark the connection as authorized.
        """
        self.net.send(
            Packet(
                Packet.Code.STATUS, self.UserConnectionStatus.REGISTER_REQUIRED.value
            )
        )

        attemptions = 0
        while attemptions <= 3:
            response = self.net.get()
            if response.code == Packet.Code.PASSWORD and "password" in response.data:
                password = response.data["password"]

                self.is_authorised = True
                self.server.server_data.users.add(self.name, self.id, password)
                self.logger.info("The user has successfully signed in")
                self.net.send(Packet(Packet.Code.OK))
                return True
            else:
                return False
        return False

    def disconnect_user(self, is_banned=False):
        """
        Gracefully disconnect the user.
         - Optionally flag the disconnection as due to a ban.
         - Attempt to communicate the disconnect status before shutting down the network connection.
         - Remove the user's trace from the global registry to free up server resources.
        """
        try:
            if is_banned:
                self.net.send(
                    Packet(Packet.Code.STATUS, self.UserConnectionStatus.BANNED.value)
                )
            else:
                self.net.send(
                    Packet(
                        Packet.Code.STATUS, self.UserConnectionStatus.DISCONNECTED.value
                    )
                )
        except Exception as e:
            if DEBUG:
                Log.exception("Failed to send 'disconnect' packet to user", e)

        self.net.disconnect()
        User.remove_user_from_list(self.server, self)

    def ban(self) -> bool:
        try:
            self.server.server_data.black_list.add(self.name, self.id)
        except Exception as e:
            Log.exception(
                "An error occurred when adding a player to the list of banned players",
                e,
            )
        self.disconnect_user()

    def unban(self) -> bool:
        try:
            self.server.server_data.black_list.remove(self.name)
        except Exception as e:
            Log.exception(
                "An error occurred when removing a player from the banned players list",
                e,
            )

    def on_disconnect(self):
        with suppress(Exception):
            self.disconnect_user()
            self.logger.info("User has been disconnected.")

    @Log.log_logger.catch
    def connect_session(self, session: Session = None) -> None:
        if not session:
            self.session = Session.connect(self)
        else:
            self.session = session
        if self.session:
            self.is_looking_for_session = False

    def is_in_session(self) -> bool:
        return True if self.session else False

    def disconnect_session(self, find_new_session: bool = False):
        self.session = None
        self.is_looking_for_session = find_new_session

    @Log.log_logger.catch
    def _handle_user(self, request) -> Optional[Packet]:
        """
        Core callback to handle incoming packets from the user.
         - Enforces registration and login before processing commands.
         - Initiates session assignment if the user is looking for a game.
         - Handles heartbeat (PING) packets, status changes, and session data routing.
         - Returns error packets when a command isn’t applicable (e.g., sending session data without an active session).
        Any exceptions during processing are caught and logged for diagnostic purposes.
        """
        if not self.net.connected():
            return
        try:
            # Authentication workflow: ensure the user is either registered and logged in or completes registration.
            if self.is_registred():
                if not self.is_logged():
                    if not self._loggin():
                        return None
            else:
                if not self._register():
                    return None

            if not self.session and self.is_looking_for_session:
                self.connect_session()

            # Process incoming requests based on their packet type.
            if request.code == Packet.Code.PING:
                # A PING packet tests connection health; also, immediately disconnect if the user appears blacklisted.
                if self.is_in_black_list():
                    self.disconnect_user(True)
                    return None

                return Packet(Packet.Code.OK)
            if request.code == Packet.Code.STATUS:
                if request.data == self.UserConnectionStatus.DISCONNECTED.value:
                    return None
                if request.data == self.UserConnectionStatus.FIND_NEW_SESSION.value:
                    self.disconnect_session(True)
                    return Packet(Packet.Code.OK)
                if request.data == self.UserConnectionStatus.LEAVE_SESSION.value:
                    self.disconnect_session(False)
                    return Packet(Packet.Code.OK)

            if request.code == Packet.Code.SESSION_DATA:
                # Forward session-related data to the user's current game session.
                if self.session:
                    self.session.add_data_packet(self, request)
                    return None
                else:
                    return Packet(
                        Packet.Code.ERROR,
                        {
                            "error_code": Network.Errors.UNEXPECTED_PACKET.value,
                            "msg": Network.ErrorMessages.PLAYER_NOT_IN_ANY_SESSION.value,
                        },
                    )
        except Exception as e:
            self.logger.exception(
                "An error occurred while processing requests from user", e
            )

        return None

    def handle_user(self):
        Thread(target=self.net.handle, daemon=True).start()
