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
    class ServerStatus(Enum):
        CONNECTED = 0
        BANNED = 1
        REACHED_USERS_LIMIT = 2

    def __init__(self, user : User, request_handler: Callable[[str], str]) -> None:
        self.user = user

        self.request_handler = request_handler
        self.connection_status : Network.ConnectionStatus = Network.ConnectionStatus.NOT_CONNECTED

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

            response = self.get(Packet(Packet.Code.USERNAME_AND_ID, {"name": self.user.name, "uid": self.user.uid}))
            if response.code == Packet.Code.STATUS:
                if response.data == Network.ServerStatus.CONNECTED.value:
                    print("Succesfully connected to the server")
                    self.connection_status = Network.ConnectionStatus.CONNECTED

                    Thread(target=self.handle, daemon=True).start()

                    return True
                elif response.data == Network.ServerStatus.BANNED.value:
                    print("You has been banned on this server.")
                    self.socket.close()
                    return False
                elif response.data == Network.ServerStatus.REACHED_USERS_LIMIT.value:
                    print("The server is full at the moment.")
                    self.socket.close()
                    return False
            elif response.code == Packet.Code.ERROR:
                print("Failed to connect to the server!")
                self.connection_status = Network.ConnectionStatus.NOT_CONNECTED
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
                self.send("DISCONNECT")
            except:
                pass

            print("Disconnected from the server.")
            self.disconnect()

    
    def get(self, data : str = None) -> Packet:
        try:
            if data:
                self.send(data)
            else:
                self.send(Packet(Packet.Code.PING, None))
            
            response = Packet(self.socket.recv(1024))

            return response
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Error checking server status: {e}")
            return None
    
    def send(self, data : Packet) -> bool:
        try:
            self.socket.send(data.to_bytes())
        except Exception:
            return False
        else:
            return True
    
    