from socket import socket
from time import sleep
from enum import Enum
from typing import Optional
from queue import Queue
from threading import Thread
from settings import *
from network import Network
from packet import Packet
from log import Log
from game_session import Session

class User: 
    class UserConnectionStatus(Enum):
        CONNECTED = 0,
        DISCONNECTED = 1
        BANNED = 2
        REACHED_USERS_LIMIT = 3
        REGISTER_REQUIRED = 4
        AUTHORIZATION_REQUIRED = 5

    users = {} # key: Server, value: set[Users]

    waiting_players = Queue()

    def append_user_in_list(server, user) -> None:
        if server in User.users:
            User.users[server].add(user)
        else:
            User.users[server] = set((user,))

    def remove_user_from_list(server, user) -> None:
        if server in User.users:
            if user in User.users[server]:
                User.users[server].remove(user)

    def get_users(server):
        try:
            return User.users[server]
        except KeyError:
            return set()
        
    def get_user_by_name(server, name : str):
        """
            return: object of class User.
        """
        for i, user in enumerate(User.get_users(server)):
            if name.lower() == user.name.lower():
                return user
            
        return None

    @Log.log_logger.catch
    def __init__(self, server, conn : socket, addr) -> None:
        self.server = server
        
        #self.is_connected = True

        self.net = Network(conn, addr, self._handle_user, self.on_disconnect)
        self.net.set_connected()

        # 
        if len(User.get_users(self.server)) > MAX_USERS:
            Log.warning("The connection request was rejected because the maximum number of users has been reached.")
            self.net.send(Packet(Packet.Code.ERROR, {"error_code": Network.Errors.REACHED_USERS_LIMIT.value}))
            self.disconnect_user()
            return

        response = self.net.get()
        if response.code == Packet.Code.USERNAME_AND_ID:
            self.name : str = response.data["name"]
            self.id : str = response.data["uid"]

            self.logger = Log.User(self.net.ip, self.name)

            if User.get_user_by_name(self.server, self.name):
                self.logger.error(f"A user with the same name already exists.")
                self.net.send(Packet(Packet.Code.ERROR, {"error_code": Network.Errors.NAME_ALREADY_IN_USE.value}))
                self.disconnect_user()
                return
            if len(self.name) >= MAX_USER_NAME_LENGTH:
                self.logger.error(f"Username exceeds the maximum length of {MAX_USER_NAME_LENGTH} characters.")
                self.net.send(Packet(Packet.Code.ERROR, {"error_code": Network.Errors.NAME_TOO_LONG.value}))
                self.disconnect_user()
                return
        
            User.append_user_in_list(self.server, self)
            self.logger.info(f"New user connected IP: \"{self.net.ip}\".")
        
            if self.is_in_black_list():
                self.logger.error(f"Disconnecting user because is in black list.")
                self.disconnect_user(True)
                return
        
            self.net.send(Packet(Packet.Code.STATUS, self.UserConnectionStatus.CONNECTED.value))
        else:
            self.disconnect_user()
        
    def is_in_black_list(self):
        black_list = self.server.server_data.black_list.get()
       
        for user in black_list:
            if user["user_name"] == self.name or user["user_id"] == self.id:
                return True
        return False
    
    def is_registred(self) -> bool:
        if self.server.server_data.users.find(self.name):
            return True
        else:
            return False

    def is_logged(self):
        user = self.server.server_data.users.find(self.name)
        if user and user["last_login_id"] == self.id:
            return True
        else:
            return False
    
    def get_ip_address(self):
        return self.net.ip

    def _loggin(self):
        user = self.server.server_data.users.find(self.name)
        if user:
            self.net.send(Packet(Packet.Code.STATUS, self.UserConnectionStatus.AUTHORIZATION_REQUIRED.value))
            
            attemptions = 0
            while attemptions <= 3:
                response = self.net.get()
                if response.code == Packet.Code.PASSWORD and "password" in response.data:
                    password = response.data["password"]

                    if password == user["password"]:
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
        self.net.send(Packet(Packet.Code.STATUS, self.UserConnectionStatus.REGISTER_REQUIRED.value))

        attemptions = 0
        while attemptions <= 3:
            response = self.net.get()
            if response.code == Packet.Code.PASSWORD and "password" in response.data:
                password = response.data["password"]

                self.server.server_data.users.add(self.name, self.id, password)
                self.logger.info("The user has successfully signed in")
                self.net.send(Packet(Packet.Code.OK))
                return True
            else:
                return False
            attemptions += 1
        return False
        
    def disconnect_user(self, is_banned = False):
        try:
            if is_banned:
                self.net.send(Packet(Packet.Code.STATUS, self.UserConnectionStatus.BANNED.value))
            else:
                self.net.send(Packet(Packet.Code.STATUS, self.UserConnectionStatus.DISCONNECTED.value))
        except Exception as e:
            if DEBUG:
                Log.exception("Failed to send 'disconnect' packet to user", e)
            
        self.net.disconnect()
        User.remove_user_from_list(self.server, self)
        
    def ban(self) -> bool:
        try:
            self.server.server_data.black_list.add(self.name, self.id)
        except Exception as e:
            Log.exception("An error occurred when adding a player to the list of banned players", e)
        self.disconnect_user()

    def unban(self) -> bool:
        try:
            self.server.server_data.black_list.remove(self.name)
        except Exception as e:
            Log.exception("An error occurred when removing a player from the banned players list", e)
    
    def on_disconnect(self):
        try:
            self.disconnect_user()
        except Exception as e:
            pass
        finally:
            try:
                self.logger.info(f"User has been disconnected.")
            except AttributeError:
                pass

    @Log.log_logger.catch
    def _handle_user(self, request) -> Optional[Packet]:
        if not self.net.connected():
            return
        try:
            if self.is_registred():
                if not self.is_logged():
                    if not self._loggin():
                        return None    
            else:
                if not self._register():
                    return None

            # User.waiting_players.put(self)
            
            # if User.waiting_players.qsize() >= 2:
            #     player1 = User.waiting_players.get()
            #     player2 = User.waiting_players.get()
            
            #     session = Session(self.server, [player1, player2])
            #     session.start()
            if request.code == Packet.Code.PING:
                if self.is_in_black_list():
                    self.disconnect_user(True)
                    return
                        
                return Packet(Packet.Code.OK)
            if request.code == Packet.Code.STATUS:
                if request.data == self.UserConnectionStatus.DISCONNECTED.value:
                    return None
        except ConnectionResetError:
            pass
        except Exception as e:
            self.logger.exception(f"An error occurred while processing requests from user", e)   
        
        return None
    def handle_user(self):
        Thread(target=self.net.handle, daemon=True).start()
        pass#Thread(target=self._handle_user, daemon=True).start()