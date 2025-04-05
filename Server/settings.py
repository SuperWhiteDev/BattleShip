HOST = "0.0.0.0"
PORT = 64221
INIT_ATTEMPTS = 100

DEBUG = False

ADMIN_TERMINAL = True
ADMIN_FILE_TERMINAL = True
ADMIN_SOCKET_TERMINAL = True

LOGGING_ADMIN_FILE_TERMINAL = True
ADMIN_FILE_TERMINAL_FILE = "terminal.txt"

LOGGING_ADMIN_SOCKET_TERMINAL = True
ADMIN_SOCKET_TERMINAL_PORT = 64222
ADMIN_SOCKET_MAX_CONNECTIONS = 5

MAX_USERS = 20
MAX_USER_NAME_LENGTH = 30

MAX_GAME_SESSIONS = 2

DATABASE_ENGINE = "MySQL" # Values: SQLite, MySQL.

# Config for MySQL database engine
DATABASE_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "W8gw#zp<9BbJSd*C",
    "database": "BattleShipDB"
}

# Config for SQLite database engine
# DATABASE_CONFIG = {
#     "database": "db.sqlite3"
# }