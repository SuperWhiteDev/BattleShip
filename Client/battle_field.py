from enum import Enum

class BattleField:
    """
    BattleField class encapsulates the game field management for the Battleship game.
    """

    # Inner enumeration for shoot states.
    class ShootState(Enum):
        UNKNOWN = 0      # Unknown shooting state
        HIT = 1          # Ship hit
        MISS = 2         # Shot missed
        ALREADY_SHOT = 3 # This cell was already shot

    BATTLE_FIELD_WIDTH = 10    # Battlefield width (10 cells)
    BATTLE_FIELD_HEIGHT = 10   # Battlefield height (10 cells)

    def __init__(self, field=None):
        """
        Initializes the BattleField instance.
        
        If a field is provided, it will be used; otherwise, an empty field is created.
        
        :param field: Optional 2D list representing the initial state of the field.
        """
        if field:
            self.field = field
        else:
            self.field = self.create_empty_field()

    def create_empty_field(self):
        """
        Creates an empty game field filled with '.' characters.
        
        :return: 2D list of size BATTLE_FIELD_HEIGHT x BATTLE_FIELD_WIDTH filled with '.'.
        """
        return [['.' for _ in range(self.BATTLE_FIELD_WIDTH)] for _ in range(self.BATTLE_FIELD_HEIGHT)]

    def can_place_ship(self, ship_length, row, col, orientation):
        """
        Checks if a ship of the given length can be placed at the specified location
        on the field in the desired orientation ('H' for horizontal, 'V' for vertical),
        without exiting boundaries or overlapping existing ships.
        
        Additionally, all adjacent cells (in 8 directions) around the proposed ship cells must be empty,
        unless they are part of the ship itself.
        
        :param ship_length: Length of the ship to be placed.
        :param row: Starting row index.
        :param col: Starting column index.
        :param orientation: 'H' for horizontal or 'V' for vertical placement.
        :return: True if placement is valid, False otherwise.
        """
        if orientation.upper() not in ("H", "V"):
            return False

        proposed_cells = []
        if orientation.upper() == 'H':
            if col + ship_length > self.BATTLE_FIELD_WIDTH:
                return False
            for j in range(col, col + ship_length):
                proposed_cells.append((row, j))
        else:
            if row + ship_length > self.BATTLE_FIELD_HEIGHT:
                return False
            for i in range(row, row + ship_length):
                proposed_cells.append((i, col))

        # Check that all proposed cells are empty.
        for (i, j) in proposed_cells:
            if self.field[i][j] != '.':
                return False

        # Check adjacent cells (in 8 directions) for each proposed cell.
        for (i, j) in proposed_cells:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    ni, nj = i + dx, j + dy
                    if not (0 <= ni < self.BATTLE_FIELD_HEIGHT and 0 <= nj < self.BATTLE_FIELD_WIDTH):
                        continue
                    if (ni, nj) in proposed_cells:
                        continue
                    if self.field[ni][nj] == 'S':
                        return False
        return True

    def place_ship(self, ship_length, row, col, orientation):
        """
        Places a ship on the field by marking the corresponding cells with 'S'.
        
        :param ship_length: Length of the ship.
        :param row: Starting row index.
        :param col: Starting column index.
        :param orientation: 'H' (horizontal) or 'V' (vertical) placement.
        :return: The updated field after placing the ship.
        """
        if orientation.upper() == "H":
            for j in range(col, col + ship_length):
                self.field[row][j] = "S"
        else:
            for i in range(row, row + ship_length):
                self.field[i][col] = "S"

    def _check_coordinates(self, row, col) -> None:
        """
        Validates the specified coordinates against field boundaries.
        
        :param row: Row index.
        :param col: Column index.
        :raises ValueError: If the coordinates are outside the valid range.
        """
        if not (0 <= row < self.BATTLE_FIELD_HEIGHT and 0 <= col < self.BATTLE_FIELD_WIDTH):
            raise ValueError("Invalid coordinates")

    def shoot(self, row, col) -> 'BattleField.ShootState':
        """
        Processes a shot at the specified coordinates.
        
        This method updates the field:
          - If a ship ('S') is hit, it changes the cell to 'H'.
          - If the cell is empty ('.'), it marks it as a miss ('M').
          - If the cell was already shot (either 'H' or 'M'), the appropriate error state is returned.
        
        :param row: The row index for the shot.
        :param col: The column index for the shot.
        :return: A ShootState indicating the outcome (HIT, MISS, ALREADY_SHOT, or UNKNOWN).
        """
        self._check_coordinates(row, col)
        cell = self.field[row][col]
        if cell == "S":
            self.field[row][col] = "H"
            return self.ShootState.HIT
        elif cell == ".":
            self.field[row][col] = "M"
            return self.ShootState.MISS
        elif cell in ("H", "M"):
            return self.ShootState.ALREADY_SHOT
        return self.ShootState.UNKNOWN

    def is_all_ships_destroyed(self) -> bool:
        """
        Checks if all ships on the field have been destroyed.
        
        :return: True if there are no cells marked as 'S', otherwise False.
        """
        for row in self.field:
            if "S" in row:
                return False
        return True
