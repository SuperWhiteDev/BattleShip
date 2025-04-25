from settings import DATABASE_ENGINE, DATABASE_CONFIG
from databases import MySQLDatabase, SQLiteDatabase


class DataBaseInitError(Exception):
    pass


class DataBase:
    engine = None
    database = None

    @staticmethod
    def init():
        if DataBase.database:
            DataBase.deinit()

        DataBase.engine = DATABASE_ENGINE

        if DataBase.engine == "MySQL":
            try:
                DataBase.database = MySQLDatabase(
                    DATABASE_CONFIG["host"],
                    DATABASE_CONFIG["user"],
                    DATABASE_CONFIG["password"],
                    DATABASE_CONFIG["database"],
                )
            except Exception as e:
                raise DataBaseInitError(
                    f"An error occurred while connecting to the database. Try using a different DBMS\nDB Error: {e}"
                )
            return DataBase.database
        elif DataBase.engine == "SQLite":
            try:
                DataBase.database = SQLiteDatabase(DATABASE_CONFIG["database"])
            except Exception as e:
                raise DataBaseInitError(
                    f"An error occurred while connecting to the database. Try using a different DBMS\nDB Error: {e}"
                )
            return DataBase.database

    @staticmethod
    def deinit():
        pass
