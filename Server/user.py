from json import dump as jdump, load as jload
from socket import socket
from typing import Union
from queue import Queue
from threading import Thread
from settings import *
from log import Log
from game_session import Session

class User: 
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
        
        self.is_connected = True

        self.conn = conn
        self.addr = addr

        self.ip = self.addr[0]

        data = self.conn.recv(1024).decode("UTF-8")
        data = data.split(",")
        self.name : str = data[0]
        self.id : str = data[1]
        self.logger = Log.User(self.ip, self.name)

        if User.get_user_by_name(self.server, self.name):
            self.logger.error(f"A user with the same name already exists.")
            self.send_data("NAME_ALREADY_IN_USE")
            self.disconnect_user()
            return
        if len(self.name) >= MAX_USER_NAME_LENGTH:
            self.logger.error(f"Username exceeds the maximum length of {MAX_USER_NAME_LENGTH} characters.")
            self.send_data("NAME_TOO_LONG")
            self.disconnect_user()
            return
        
        User.append_user_in_list(self.server, self)
        self.logger.info(f"New user connected IP: \"{self.ip}\".")
        
        if self.is_in_black_list():
            self.logger.error(f"Disconnecting user because is in black list.")
            self.disconnect_user(True)
            return

    def recieve_data(self) -> str:
        if not self.is_connected or self.conn.fileno() != -1:
            data = self.conn.recv(1024).decode("UTF-8")
            return data
        else:
            try:
                self.logger.error("Error: Failed to receive because, connection is already closed.")
            except AttributeError:
                pass
            return None
        
    def send_data(self, string : str) -> None:
        #print("SEdning")
        self.conn.send(string.encode("UTF-8"))
        #print("Sended")
        
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

    def _loggin(self):
        user = self.server.server_data.users.find(self.name)
        if user:
            self.send_data("PASSWORD_REQUIRED")
            
            attemptions = 0
            while attemptions <= 3:
                password = self.recieve_data()
                if password.startswith("PASSWORD "):
                    password = password.replace("PASSWORD ", "")
            
                    if password == user["password"]:
                        self.server.server_data.users.update_login(self.name, self.id)
                        self.logger.info("The user has successfully logged in")
                        return True
                else:
                    self.send_data("UNCORRECT")
                attemptions += 1

        self.disconnect_user()
        return False

    def _register(self):
        self.send_data("REGISTER_REQUIRED")
        
        attemptions = 0
        while attemptions <= 3:
            password = self.recieve_data()
            if password.startswith("PASSWORD "):
                password = password.replace("PASSWORD ", "")
                self.server.server_data.users.add(self.name, self.id, password)
                self.logger.info("The user has successfully signed in")
                return True
            else:
                self.send_data("UNCORRECT")
        return False
        
    def disconnect_user(self, is_banned = False):
        try:
            if is_banned:
                self.send_data("BANNED")
            else:
                self.send_data("DISCONNECT")
        except Exception:
            pass
            
        self.conn.close()
        self.is_connected = False
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
    
    @Log.log_logger.catch
    def _handle_user(self):
        if not self.is_connected:
            return
        try:
            if self.is_registred():
                if not self.is_logged():
                    if not self._loggin():
                        return
            else:
                if not self._register():
                    return

            self.conn.send("OK".encode("UTF-8"))

            User.waiting_players.put(self)
            
            if User.waiting_players.qsize() >= 2:
                player1 = User.waiting_players.get()
                player2 = User.waiting_players.get()
            
                session = Session(self.server, [player1, player2])
                session.start()
            while True:
                data = self.recieve_data()

                if data:
                    if DEBUG:
                        self.logger.debug(f"Recivied data [{data}]")
                    if data == "PING":
                        if self.is_in_black_list():
                            self.disconnect_user(True)
                            return
                        
                        self.send_data("OK")
                        
                    if data == "DISCONNECT":
                        break
                else:
                    break
        except ConnectionResetError:
            pass
        except Exception as e:
            self.logger.exception(f"An error occurred while processing requests from user", e)   
        finally:
            try:
                self.disconnect_user()
            except Exception as e:
                pass
            finally:
                self.logger.info(f"User has been disconnected.")   

    def handle_user(self):
        Thread(target=self._handle_user, daemon=True).start()