from time import sleep
from config import Config
from utils import clear_console
from network import Network
from user import User
from enums import GameDataCode, GameDataType
from ui import UI
from battle_field import BattleField
from packet import Packet

class BattleShip:
    def __init__(self) -> None:
        self.config = Config()
        self.user = User(self.config)
        self.ui = UI(self)
        
        # Game variables
        self.is_in_session = False
        self.battle_field = None

    def create_user(self):
        self.user.set_name(input("Enter your username: "))

    def get_server(self) -> tuple[str, int]:
        def display_available_servers():
            print("Servers available:")

            for i, server in enumerate(self.config.servers):
                print(f"{i + 1}. {server['name']}")

        display_available_servers()

        print('\n"add". Add new server')

        while True:
            user_in = (
                input('Enter server id or "add" to append new server to list: ')
                .strip()
                .lower()
            )

            if user_in == "add":
                self.add_new_server()
                clear_console()
                return self.get_server()
            else:
                try:
                    server_id = int(user_in) - 1
                except ValueError:
                    continue

                try:
                    server = self.config.servers[server_id]
                except IndexError:
                    continue
                else:
                    return (server["ip"], int(server["port"]))

    def add_new_server(self) -> None:
        name = input("Enter what you want to name the server: ")
        ip = input("Enter server IPv4 address: ").strip()
        port = (
            input("Enter server port(enter to use default port 64221): ").strip()
            or 64221
        )

        self.config.servers.add_server(name, ip, port)

    def play_game(self):
        if not self.user.is_valid():
            self.create_user()

        server_ip, server_port = self.get_server()

        self.connection = Network(self.user, self.server_request_handler)
        self.connection.connect(server_ip, server_port)

        if self.connection.connected():
            # Thread(target=self.connection.handle).start()

            self.handle_game()
        else:
            print("Not connected")

    def handle_game(self):
        started = False

        self.battle_field = None

        while self.connection.connected():
            if not self.connection.authorised():
                sleep(1.0)
                continue
            else:
                if not started:
                    started = True
                    print(
                        "Game running... (type 'disconnect' to leave from the server)"
                    )
            
            if self.is_in_session:
                sleep(1.0)
                continue
            
            user_in = input("> ")
            user_in_lower = user_in.strip().lower()
            if user_in_lower == "disconnect":
                self.connection.disconnect()
                sleep(1)
            elif user_in_lower == "play" and not self.is_in_session:
                self.connect_to_session()
            elif user_in_lower == "leave" and self.is_in_session:
                self.leave_session()

    def server_request_handler(self, request: Packet):
        if request.code == Packet.Code.OK:
            self.connection.set_authorised(True)
            sleep(3)
        elif request.code == Packet.Code.STATUS:
            self.server_handle_user_connection_status(request.data)
        elif request.code == Packet.Code.SESSION_DATA:
            response = self.handle_session_connection(request.data)
            sleep(0.5)
            return response
        elif request.code == Packet.Code.ERROR:
            error = request.data

            self.handle_error(error)
        elif request.code == Packet.Code.UNDEFINED:
            self.connection.disconnect()
            return None
        else:
            print(f"Unknown code from server: {request.code}")

        return None

    def handle_error(self, error : dict) -> None:
        error_code = ""
        error_msg = ""

        if "error_code" in error:
            if error["error_code"] == Network.Errors.UNEXPECTED_PACKET.value:
                error_code = "<Unexpected packet get sended>:"
            if error["error_code"] == Network.Errors.UNCORRECT_PACKET.value:
                error_code = "<Uncorrect packet ged sended>:"
        if "msg" in error:
            if error["msg"] == Network.ErrorMessages.PLAYER_NOT_IN_ANY_SESSION.value:
                #error_msg = "Attempting to access a session to which the player is not connected!"
                self.on_session_closed()
                return None
            else:
                error_msg = error["msg"]

        print(f"Error: {error_code} {error_msg}")
    def server_handle_user_connection_status(
        self, status: Network.UserConnectionStatus
    ):
        # print(f"Status is {status}")
        if status == Network.UserConnectionStatus.BANNED.value:
            print("You have been banned on this server.")
        if status == Network.UserConnectionStatus.DISCONNECTED.value:
            print("You has been disconnected from the server.")
        elif status == Network.UserConnectionStatus.REGISTER_REQUIRED.value:
            print(
                "To connect to this server you need to register your name on it so that no one else can connect using your name"
            )

            while True:
                password = input("Enter password: ")
                if password == "":
                    continue

                response = self.connection.get(
                    Packet(Packet.Code.PASSWORD, {"password": password})
                )

                if response.code == Packet.Code.OK:
                    print("Succesfully connected to the server")
                    self.connection.set_authorised(True)
                    break
                elif response.code == Packet.Code.ERROR:
                    if isinstance(response.data, dict) and "error" in response.data:
                        print(response.data["error"])
                    else:
                        print("Not correct. Try again.")
                else:
                    return None
        elif status == Network.UserConnectionStatus.AUTHORIZATION_REQUIRED.value:
            while True:
                password = input("Enter the password for this account: ")
                if password == "":
                    continue

                response = self.connection.get(
                    Packet(Packet.Code.PASSWORD, {"password": password})
                )

                if response.code == Packet.Code.OK:
                    print("Succesfully connected to the server")
                    self.connection.set_authorised(True)
                    break
                elif response.code == Packet.Code.ERROR:
                    if isinstance(response.data, dict) and "error" in response.data:
                        print(response.data["error"])
                    else:
                        print("Not correct credintials. Try again.")
                else:
                    return None
        else:
            return None
    
    def on_session_connected(self):
        if not self.is_in_session:
            self.connection.set_default_packet(
                Packet(
                    Packet.Code.SESSION_DATA,
                    {"code": GameDataCode.GET_DATA.value, "args": None},
                )
            )
            self.is_in_session = True

            self.battle_field = None

            self.player_shooting = False

            self.game_ended = False

    def on_session_closed(self):
        if self.is_in_session:
            print("Game stopped.")
            self.connection.set_default_packet()
            self.is_in_session = False

            self.battle_field = None

            print("Enter 'play' if you want to find a new sesion")

    def connect_to_session(self):
        self.connection.delay_send(Packet(Packet.Code.STATUS, Network.UserConnectionStatus.FIND_NEW_SESSION.value))

    def leave_session(self):
        self.connection.delay_send(Packet(Packet.Code.STATUS, Network.UserConnectionStatus.LEAVE_SESSION.value))

    def send_to_session(self, data: dict) -> None:
        if self.is_in_session:
            self.connection.delay_send(Packet(Packet.Code.SESSION_DATA, {"code": GameDataCode.POST_DATA.value, "data": data}))

    def handle_session_connection(self, data: dict):
        if "code" in data:
            code = data["code"]

            if code == GameDataCode.SESSION_STARTED.value:
                print(f"Connected to session #{data['session_id']}.\nStarting game.")

                self.on_session_connected()
            elif code == GameDataCode.SESSION_CLOSED.value:
                self.on_session_closed()
            elif code == GameDataCode.POST_DATA.value:
                if data["data"]:
                    data = data["data"]

                    if data["type"] == GameDataType.BATTLE_FIELD_REQUIRED.value:
                        if self.battle_field is None:
                            self.battle_field = self.ui.get_battle_field()

                        self.send_to_session({"type": GameDataType.BATTLE_FIELD.value, "field": self.battle_field.field})
                        
                    if data["type"] == GameDataType.NOT_YOUR_TURN.value:
                        clear_console()
                        print("Wait for another player to attack.")
                        print("Your field:")
                        self.ui.display_field(self.battle_field)

                    if data["type"] == GameDataType.SHOOT_STATE.value:
                        shoot_state = data["shoot_state"]
                        if shoot_state == BattleField.ShootState.HIT.value:
                            clear_console()

                            print("You hit! You can shoot again.")
                            row, col = self.ui.get_shoot_coordinates(BattleField(data["field"]))

                            self.send_to_session({"type": GameDataType.COORDINATE.value, "coords": {"row": row, "col": col}})
                        elif shoot_state == BattleField.ShootState.MISS.value:
                            clear_console()
                            print("You missed.")

                            self.battle_field = BattleField(data["field"])

                            sleep(0.5)
                        elif shoot_state == BattleField.ShootState.ALREADY_SHOT.value:
                            print("You already shot at this cell. Try again.")
                            sleep(0.7)
                    if data["type"] == GameDataType.BATTLE_FIELD.value:
                        clear_console()

                        print(f"{data["player"]} field:")
                        row, col = self.ui.get_shoot_coordinates(BattleField(data["field"]))
                        self.send_to_session({"type": GameDataType.COORDINATE.value, "coords": {"row": row, "col": col}})

                    if data["type"] == GameDataType.RESULTS.value:
                        if not self.game_ended:
                            if data["winner"] == "you":
                                print("Congratulations, you destroyed all the enemy ships.")
                            else:
                                print(f"All your ships have been destroyed by player {data["winner"]}")
                            self.game_ended = True
                            
            elif code == GameDataCode.GET_DATA.value:
                print(f"Server gets data: {data}")
            elif code == GameDataCode.COMPLETE.value:
                ...
            elif code == GameDataCode.WAITING.value:
                clear_console()
                if "player" in data:
                    print(f"Waiting for the players: {data["player"]}.")
                else:
                    print("Waiting other players.")
            return None
        else:
            return Packet(Packet.Code.ERROR, {"error_code": Network.Errors.UNCORRECT_PACKET.value})
        
    
    def start(self):
        """
        Starts the game by launching the main menu.
        The UI loop is handled by the ui module.
        """
        self.ui.main_menu()