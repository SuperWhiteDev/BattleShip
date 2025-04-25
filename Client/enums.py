"""
Module containing enumerations used in the application.
These enums define protocol codes and game states.
"""

from enum import Enum

class GameDataCode(Enum):
    SESSION_STARTED = 0  # Session has started
    SESSION_CLOSED = 1   # Session has been closed
    GET_DATA = 2         # Request to get data
    POST_DATA = 3        # Posting data (e.g. field, coordinate)
    COMPLETE = 4         # Action complete
    WAITING = 5          # Waiting (e.g., for other players)

class GameDataType(Enum):
    BATTLE_FIELD_REQUIRED = 0  # Request to send the battle field
    BATTLE_FIELD = 1           # Actual battle field data
    NOT_YOUR_TURN = 2          # Notification: not your turn
    COORDINATE = 3             # Coordinate data (e.g., for shooting)
    SHOOT_STATE = 4            # Outcome of a shot (hit/miss)
    RESULTS = 5                # Game results (winner announcement)