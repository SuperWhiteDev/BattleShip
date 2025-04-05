import json
from typing import TypedDict

class Config:
    class User(TypedDict):
        name: str

    class Servers(TypedDict):
        name: str
        ip: str
        port: int

    BASE_CONFIG = {"user":{"name": None}, "servers": []}

    def __init__(self) -> None: 
        self.update()

    def _get(self) -> dict:
        try:
            with open("config.json", "r", encoding="UTF-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return self.BASE_CONFIG
    def _write(self) -> None:
        try:
            with open("config.json", "w", encoding="UTF-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(e)
            pass

    def update(self):
        self.config = self._get()
        
        self.user : self.User = {"name": self.config["user"]["name"]}
        self.servers : list[self.Servers] = []
        
        for server in self.config["servers"]:
            self.servers.append({"name": server["server_name"], "ip": server["server_ip"], "port": int(server["server_port"])})
    def save(self) -> bool:
        try:
            self.config["user"] = {
                "name": self.user["name"]
            }
            self.config["servers"] = []
            for server in self.servers:
                self.config["servers"].append({
                    "server_name": server["name"],
                    "server_ip": server["ip"],
                    "server_port": server["port"]
                })
            self._write()
        except Exception:
            return False
        else:
            return True
        
    def add_server(self, name, ip, port) -> bool:
        self.servers.append({"name": name, "ip": ip, "port": port})

        return self.save()

    # def create_config(self):
    #     config = self._get()

    #     config["user"] = {
    #         "name": input("Enter your username: ").strip(),
    #     }
    #     config["servers"] = []

    #     self.save_config(config)
