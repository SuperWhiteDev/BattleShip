#!/usr/bin/env python3
"""
Entry point for BattleShip client application.
This module initializes and starts the game.
"""

from battle_ship import BattleShip

def main() -> int:
    game = BattleShip()

    try:
        game.start()  # Start the game (this will invoke the UI loop)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Critical Error: {e}!")
        return 1
    else:
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

