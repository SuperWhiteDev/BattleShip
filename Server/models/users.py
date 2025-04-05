from datetime import datetime
from .model import DataModel
from settings import MAX_USER_NAME_LENGTH

class Users(DataModel):
    def __init__(self, data: 'Data') -> None:
        self.data = data
        self._create_table()

    def _create_table(self) -> None:
        self.data.database.create_table("users", {"user_name": f"VARCHAR({MAX_USER_NAME_LENGTH}) PRIMARY KEY", "last_login_id": "VARCHAR(36) NOT NULL", "password": "VARCHAR(40)", "register_date": "DATETIME NOT NULL"})

    def delete(self) -> None:
        self.data.database.delete_table("users")

    def get(self) -> dict:
        return self.data.database.select("users")

    def add(self, user_name: str, user_id: str, password: str) -> None:
        self.data.database.insert("users", {"user_name": user_name.lower(), "last_login_id": user_id, "password": password, "register_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    def remove(self, user_name: str) -> bool:
        deleted = self.data.database.delete("users", {"user_name": user_name.lower()})
        return deleted > 0

    def find(self, user_name: str) -> dict:
        users = self.get()
        for user in users:
            if user["user_name"] == user_name.lower():
                return user
        return None

    def update_login(self, user_name: str, user_id: str) -> bool:
        return self.data.database.set("users", "last_login_id", user_id, {"user_name": user_name}) > 0
