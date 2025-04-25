from abc import ABC, abstractmethod


class DatabaseInterface(ABC):
    @abstractmethod
    def create_table(self, table_name, fields):
        pass

    @abstractmethod
    def delete_table(self, table_name):
        pass

    @abstractmethod
    def insert(self, table_name, data):
        pass

    @abstractmethod
    def select(self, table_name, conditions=None):
        pass

    @abstractmethod
    def delete(self, table_name, conditions=None):
        pass

    @abstractmethod
    def set(self, table_name: str, field: str, value, conditions: dict) -> int:
        pass
