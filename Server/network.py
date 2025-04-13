import socket
from threading import Thread
from typing import Callable
from enum import Enum
from packet import Packet
from log import Log

class Network:
    class ConnectionStatus(Enum):
        NOT_CONNECTED = 0
        CONNECTED = 1
    class Errors(Enum):
        NAME_ALREADY_IN_USE = 0
        NAME_TOO_LONG = 1
        REACHED_USERS_LIMIT = 2

    def __init__(self, conn : socket, addr, request_handler: Callable[[str], str], on_disconnect : Callable[[], None]) -> None:
        self.conn = conn
        self.addr = addr
        self.ip = self.addr[0]
        
        self.request_handler = request_handler
        self.on_disconnect = on_disconnect
        self.connection_status : Network.ConnectionStatus = Network.ConnectionStatus.NOT_CONNECTED

    def disconnect(self):
        self.connection_status = Network.ConnectionStatus.NOT_CONNECTED

        if self.conn:
            self.conn.close()

    def set_connected(self):
        self.connection_status = Network.ConnectionStatus.CONNECTED

    def connected(self) -> bool:
        return self.connection_status == Network.ConnectionStatus.CONNECTED
    
    def get(self, data : str = None) -> Packet:
        if not self.connected():
            return Packet(Packet.Code.UNDEFINED)
        
        try:
            if data:
                self.send(data)
            
            response = self.conn.recv(1024)
            response = Packet(response)

            return response
        except socket.timeout:
            return Packet(Packet.Code.UNDEFINED)
        except Exception as e:
            #Log.exception("Failed to parse packet from user", e)
            return Packet(Packet.Code.UNDEFINED)
    
    def send(self, data : Packet) -> bool:
        if not self.connected():
            return Packet(Packet.Code.UNDEFINED)
        
        try:
            self.conn.send(data.to_bytes())
        except Exception as e:
            #Log.exception("An error occurred when sending data to a user", e)
            return False
        else:
            return True

    def handle(self):
        try:
            while self.connected():
                request = self.get()
                if request.code != Packet.Code.UNDEFINED:
                    response = self.request_handler(request)
                    if response:
                        self.send(response)
                else:
                    break     
        finally:
            self.on_disconnect()

    # def recieve_data(self) -> str:
    #     if not self.is_connected or self.conn.fileno() != -1:
    #         data = self.conn.recv(1024).decode("UTF-8")
    #         return data
    #     else:
    #         try:
    #             self.logger.error("Error: Failed to receive because, connection is already closed.")
    #         except AttributeError:
    #             pass
    #         return None
        
    # def send_data(self, string : str) -> None:
    #     #print("SEdning")
    #     self.conn.send(string.encode("UTF-8"))
    #     #print("Sended")