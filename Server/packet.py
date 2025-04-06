from enum import Enum
from pickle import dumps, loads
class Packet:
    class Code(Enum):
        OK = 0
        ERROR = 1
        PING = 2

    def __init__(self, code : "Code", data = None) -> None:
        self.code = code
        self.data = None

    def get_code(self):
        return self.code
    def get_data(self):
        return self.data
    def set_code(self, code : "Code"):
        self.code = code
    def set_data(self, data):
        self.data = data

    def to_bytes(self) -> bytes:
        if not (0 <= self.code <= 255):
            raise ValueError("The code must be a valid value between 0 and 255")
        code = bytes([self.code])
        
        if self.data:
            return b"H"+code+dumps(self.data)
        else:
            return b"H"+code
        
    def parse(self, packet: bytes) -> None:
        if packet[0:1] != b"H":
            raise ValueError("This package is not valid!")
        self.code = packet[1]

        if len(packet) > 2:
            self.data = loads(packet[2:])
        else:
            self.data = None



    