from datetime import datetime
from .model import DataModel
from settings import MAX_USER_NAME_LENGTH


class Users(DataModel):
    def __init__(self, data: "Data") -> None:
        self.data = data
        self._create_table()

    def _create_table(self) -> None:
        self.data.database.create_table(
            "users",
            {
                "user_name": f"VARCHAR({MAX_USER_NAME_LENGTH}) PRIMARY KEY",
                "last_login_id": "VARCHAR(36) NOT NULL",
                "password": "VARCHAR(40)",
                "register_date": "DATETIME NOT NULL",
                "stat_wins": "INT NOT NULL DEFAULT 0",
                "stat_defeats": "INT NOT NULL DEFAULT 0",
                "stat_matches": "INT NOT NULL DEFAULT 0",
                "stat_longest_match": "INT NOT NULL DEFAULT 0",
                "stat_hits": "INT NOT NULL DEFAULT 0",
                "stat_misses": "INT NOT NULL DEFAULT 0",
            },
        )

    def delete(self) -> None:
        self.data.database.delete_table("users")

    def get(self) -> dict:
        return self.data.database.select("users")

    def add(self, user_name: str, user_id: str, password: str) -> None:
        self.data.database.insert(
            "users",
            {
                "user_name": user_name.lower(),
                "last_login_id": user_id,
                "password": password,
                "register_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

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
        return (
            self.data.database.set(
                "users", "last_login_id", user_id, {"user_name": user_name}
            )
            > 0
        )

    def get_stat_wins(self, user_name: str) -> int:
        user = self.find(user_name)

        return user["stat_wins"] if user and "stat_wins" in user else 0

    def set_stat_wins(self, user_name: str, value: int) -> bool:
        return (
            self.data.database.set(
                "users", "stat_wins", value, {"user_name": user_name.lower()}
            )
            > 0
        )

    def get_stat_defeats(self, user_name: str) -> int:
        user = self.find(user_name)
        return user["stat_defeats"] if user and "stat_defeats" in user else 0

    def set_stat_defeats(self, user_name: str, value: int) -> bool:
        return (
            self.data.database.set(
                "users", "stat_defeats", value, {"user_name": user_name.lower()}
            )
            > 0
        )

    def get_stat_matches(self, user_name: str) -> int:
        user = self.find(user_name)
        return user["stat_matches"] if user and "stat_matches" in user else 0

    def set_stat_matches(self, user_name: str, value: int) -> bool:
        return (
            self.data.database.set(
                "users", "stat_matches", value, {"user_name": user_name.lower()}
            )
            > 0
        )

    def get_stat_longest_match(self, user_name: str) -> int:
        user = self.find(user_name)
        return (
            user["stat_longest_match"] if user and "stat_longest_match" in user else 0
        )

    def set_stat_longest_match(self, user_name: str, value: int) -> bool:
        return (
            self.data.database.set(
                "users", "stat_longest_match", value, {"user_name": user_name.lower()}
            )
            > 0
        )

    def get_stat_hits(self, user_name: str) -> int:
        user = self.find(user_name)
        return user["stat_hits"] if user and "stat_hits" in user else 0

    def set_stat_hits(self, user_name: str, value: int) -> bool:
        return (
            self.data.database.set(
                "users", "stat_hits", value, {"user_name": user_name.lower()}
            )
            > 0
        )

    def get_stat_misses(self, user_name: str) -> int:
        user = self.find(user_name)
        return user["stat_misses"] if user and "stat_misses" in user else 0

    def set_stat_misses(self, user_name: str, value: int) -> bool:
        return (
            self.data.database.set(
                "users", "stat_misses", value, {"user_name": user_name.lower()}
            )
            > 0
        )
