"""
User Interface module.
Contains functions for displaying menus, boards and handling basic user interactions.
"""

from pyfiglet import figlet_format
from time import sleep
from battle_field import BattleField
from utils import clear_console


class UI:
    def __init__(self, game : "BattleShip") -> None:
        self.game = game
        
    def display_title(self):
        """
        Renders and prints the game title using ASCII art.
        """
        print(figlet_format("BattleShip Game"))

    def main_menu(self):
        """
        Displays the main menu loop.
        Continually prompts the user for actions until they choose to exit.
        """
        clear_console()
        while True:
            action = self.start_menu()
            if action == "exit":
                break
            if action == "play":
                self.game.play_game()
                return
            sleep(2.0)
            clear_console()

    def start_menu(self):
        """
        Displays the start menu.
        
        Prompts the user to enter a command (e.g., "play" to start the game or "settings" for options).
        Returns the chosen action.
        """
        self.display_title()
        try:
            while True:
                inp = input('Enter "Play" to play the game or "Settings" for options: ').strip().lower()
                if inp == "play":
                    return "play"
                elif inp == "settings":
                    # settings_menu() возвращает, например, новое имя пользователя.
                    new_name = self.settings_menu()
                    if new_name is not None:
                        print(f"New name set to: {new_name}")
        except KeyboardInterrupt:
            return "exit"

    def settings_menu(self):
            def option_me():
                options = {"Name": self.game.user.name}

                for i, (option, value) in enumerate(options.items()):
                    print(f"{i + 1}. {option.capitalize()} - {value}.")

                inp = input("Enter what option you want to change: ").strip().lower()

                try:
                    index = int(inp)
                except ValueError:
                    index = -1

                if inp == "name" or index == 1:
                    self.game.user.set_name(input("Enter your new name: ").strip())

            options = ["Me"]

            for i, option in enumerate(options):
                print(f"{i + 1}. {option}.")

            while True:
                try:
                    option = (
                        input('Enter option or "back" to return to start menu: ')
                        .strip()
                        .lower()
                    )

                    if option == "back":
                        break

                    if option == options[0].lower() or int(option) == 1:
                        option_me()
                except Exception as e:
                    print(e)
                    continue

    def create_user(self):
        self.game.user.set_name(input("Enter your username: "))

    def get_server(self) -> tuple[str, int]:
        def display_available_servers():
            print("Servers available:")

            for i, server in enumerate(self.game.config.servers):
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
                    server = self.game.config.servers[server_id]
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

        self.game.config.add_server(name, ip, port)

    def display_field(self, field : BattleField):
        """
        Displays a field (2D list) on the console.
        
        :param field: 2D list representing the game field.
        """
        header = "   " + " ".join(chr(65 + i) for i in range(len(field.field[0])))
        print(header)
        print("   " + "---" * len(field.field[0]))
        for idx, row in enumerate(field.field):
            print(f"{idx:2} " + " ".join(row))
        print()

    def get_shoot_coordinates(self, field : BattleField):
        """
        Prompts the user to input coordinates for shooting.
        The column can be entered as a number or a letter.
        
        :param field: The field to display for reference.
        :return: A tuple with (row, col) coordinates.
        """
        self.display_field(field)
        while True:
            user_in = input("Enter row and column to shoot (e.g., '3 A'): ").strip().split()
            if len(user_in) != 2:
                print("Error: Please enter exactly 2 values (row and column). Try again.")
                continue
            try:
                row = int(user_in[0])
            except ValueError:
                print("Error: The row must be an integer between 0 and 9. Try again.")
                continue
            col_part = user_in[1]
            if col_part.isalpha():
                col = ord(col_part.upper()) - ord("A")
            else:
                try:
                    col = int(col_part)
                except ValueError:
                    print("Error: The column must be a number or a letter between A and J. Try again.")
                    continue

            try:
                field._check_coordinates(row, col)
            except ValueError:
                print("Error: The coordinates must be an numbers beetwen 0 and 9. Please try again.\n")
                continue

            return row, col
        
    def get_battle_field(self) -> BattleField:
            print("Press any key to start placing ships")

            ship_lengths = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

            battle_field = BattleField()

            self.display_field(battle_field)

            for ship_length in ship_lengths:
                while True:
                    print(f"Place a ship length {ship_length}.")

                    user_in = input("Enter row, column and orientation (e.g., '3 A H'): ").strip().split()
                    if len(user_in) != 3:
                        print("Error: Please enter exactly 3 values (row, column, orientation). Try again.\n")
                        continue
                    
                    try:
                        row = int(user_in[0])
                    except ValueError:
                        print("Error: The first coordinate (row) must be an integer. Please try again.\n")
                        continue

                    col_part = user_in[1]
                    if col_part.isalpha():
                        col = ord(col_part.upper()) - ord('A')
                    else:
                        try:
                            col = int(col_part)
                        except ValueError:
                            print("Error: The second coordinate (column) must be a number or a letter. Try again.\n")
                            continue

                    orientation = user_in[2].upper()
                    if row not in range(10) or col not in range(10):
                        print("Error: Row must be between 0 and 9 and column between A and J (or 0 and 9). Try again.\n")
                        continue
                    if orientation not in ('H', 'V'):
                        print("Error: Orientation must be 'H' (horizontal) or 'V' (vertical). Try again.\n")
                        continue

                    if not battle_field.can_place_ship(ship_length, row, col, orientation):
                        print("Cannot place ship here. It might exceed the boundaries or overlap with another ship. Try again.\n")
                        continue

                    battle_field.place_ship(ship_length, row, col, orientation)
                    
                    clear_console()
                    print("Ship placed successfully!")
                    self.display_field(battle_field)
                    break

            return battle_field
