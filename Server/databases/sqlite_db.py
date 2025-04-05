import sqlite3 as sql
from .db import DatabaseInterface
from log import Log

class SQLiteDatabase(DatabaseInterface):
    def __init__(self, database_file: str) -> None:
        Log.info("Connecting to a SQLite database...")

        self.connection = sql.connect(database_file, check_same_thread=False)
        self.connection.row_factory = sql.Row
        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            Log.info(f"Successfully connected to SQLite Database. SQLite DB version is {version}")
        except sql.DatabaseError as e:
            Log.exception("Failed to connect to SQLite database.", e)
            raise Exception(f"Failed to connect to SQLite database. Error: {e}")
    
    def __del__(self):
        try:
            if self.connection:
                Log.info("Closing the SQLite database connection...")
                self.connection.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

    def create_table(self, table_name : str, fields : dict) -> None:
        cursor = self.connection.cursor()
        field_definitions = ", ".join([f"{name} {type}" for name, type in fields.items()])

        cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({field_definitions});")
        self.connection.commit()
        cursor.close()

    def delete_table(self, table_name : str):
        cursor = self.connection.cursor()

        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        self.connection.commit()
        cursor.close()

    def insert(self, table_name : str, data):
        cursor = self.connection.cursor()

        columns = ", ".join(data.keys())
        values = ", ".join(["?"] * len(data))
        cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values});", tuple(data.values()))

        self.connection.commit()
        cursor.close()
        
    def select(self, table_name : str, conditions=None):
        cursor = self.connection.cursor()
        query = f"SELECT * FROM {table_name}"
        if conditions:
            condition_str = " AND ".join([f"{col}=?" for col in conditions])
            query += f" WHERE {condition_str}"
            cursor.execute(query, tuple(conditions.values()))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return rows
       
    def delete(self, table_name : str, conditions=None):
        cursor = self.connection.cursor()
        query = f"DELETE FROM {table_name}"
        if conditions:
            condition_str = " AND ".join([f"{col}=?" for col in conditions])
            query += f" WHERE {condition_str}"
            cursor.execute(query, tuple(conditions.values()))
        else:
            cursor.execute(query)

        deleted = cursor.rowcount
        self.connection.commit()
        cursor.close()

        return deleted

    def set(self, table_name : str, field: str, value, conditions: dict) -> int:
        """
        Sets a new value for the specified field in rows matching the conditions.
        :param table_name: The name of the table.
        :param field: The field to be updated.
        :param value: New value for the field.
        :param conditions: Dictionary of conditions for selecting rows (where keys are column names and values are their values).
        """
        cursor = self.connection.cursor()
        condition_str = " AND ".join([f"{col}=?" for col in conditions.keys()])
        query = f"UPDATE {table_name} SET {field}=? WHERE {condition_str};"
        params = (value,) + tuple(conditions.values())
        
        cursor.execute(query, params)
        updated_rows = cursor.rowcount
        
        self.connection.commit()
        cursor.close()
        
        return updated_rows