import socket
from time import sleep
from user import User

class Network:
    def __init__(self, user : User) -> None:
        self.user = user
        self.connected_to_server = False
        self.last_connection_status = "UNDEFINED"


    def connect(self, ip: str, port: int, max_attempts: int = 5) -> bool:
        self.connected_to_server = False
        self.last_connection_status = "UNDEFINED"

        attempts = 0
        while attempts != max_attempts:
            if attempts:
                print("Attempting to reconnect...")
            else:
                print(f"Connecting to the server IP: {ip}, PORT: {port}...")
    
            try:        
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10.0)
                self.socket.connect((ip, port))

                self.socket.send(f"{self.user.name},{self.user.uid}".encode("UTF-8"))
                response = self.socket.recv(1024).decode("UTF-8")
            
                if response == "OK":
                    print("Succesfully connected to the server")
                    self.connected_to_server = True
                    self.last_connection_status = "CONNECTED"
                    return True

                elif response == "BANNED":
                    print("You has been banned on this server.")
                    self.socket.close()
                    break
                elif response == "REACHED_USERS_LIMIT":
                    print("The server is full at the moment.")
                    self.socket.close()
                    break
                elif response == "REGISTER_REQUIRED":
                    print("To connect to this server you need to register your name on it so that no one else can connect using your name")
                
                    while True:
                        password = input("Enter password: ")
                        if password == "":
                            continue

                        self.socket.send(f"PASSWORD {password}".encode("UTF-8"))

                        response = self.socket.recv(1024).decode("UTF-8")
            
                        if response == "OK":
                            print("Succesfully connected to the server")
                            self.connected_to_server = True
                            self.last_connection_status = "CONNECTED"
                            return True

                        elif response == "UNCORRECT":
                            print("Not correct credintials. Try again.")
                elif response == "PASSWORD_REQUIRED":
                    while True:
                        password = input("Enter the password for this account: ")
                        if password == "":
                            continue

                        self.socket.send(f"PASSWORD {password}".encode("UTF-8"))

                        response = self.socket.recv(1024).decode("UTF-8")
            
                        if response == "OK":
                            print("Succesfully connected to the server")
                            self.connected_to_server = True
                            self.last_connection_status = "CONNECTED"
                            return True

                        elif response == "UNCORRECT":
                            print("Not correct. Try again.")
                else:
                    sleep(1.0)
            
            except Exception as e:
                print(e)
                print(f"Failed connect to the server IP: {ip}, PORT: {port}.")
                sleep(1.0)

            attempts += 1

        print("Failed to connect to the server!")
        self.disconnect()
        return False
            
            
    def disconnect(self):
        self.connected_to_server = False
        self.last_connection_status = "DISCONNECTED"

    def connected(self) -> bool:
        return self.connected_to_server and self.last_connection_status == "CONNECTED"
    
    
    def get_server_response(self) -> str:
        try:
            self.socket.send("PING".encode("UTF-8"))

            response = self.socket.recv(1024).decode("UTF-8")

            return response
        except socket.timeout:
            return "timeout"
        except Exception as e:
            print(f"Error checking server status: {e}")
            return "error"

    def handle(self):
        try:
            while self.connected_to_server:
                response = self.get_server_response()

                if response == "OK":
                    sleep(5)  # Проверяем сервер каждые 5 секунд
                elif response == "BANNED":
                    print("You have been banned on this server.")
                    break
                elif response in ["timeout", "error"]:
                    print("It seems the server doesn't work now.")
                    break
                elif response.startswith("Session started"):
                    self.handle_session_connection(int(response.split("ID=")[1]))
                elif response == "Session closed":
                    print("Game stopped.")
        finally:
            try:
                self.socket.send("DISCONNECT".encode("UTF-8"))
            except:
                pass

            self.socket.close()
            print("Disconnected from the server.")

            self.disconnect()

    def handle_session_connection(self, session_id):
            print(f"Connected to session #{session_id}.\nStarting game.")
    
    