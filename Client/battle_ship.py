import sys
from threading import Thread
from pyfiglet import figlet_format
from time import sleep
from config import Config
from utils import clear_console
from network import Network
from user import User
from packet import Packet

class BattleShip:
    def __init__(self) -> None:
        self.config = Config()
        self.user = User(self.config)

    def main_menu(self):    
        clear_console()

        try:
            while True:
                action = self.start_menu()
                if action == "exit":
                    break

                sleep(2.0)
                clear_console()
        except KeyboardInterrupt:
            pass

    def start_menu(self):
            print(figlet_format("BattleShip Game"))

            try:
                while True:
                    inp = input("Enter \"Play\" to play the game: ").strip().lower()

                    if inp == "play":
                        self.play_game()
                        return
                    elif inp == "settings":
                        self.settings_menu()
            except KeyboardInterrupt:
                return "exit"

    def settings_menu(self):
        def option_me():
            options = {"Name": self.user.name}
            
            for i, (option, value) in enumerate(options.items()):
                print(f"{i+1}. {option.capitalize()} - {value}.")
        
            inp = input("Enter what option you want to change: ").strip().lower()

            try:
                index = int(inp)
            except ValueError:
                index = -1

            if inp == "name" or index == 1:
                self.user.set_name(input("Enter your new name: ").strip())

        options = ["Me"]

        for i, option in enumerate(options):
            print(f"{i+1}. {option}.")

        while True:
            try:
                option = input("Enter option or \"back\" to return to start menu: ").strip().lower()
            
                if option == "back":
                    break
                
                if option == options[0].lower() or int(option) == 1:
                    option_me()
            except Exception as e:
                print(e)
                continue

    def create_user(self):
        self.user.set_name(input("Enter your username: "))

    def get_server(self) -> tuple[str, int]:
        def display_available_servers():
            print("Servers available:")

            for i, server in enumerate(self.config.servers):
                print(f"{i+1}. {server["name"]}")
                
        display_available_servers()
    
        print("\n\"add\". Add new server")
    
        while True:
            user_in = input("Enter server id or \"add\" to append new server to list: ").strip().lower()

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
        port = input("Enter server port(enter to use default port 64221): ").strip() or 64221

        self.config.servers.add_server(name, ip, port)

    def play_game(self):
        if not self.user.is_valid():
            self.create_user()
        
        server_ip, server_port = self.get_server()

        self.connection = Network(self.user, self.server_request_handler)
        self.connection.connect(server_ip, server_port)
        
        if self.connection.connected():
            #Thread(target=self.connection.handle).start()
            self.handle_game()
        else:
            print("Not connected")

    def handle_game(self):
        started = False
        while self.connection.connected():
            if not self.connection.authorised():
                sleep(1.0)
                continue
            else:
                if not started:
                    started = True
                    print("Game running... (type 'disconnect' to leave from the server)")

            user_input = input("> ").strip().lower()
            if user_input == "disconnect":
                self.connection.disconnect()
                sleep(1)

    def server_request_handler(self, request : Packet):
        if request.code == Packet.Code.OK:
            self.connection.set_authorised(True)
            sleep(5)
        elif request.code == Packet.Code.STATUS:
            self.server_handle_user_connection_status(request.data)
        #elif request.startswith("Session started"):
        #    self.handle_session_connection(int(response.split("ID=")[1]))
        #elif request == "Session closed":   
        #    print("Game stopped.")
        elif request.code == Packet.Code.UNDEFINED:
            self.connection.disconnect()
            return None
        else:
            print(f"Unknown code from server: {request.code}")
        
        return None
            
    def server_handle_user_connection_status(self, status : Network.UserConnectionStatus):
        #print(f"Status is {status}")
        if status == Network.UserConnectionStatus.BANNED.value:
            print("You have been banned on this server.")
        if status == Network.UserConnectionStatus.DISCONNECTED.value:
            print("You has been disconnected from the server.")
        elif status == Network.UserConnectionStatus.REGISTER_REQUIRED.value:
            print("To connect to this server you need to register your name on it so that no one else can connect using your name")
                
            while True:
                password = input("Enter password: ")
                if password == "":
                    continue

                response = self.connection.get(Packet(Packet.Code.PASSWORD, {"password": password}))

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

                response = self.connection.get(Packet(Packet.Code.PASSWORD, {"password": password}))

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
        
    def handle_session_connection(self, session_id):
            print(f"Connected to session #{session_id}.\nStarting game.")

def main() -> int:
    bs = BattleShip()
    bs.main_menu()

    return 0

if __name__ == "__main__":
    sys.exit(main())