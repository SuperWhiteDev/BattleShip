import socket
from queue import Queue
from threading import Thread
from typing import Callable, Optional
from enums import ConnectionStatus, UserConnectionStatus, Errors
from contextlib import suppress
from time import sleep
from user import User
from packet import Packet
from select import select

class Network:
    def __init__(self, user: User, request_handler: Callable[[str], str]) -> None:
        self.user = user

        self.request_handler = request_handler
        self.connection_status: ConnectionStatus = (
            ConnectionStatus.NOT_CONNECTED
        )

        self.is_authorised = False

        self.set_default_packet()
        self.next_send_packets = Queue(25)

    def connect(self, ip: str, port: int, max_attempts: int = 5) -> bool:
        if not max_attempts:
            print("Failed to connect to the server!")
            self.connection_status = ConnectionStatus.NOT_CONNECTED
            return False
        try:
            print(f"Connecting to the server IP: {ip}, PORT: {port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((ip, port))

            self.connection_status = ConnectionStatus.CONNECTING

            response = self.get(
                Packet(
                    Packet.Code.USERNAME_AND_ID,
                    {"name": self.user.name, "uid": self.user.uid},
                )
            )
            if response.code == Packet.Code.STATUS:
                if response.data == UserConnectionStatus.CONNECTED.value:
                    print("Succesfully connected to the server")
                    self.connection_status = ConnectionStatus.CONNECTED

                    Thread(target=self.handle, daemon=True).start()

                    return True
                elif response.data == UserConnectionStatus.BANNED.value:
                    print("You has been banned on this server.")
                    self.disconnect()
                    return False
            elif response.code == Packet.Code.ERROR:
                if response.data["error_code"] == Errors.REACHED_USERS_LIMIT.value:
                    print(
                        "Error connecting to the server because server is full at the moment."
                    )
                    self.disconnect()
                    return False
                elif (
                    response.data["error_code"] == Errors.NAME_ALREADY_IN_USE.value
                ):
                    print(
                        "Error connecting to the server because another user under your name is already connected to the server"
                    )
                    self.disconnect()
                    return False
                elif response.data["error_code"] == Errors.NAME_TOO_LONG.value:
                    print(
                        "Error connecting to the server because your username exceeds the username length limit for a user on the server"
                    )
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
        return self.connect(ip, port, max_attempts - 1)

    def disconnect(self):
        self.connection_status = ConnectionStatus.NOT_CONNECTED

        if self.socket:
            self.socket.close()

    def connected(self) -> bool:
        return self.connection_status == ConnectionStatus.CONNECTED

    def connecting(self) -> bool:
        return self.connection_status == ConnectionStatus.CONNECTING

    def authorised(self) -> bool:
        return self.is_authorised

    def set_authorised(self, state: bool) -> None:
        self.is_authorised = state

    def set_default_packet(self, packet: Optional[Packet] = None) -> None:
        if packet:
            self.default_packet = packet
        else:
            self.default_packet = Packet(Packet.Code.PING, None)
    
    def delay_send(self, packet : Optional[Packet]) -> None:
        self.next_send_packets.put(packet)

    def handle(self):
        try:
            while self.connected():
                request = self.get()
                if request:
                    if request.code == Packet.Code.UNDEFINED:
                        print("It seems the server doesn't work now.")
                        break
                    else:
                        response = self.request_handler(request)
                        if response:
                            self.send(response)
        finally:
            with suppress(Exception):
                self.send(Packet.Code.STATUS, UserConnectionStatus.DISCONNECTED)

            print("Disconnected from the server.")
            self.disconnect()

    def _flush_socket(self):
        while True:
            ready_to_read, _, _ = select([self.socket], [], [], 0)
            if ready_to_read:
                try:
                    flushed = self.socket.recv(1024)
                    if flushed:
                        return flushed
                    else:
                        break
                except socket.error:
                    break
            else:
                break
        return None

    def get(self, data: str = None) -> Packet:
        if not self.connected() and not self.connecting():
            return Packet(Packet.Code.UNDEFINED)

        try:
            buffer = self._flush_socket()
            if buffer:
                return Packet(buffer)
            
            if data:
                self.send(data)
            elif not self.next_send_packets.empty():
                self.send(self.next_send_packets.get())
            elif self.default_packet:
                self.send(self.default_packet)
            else:
                self.send(Packet(Packet.Code.PING, None))

            resp = self.socket.recv(1024)
            response = Packet(resp)

            # print(f"Get {response}")

            return response
        except socket.timeout:
            print("Error: Timeout. Most likely the server is overloaded or not working at the moment")
            return Packet(Packet.Code.UNDEFINED)
        except Exception as e:
            print(f"An error occurred while waiting for a response from the server: {e}")
            return Packet(Packet.Code.UNDEFINED)

    def send(self, data: Packet) -> bool:
        if not self.connected() and not self.connecting():
            return False
        
        try:
            self.socket.send(data.to_bytes())
        except Exception as e:
            print(f"Error when sending {e}")
            return False
        else:
            return True
