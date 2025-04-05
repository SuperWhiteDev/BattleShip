import sys
from threading import Thread
from pyfiglet import figlet_format
from time import sleep
from config import Config
from utils import clear_console
from network import Network
from user import User

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
            for i, (option, value) in enumerate(self.config.items()):
                print(f"{i+1}. {option.capitalize()} - {value}.")
        
            inp = input("Enter what option you want to change: ").strip().lower()
            if inp == "name":
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
            except Exception:
                continue

    def play_game(self):
        if not self.user.is_valid():
            self.create_user()
        
        server_ip, server_port = self.get_server()

        self.connection = Network(self.user)
        self.connection.connect(server_ip, server_port)
        
        if self.connection.connected():
            Thread(target=self.connection.handle).start()
            self.handle_game()

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

    def handle_game(self):
        while self.connection.last_connection_status == "UNDEFINED" or self.connection.last_connection_status == "DISCONNECTED":
            sleep(1.0)

            if self.connection.last_connection_status != "DISCONNECTED":
                print("Game running... (type 'disconnect' to leave from the server)")

                while connected_to_server:
                    user_input = input("> ").strip().lower()
                    if user_input == "disconnect":
                        connected_to_server = False
                        break
        
                while self.connection.last_connection_status != "DISCONNECTED":
                    sleep(1.0)

def main() -> int:
    bs = BattleShip()
    bs.main_menu()

    return 0

if __name__ == "__main__":
    sys.exit(main())