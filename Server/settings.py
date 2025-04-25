# Server Configuration File for the Battleship Project
# This file defines various parameters used throughout the server implementation,
# including network settings, admin interfaces, limits, and database configurations.

# Host configuration:
# "0.0.0.0" means the server will listen on all available network interfaces.
HOST = "0.0.0.0"

# Port on which the server will accept incoming connections (by default 64221).
PORT = 64221

# Number of initialization attempts (e.g., binding the socket).
# The server will try up to this many times before giving up.
INIT_ATTEMPTS = 100

# Debug mode flag.
# When set to True, the server will generate verbose logging for diagnostics.
DEBUG = False

# Enable various administrator interfaces:
ADMIN_TERMINAL = True       # Enable command-line (terminal) admin interface.
ADMIN_FILE_TERMINAL = True  # Enable file-based admin interface (commands read/written to a file).
ADMIN_SOCKET_TERMINAL = True  # Enable socket-based admin interface for remote management.

# Settings for the file-based admin terminal:
LOGGING_ADMIN_FILE_TERMINAL = True  # Enable logging of commands executed via the file terminal.
ADMIN_FILE_TERMINAL_FILE = "terminal.txt"  # Filename used for read/write operations in the file terminal.

# Settings for the socket-based admin terminal:
LOGGING_ADMIN_SOCKET_TERMINAL = True  # Enable logging of commands received via the socket terminal.
ADMIN_SOCKET_TERMINAL_PORT = 64222     # Port on which the admin socket interface will listen.
ADMIN_SOCKET_MAX_CONNECTIONS = 5       # Maximum number of concurrent connections for the socket interface.

# Session log settings:
# Determines whether session logs are printed to the console.
CONSOLE_LOGGING_SESSION_LOGS = False

# User and session limits:
MAX_USERS = 20               # Maximum number of simultaneous users allowed.
MAX_USER_NAME_LENGTH = 30    # Maximum allowable length for a username.

MAX_GAME_SESSIONS = 2        # Maximum number of concurrent game sessions allowed.

# Database configuration:
# DATABASE_ENGINE specifies the database backend that the server will use.
# Supported values are "SQLite" or "MySQL". Currently set to "MySQL".
DATABASE_ENGINE = "MySQL"  # Choose between "SQLite" and "MySQL"

# Configuration for MySQL database engine (uncomment to use):
# DATABASE_CONFIG = {
#     "host": "localhost",            # MySQL server host
#     "user": "Your username",                 # MySQL username
#     "password": "Your password",  # Password for accessing MySQL
#     "database": "BattleShipDB"       # Name of the MySQL database to use
# }

# Configuration for SQLite database engine:
DATABASE_CONFIG = {
    "database": "db.sqlite3"
}