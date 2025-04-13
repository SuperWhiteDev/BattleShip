import socket
from threading import Thread
from typing import Callable
from enum import Enum
from time import sleep
from user import User
from packet import Packet

class Network:
    class ConnectionStatus(Enum):
        NOT_CONNECTED = 0
        CONNECTED = 1
        CONNECTING = 2
    class Errors(Enum):
        NAME_ALREADY_IN_USE = 0
        NAME_TOO_LONG = 1
        REACHED_USERS_LIMIT = 2
    class UserConnectionStatus(Enum):
        CONNECTED = 0,
        DISCONNECTED = 1
        BANNED = 2
        REACHED_USERS_LIMIT = 3
        REGISTER_REQUIRED = 4
        AUTHORIZATION_REQUIRED = 5

    def __init__(self, user : User, request_handler: Callable[[str], str]) -> None:
        self.user = user

        self.request_handler = request_handler
        self.connection_status : Network.ConnectionStatus = Network.ConnectionStatus.NOT_CONNECTED

        self.is_authorised = False

    def connect(self, ip: str, port: int, max_attempts: int = 5) -> bool:
        if not max_attempts:
            print("Failed to connect to the server!")
            self.connection_status = Network.ConnectionStatus.NOT_CONNECTED
            return False
        try:
            print(f"Connecting to the server IP: {ip}, PORT: {port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((ip, port))

            self.connection_status = Network.ConnectionStatus.CONNECTING

            response = self.get(Packet(Packet.Code.USERNAME_AND_ID, {"name": self.user.name, "uid": self.user.uid}))
            
            if response.code == Packet.Code.STATUS:
                if response.data == Network.UserConnectionStatus.CONNECTED.value:
                    print("Succesfully connected to the server")
                    self.connection_status = Network.ConnectionStatus.CONNECTED

                    Thread(target=self.handle, daemon=True).start()

                    return True
                elif response.data == Network.UserConnectionStatus.BANNED.value:
                    print("You has been banned on this server.")
                    self.disconnect()
                    return False
            elif response.code == Packet.Code.ERROR:
                if response.data["error_code"] == self.Errors.REACHED_USERS_LIMIT.value:
                    print("Error connecting to the server because server is full at the moment.")
                    self.disconnect()
                    return False
                elif response.data["error_code"] == self.Errors.NAME_ALREADY_IN_USE.value:
                    print("Error connecting to the server because another user under your name is already connected to the server")
                    self.disconnect()
                    return False
                elif response.data["error_code"] == self.Errors.NAME_TOO_LONG.value:
                    print("Error connecting to the server because your username exceeds the username length limit for a user on the server")
                    self.disconnect()
                    return False
            else:
                print("Failed to connect to the server!")
                self.disconnect()
                return False
        except Exception as e:
            print(e)
        
        print(f"Failed connect to the server IP: {ip}, PORT: {port}.")
        sleep(1.0)

        print("Attempting to reconnect...")
        return self.connect(ip, port, max_attempts-1)
        

    def disconnect(self):
        self.connection_status = Network.ConnectionStatus.NOT_CONNECTED

        if self.socket:
            self.socket.close()

    def connected(self) -> bool:
        return self.connection_status == Network.ConnectionStatus.CONNECTED
    
    def connecting(self) -> bool:
        return self.connection_status == Network.ConnectionStatus.CONNECTING
    
    def authorised(self) -> bool:
        return self.is_authorised
    
    def set_authorised(self, state : bool) -> None:
        self.is_authorised = state
        
    def handle(self):
        try:
            while self.connected():
                request = self.get()
                if request:
                    response = self.request_handler(request)
                    if response:
                        self.send(response)
                else:
                    print("It seems the server doesn't work now.")
                    break            
        finally:
            try:
                self.send(Packet.Code.STATUS, Network.UserConnectionStatus.DISCONNECTED)
            except:
                pass

            print("Disconnected from the server.")
            self.disconnect()

    
    def get(self, data : str = None) -> Packet:
        if not self.connected() and not self.connecting():
            return Packet(Packet.Code.UNDEFINED)
        
        try:
            if data:
                self.send(data)
            else:
                self.send(Packet(Packet.Code.PING, None))
            
            resp = self.socket.recv(1024)
            response = Packet(resp)

            return response
        except socket.timeout:
            return Packet(Packet.Code.UNDEFINED)
        except Exception as e:
            print(f"Error checking server status: {e}")
            return Packet(Packet.Code.UNDEFINED)
    
    def send(self, data : Packet) -> bool:
        if not self.connected() and not self.connecting():
            return False
        
        try:
            self.socket.send(data.to_bytes())
        except Exception as e:
            print(f"Error when sending {e}")
            return False
        else:
            return True
    
    