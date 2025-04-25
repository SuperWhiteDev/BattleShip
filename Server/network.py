import socket
from typing import Callable
from enum import Enum
from packet import Packet
from log import Log
from settings import DEBUG


class Network:
    class ConnectionStatus(Enum):
        NOT_CONNECTED = 0
        CONNECTED = 1

    class Errors(Enum):
        NAME_ALREADY_IN_USE = 0
        NAME_TOO_LONG = 1
        REACHED_USERS_LIMIT = 2
        UNEXPECTED_PACKET = 3
        UNCORRECT_PACKET = 4

    class ErrorMessages(Enum):
        PLAYER_NOT_IN_ANY_SESSION = 0

    def __init__(
        self,
        conn: socket,
        addr,
        request_handler: Callable[[str], str],
        on_disconnect: Callable[[], None],
    ) -> None:
        self.conn = conn
        self.addr = addr
        self.ip = self.addr[0]
        self.port = self.addr[1]

        self.request_handler = request_handler
        self.on_disconnect = on_disconnect
        self.connection_status: Network.ConnectionStatus = (
            Network.ConnectionStatus.NOT_CONNECTED
        )

    def disconnect(self):
        """
        Cleanly terminates the connection.
        Changing the connection status first ensures that any ongoing loops or attempts to use the connection do not proceed,
        and then closes the socket.
        """
        self.connection_status = Network.ConnectionStatus.NOT_CONNECTED

        if self.conn:
            self.conn.close()

    def set_connected(self):
        self.connection_status = Network.ConnectionStatus.CONNECTED

    def connected(self) -> bool:
        return self.connection_status == Network.ConnectionStatus.CONNECTED

    def get(self, data: str = None) -> Packet:
        if not self.connected():
            return Packet(Packet.Code.UNDEFINED)

        try:
            if data:
                self.send(data)

            response = self.conn.recv(1024)
            response = Packet(response)

            if DEBUG:
                Log.debug(f"Get from {self.ip}:{self.port} - {response}")

            return response
        except socket.timeout:
            return Packet(Packet.Code.UNDEFINED)
        except Exception as e:
            if DEBUG:
                Log.exception("Failed to parse packet from user", e)
            return Packet(Packet.Code.UNDEFINED)

    def send(self, data: Packet) -> bool:
        if not self.connected():
            return Packet(Packet.Code.UNDEFINED)

        if DEBUG:
            Log.debug(f"Send to {self.ip}:{self.port} - {data}")

        try:
            self.conn.send(data.to_bytes())
        except Exception as e:
            if DEBUG:
                Log.exception("An error occurred when sending data to a user", e)
            return False
        else:
            return True

    def handle(self):
        """
        Main loop for processing incoming data on this network connection.
        - Continuously reads incoming packets while the connection is active.
        - Processes each received packet using the provided request_handler callback.
        - Sends the response packet back to the client if one is provided.
        - Breaks the loop on receiving a defined 'undefined' packet (implying disconnection or error).
        - Ensures that the on_disconnect callback is always executed,
          facilitating resource cleanup and further disconnection handling.
        
        This design decouples the packet handling logic from the raw socket operations,
        making it easier to test and extend.
        """
        try:
            while self.connected():
                request = self.get()
                if request.code != Packet.Code.UNDEFINED:
                    response = self.request_handler(request)
                    if response:
                        self.send(response)
                else:
                    # If the packet is undefined, it typically signals a problem or a break condition.
                    break
        finally:
            self.on_disconnect()