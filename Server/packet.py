from enum import Enum
from pickle import dumps, loads

class Packet:
    class Code(Enum):
        UNDEFINED = 0
        OK = 1
        ERROR = 2
        PING = 3
        STATUS = 4
        USERNAME_AND_ID = 5
        PASSWORD = 6

        @classmethod
        def to_code(cls, value : int) -> "Code":
            for member in cls:
                if member.value == value:
                    return member
            return cls.UNDEFINED

    def __init__(self, *args) -> None:
        if len(args) == 1 and isinstance(args[0], bytes):
            self.parse(args[0])
        elif len(args) == 1 and isinstance(args[0], self.Code):
            self.code = args[0]
            self.data = None
        elif len(args) == 2:
            self.code = args[0]
            self.data = args[1]
        else:
            self.code = Packet.Code.UNDEFINED
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
        if not (0 <= self.code.value <= 255):
            raise ValueError("The code must be a valid value between 0 and 255")
        code = bytes([self.code.value])
        
        if self.data:
            return b"H"+code+dumps(self.data)
        else:
            return b"H"+code
        
    def parse(self, packet: bytes) -> None:
        if packet[0:1] != b"H":
            raise ValueError("This package is not valid!")
        
        self.code = Packet.Code.to_code(int(packet[1]))

        if len(packet) > 2:
            self.data = loads(packet[2:])
        else:
            self.data = None



    