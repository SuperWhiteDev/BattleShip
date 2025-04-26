"""
Module containing enumerations used in the application.
These enums define protocol codes and game states.
"""

from enum import Enum

class ConnectionStatus(Enum):
    """
    Enumeration representing the current connection state.
    """
    NOT_CONNECTED = 0   # The user is not connected to the server.
    CONNECTED = 1       # The user is successfully connected.
    CONNECTING = 2      # The user is in the process of connecting.

class Errors(Enum):
    """
    Enumeration for various error codes encountered during operation.
    These errors can be used to signal specific issues in authentication, limits, and communication.
    """
    NAME_ALREADY_IN_USE = 0      # The username is already taken.
    NAME_TOO_LONG = 1            # The provided username exceeds the allowed length.
    REACHED_USERS_LIMIT = 2      # The maximum number of users has been reached.
    UNEXPECTED_PACKET = 3        # Receiving a package that wasn't supposed to arrive.
    UNCORRECT_PACKET = 4         # An incorrectly formatted packet was received.
    
class ErrorMessages(Enum):
    """
    Enumeration for descriptive error messages.
    """
    PLAYER_NOT_IN_ANY_SESSION = 0  # The player is not connected to any session.

class UserConnectionStatus(Enum):
    CONNECTED = 1               # The user is connected.
    DISCONNECTED = 2            # The user has been disconnected.
    BANNED = 3                  # The user is banned on the server.
    REACHED_USERS_LIMIT = 4     # The maximum user count on the server has been reached.
    REGISTER_REQUIRED = 5       # Registration is required before connecting.
    AUTHORIZATION_REQUIRED = 6  # Authorization is required (e.g., correct password needed).
    FIND_NEW_SESSION = 8        # Request for joining a new session.
    LEAVE_SESSION = 9           # Request to leave the current session.

class GameDataCode(Enum):
    SESSION_STARTED = 0  # Notification: Session has started
    SESSION_CLOSED = 1   # Notification: Session has been closed
    GET_DATA = 2         # Request to get data
    POST_DATA = 3        # Posting data (e.g. field, coordinate)
    COMPLETE = 4         # Battlefield validation complete
    WAITING = 5          # Waiting (e.g., for other players)

class GameDataType(Enum):
    BATTLE_FIELD_REQUIRED = 0  # Request to send the battle field
    BATTLE_FIELD = 1           # Actual battle field data
    NOT_YOUR_TURN = 2          # Notification: not your turn
    COORDINATE = 3             # Coordinate data (e.g., for shooting)
    SHOOT_STATE = 4            # Outcome of a shot (hit/miss)
    RESULTS = 5                # Game results (winner announcement)