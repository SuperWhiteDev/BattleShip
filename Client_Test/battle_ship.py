import os
import sys
import socket
import json
from threading import Thread
from pyfiglet import figlet_format
from time import sleep
from tool import get_uuid

connected_to_server = False
last_connection_status = "UNDEFINED"

def get_config() -> dict:
    try:
        with open("config.json", "r", encoding="UTF-8") as f:
            config = json.load(f)
    except Exception as e:
        #print(f"Error: {e}")
        config = {}

    return config

def save_config(config) -> None:
    with open("config.json", "w", encoding="UTF-8") as f:
        json.dump(config, f, indent=4)

def get_servers_list() -> list:
    return get_config()["servers"]

def create_config():
    config = get_config()

    config["user"] = {
        "name": input("Enter your username: ").strip(),
    }
    config["servers"] = []

    save_config(config)

def init_user():
    global user

    try:
        user_config = get_config()["user"]
        user = {
            "name": user_config["name"],
            "uid": get_uuid()
        }
    except KeyError:
        create_config()
        init_user()

def clear_console():
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)

def save_new_server(server : dict) -> None:
    config = get_config()
    servers = get_servers_list()

    servers.append(server)

    config["servers"] = servers
    
    save_config(config)
    
def add_new_server() -> None:
    server_name = input("Enter what you want to name the server: ")
    server_ip = input("Enter server IPv4 address: ").strip()
    server_port = input("Enter server port(enter to use default port 64221): ").strip()

    if not server_port:
        server_port = 64221
    
    new_server = {"server_name": server_name, "server_ip": server_ip, "server_port": server_port}
    save_new_server(new_server)

def get_server() -> tuple[str, int]:
    def display_available_servers():
        servers_list = get_servers_list()
        
        server_id = 1
        for server in servers_list:
            print(f"{server_id}. {server["server_name"]}")
            server_id += 1
        
    print("Servers available:")

    display_available_servers()
    
    print("\n\"add\". Add new server")
    
    while True:
        user_in = input("Enter server id or \"add\" to append new server to list: ").strip().lower()

        if user_in == "add":
            add_new_server()
            clear_console()
            return get_server()
        else:
            servers_list = get_servers_list()

            try:    
                server_id = int(user_in) - 1
            except ValueError:
                continue
        
            server = servers_list[server_id]

            return (server["server_ip"], int(server["server_port"]))

def connect_server(server_ip : str, server_port : int, max_attempts : int) -> socket.socket:
    global user, connected_to_server, last_connection_status

    connected_to_server = False
    last_connection_status = "UNDEFINED"

    attempts = 0
    while attempts != max_attempts:
        if attempts:
            print("Attempting to reconnect...")
        else:
            print(f"Connecting to the server IP: {server_ip}, PORT: {server_port}...")
    
        try:        
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(10.0)
            client_socket.connect((server_ip, server_port))

            client_socket.send(f"{user["name"]},{user['uid']}".encode("UTF-8"))
            response = client_socket.recv(1024).decode("UTF-8")
            
            if response == "OK":
                print("Succesfully connected to the server")
                return client_socket
            elif response == "BANNED":
                print("You has been banned on this server.")
                client_socket.close()
                return None
            elif response == "REACHED_USERS_LIMIT":
                print("The server is full at the moment.")
                client_socket.close()
                return None
            elif response == "REGISTER_REQUIRED":
                print("To connect to this server you need to register your name on it so that no one else can connect using your name")
                
                while True:
                    password = input("Enter password: ")
                    if password == "":
                        continue

                    client_socket.send(f"PASSWORD {password}".encode("UTF-8"))

                    response = client_socket.recv(1024).decode("UTF-8")
            
                    if response == "OK":
                        print("Succesfully connected to the server")
                        return client_socket
                    elif response == "UNCORRECT":
                        print("Not correct credintials. Try again.")
            elif response == "PASSWORD_REQUIRED":
                while True:
                    password = input("Enter the password for this account: ")
                    if password == "":
                        continue

                    client_socket.send(f"PASSWORD {password}".encode("UTF-8"))

                    response = client_socket.recv(1024).decode("UTF-8")
            
                    if response == "OK":
                        print("Succesfully connected to the server")
                        return client_socket
                    elif response == "UNCORRECT":
                        print("Not correct. Try again.")
            else:
                sleep(1.0)
            
        except Exception as e:
            print(e)
            print(f"Failed connect to the server IP: {server_ip}, PORT: {server_port}.")
            #print(f"Error: {e}")
            sleep(1.0)

        attempts += 1

    return None

def get_server_response(client_socket: socket.socket) -> str:
    try:
        client_socket.send("PING".encode("UTF-8"))

        response = client_socket.recv(1024).decode("UTF-8")

        return response
    except socket.timeout:
        return "timeout"
    except Exception as e:
        print(f"Error checking server status: {e}")
        return "error"
    
def handle_server_connection(server_ip: str, server_port: int):
    def set_disconnect_status():
        global connected_to_server, last_connection_status
        connected_to_server = False
        last_connection_status = "DISCONNECTED"
    def set_connected_status():
        global connected_to_server, last_connection_status
        connected_to_server = True
        last_connection_status = "CONNECTED"
    def handle_session_connection(session_id):
        print(f"Connected to session #{session_id}.\nStarting game.")
    

    """
    Поток для работы с сервером.
    """
    global connected_to_server

    client_socket = connect_server(server_ip, server_port, 5)
    if not client_socket:
        print("Failed to connect to the server!")
        set_disconnect_status()
        return
    else:
        set_connected_status()

    try:
        while connected_to_server:
            response = get_server_response(client_socket)

            if response == "OK":
                sleep(5)  # Проверяем сервер каждые 5 секунд
            elif response == "BANNED":
                print("You have been banned on this server.")
                break
            elif response in ["timeout", "error"]:
                print("It seems the server doesn't work now.")
                break
            elif response.startswith("Session started"):
                handle_session_connection(int(response.split("ID=")[1]))
            elif response == "Session closed":
                print("Game stopped.")
    finally:
        try:
            client_socket.send("DISCONNECT".encode("UTF-8"))
        except:
            pass
        client_socket.close()
        print("Disconnected from the server.")

        set_disconnect_status()

def settings_menu():
    def option_me():
        global user

        config = get_config()

        settings = {"Name": config["user"]["name"]}

        for i, (option, value) in enumerate(settings.items()):
            print(f"{i+1}. {option} - {value}.")
        
        inp = input("Enter what option you want to change: ").strip().lower()
        if inp == "name":
            new_name = input("Enter your new name: ").strip()

            config["user"] = {
                "name": new_name
            }

            try:
                user["name"] = new_name
            except NameError:
                pass

            save_config(config)

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

def start_menu():
    print(figlet_format("BattleShip Game"))

    try:
        while True:
            inp = input("Enter \"Play\" to play the game: ").strip().lower()

            if inp == "play":
                return "play"
            elif inp == "settings":
                settings_menu()
    except KeyboardInterrupt:
        return "exit"

def play_game():
    global connected_to_server, last_connection_status

    init_user()

    server_ip, server_port = get_server()

    Thread(target=handle_server_connection, args=(server_ip, server_port), daemon=True).start()
            
    while last_connection_status == "UNDEFINED" or last_connection_status == "DISCONNECTED":
        sleep(1.0)

    if last_connection_status != "DISCONNECTED":
        print("Game running... (type 'disconnect' to leave from the server)")

        while connected_to_server:
            user_input = input("> ").strip().lower()
            if user_input == "disconnect":
                connected_to_server = False
                break
        
        while last_connection_status != "DISCONNECTED":
            sleep(1.0)
            

def main() -> int:
    clear_console()

    try:
        while True:
            action = start_menu()
            if action == "play":
                play_game()
            else:
                break

            sleep(2.0)
            clear_console()
    except KeyboardInterrupt:
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())