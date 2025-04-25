#!/usr/bin/env python3
"""
Entry point for BattleShip client application.
This module initializes and starts the game.
"""

from battle_ship import BattleShip

def main() -> int:
    game = BattleShip()
    game.start()  # Start the game (this will invoke the UI loop)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

