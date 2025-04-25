from threading import Thread
from time import sleep, time
from typing import Optional
from enum import Enum
from queue import Queue
from packet import Packet
from network import Network
from log import Log

MIN_PLAYERS_IN_SESSION = 2  # Minimum number of players required to start a session

class BattleField:
    class ShootState(Enum):
        UNKNOWN = 0     # The state of the shot could not be determined
        HIT = 1         # The shot hit a ship cell
        MISS = 2        # The shot missed any ship
        ALREADY_SHOT = 3  # The cell has already been shot at

    BATTLE_FIELD_WIDTH = 10   # Battlefield width is fixed at 10 cells
    BATTLE_FIELD_HEIGH = 10   # Battlefield height is fixed at 10 cells

    def __init__(self, battle_field: list[list] = None) -> None:
        """
        Initializes the battlefield with either an existing configuration or a clean 10x10 grid.
        If a battlefield configuration is provided, its validity is checked:
          - The battlefield must be a list of 10 lists.
          - Each inner list must also have 10 elements.
          - Ships (cells marked with "S") are grouped using DFS to check ship contiguity.
          - Each ship must be placed either horizontally or vertically.
          - The cells of each ship must be continuous (no gaps).
          - The configuration must match the expected ship sizes (one 4-cell, two 3-cells,
            three 2-cells, and four 1-cell ships).
          - Ships cannot be adjacent to each other in any of the 8 surrounding directions.
        If any of these checks fail, a ValueError is raised.
        """
        if battle_field:
            if isinstance(battle_field, list):
                if all([
                    isinstance(field, list) and len(field) == 10
                    for field in battle_field
                ]):
                    n, m = 10, 10
                    # Initialize helper matrices for DFS: 'visited' tracks cells that have been checked,
                    # 'component_id' stores which ship component each cell belongs to.
                    visited = [[False] * m for _ in range(n)]
                    component_id = [[None] * m for _ in range(n)]
                    ship_lengths = []
                    comp_id = 0
                    components = {}  # comp_id: list of (i, j) cells in that ship

                    # DFS to traverse the ships (connected components)
                    for i in range(n):
                        for j in range(m):
                            if battle_field[i][j] == "S" and not visited[i][j]:
                                stack = [(i, j)]
                                components[comp_id] = []
                                while stack:
                                    x, y = stack.pop()
                                    if visited[x][y]:
                                        continue
                                    visited[x][y] = True
                                    component_id[x][y] = comp_id
                                    components[comp_id].append((x, y))
                                    # Traverse neighbors in 4 directions (without diagonals)
                                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                                        nx, ny = x + dx, y + dy
                                        if (
                                            0 <= nx < n
                                            and 0 <= ny < m
                                            and battle_field[nx][ny] == "S"
                                            and not visited[nx][ny]
                                        ):
                                            stack.append((nx, ny))
                                ship_cells = components[comp_id]
                                xs = [x for x, _ in ship_cells]
                                ys = [y for _, y in ship_cells]
                                # Check that the ship is placed either horizontally or vertically
                                if not (all(x == xs[0] for x in xs) or all(y == ys[0] for y in ys)):
                                    raise ValueError(
                                        f"Ship component {comp_id} is not placed horizontally or vertically."
                                    )
                                # Check for continuity: the distance between the extreme cells + 1 must equal the number of cells
                                if all(x == xs[0] for x in xs):  # horizontal ship
                                    if (max(ys) - min(ys) + 1) != len(ship_cells):
                                        raise ValueError(
                                            f"Ship component {comp_id}'s cells are not contiguous horizontally."
                                        )
                                else:  # vertical ship
                                    if (max(xs) - min(xs) + 1) != len(ship_cells):
                                        raise ValueError(
                                            f"Ship component {comp_id}'s cells are not contiguous vertically."
                                        )
                                ship_lengths.append(len(ship_cells))
                                comp_id += 1

                    # Check for expected configuration based on ship sizes.
                    # Classic configuration: one 4-cell, two 3-cells, three 2-cells, and four 1-cell ships.
                    expected_ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
                    if sorted(ship_lengths) != sorted(expected_ships):
                        raise ValueError(
                            f"Ship sizes {sorted(ship_lengths)} do not match expected configuration {sorted(expected_ships)}."
                        )

                    # Additional check: ships must not touch each other,
                    # meaning that no ship cell should have a neighbor (in any of 8 directions) that belongs to a different ship.
                    for i in range(n):
                        for j in range(m):
                            if battle_field[i][j] == "S":
                                for dx in [-1, 0, 1]:
                                    for dy in [-1, 0, 1]:
                                        if dx == 0 and dy == 0:
                                            continue
                                        ni, nj = i + dx, j + dy
                                        if (
                                            0 <= ni < n
                                            and 0 <= nj < m
                                            and battle_field[ni][nj] == "S"
                                        ):
                                            # If the neighboring cell belongs to a different ship:
                                            if component_id[ni][nj] != component_id[i][j]:
                                                raise ValueError(
                                                    "Ships cannot be adjacent to each other, even diagonally."
                                                )

                    self.battle_field = battle_field
                else:
                    raise ValueError("Uncorrect battle field")
            else:
                raise ValueError("Uncorrect battle field")
        else:
            # If no battlefield configuration is provided, initialize an empty 10x10 grid filled with '.' (empty cell)
            self.battle_field = [["." for _ in range(10)] for _ in range(10)]

    def _check_coordinates(self, row, col) -> None:
        """
        Validate that the provided coordinates (row, col) are within the bounds of the battlefield.
        Raises a ValueError if the coordinates are invalid.
        """
        rows = len(self.battle_field)
        cols = len(self.battle_field[0])

        if not (0 <= row < rows and 0 <= col < cols):
            raise ValueError("Invalid coordinates")

    def shoot(self, row, col) -> 'BattleField.ShootState':
        """
        Processes a shot at the coordinates (row, col):
          - Check the coordinates for validity.
          - Retrieve the content of the targeted cell.
          - If a ship is present ("S"), mark the cell as hit ("H") and return HIT.
          - If the cell is empty (".") mark it as a miss ("M") and return MISS.
          - If the cell was already hit or marked as a miss (i.e. "H" or "M"), return ALREADY_SHOT.
          - Otherwise, return UNKNOWN.
        """
        self._check_coordinates(row, col)

        cell = self.battle_field[row][col]
        if cell == "S":
            self.battle_field[row][col] = "H"
            return self.ShootState.HIT
        elif cell == ".":
            self.battle_field[row][col] = "M"
            return self.ShootState.MISS
        elif cell in ("H", "M"):
            return self.ShootState.ALREADY_SHOT

        return self.ShootState.UNKNOWN

    def is_all_ships_destroyed(self):
        """
        Check the entire battlefield to determine if all ship cells ("S") have been turned into hits ("H").
        Returns True if no ship cells remain, indicating that all ships have been destroyed.
        """
        for row in self.battle_field:
            if "S" in row:
                return False
        return True

    def set(self, row, col, shoot_state: 'BattleField.ShootState') -> None:
        """
        Manually sets the state of a specific cell in the battlefield:
          - Validates the coordinates.
          - Sets the cell to "H" (hit) or "M" (miss) based on the provided shoot_state.
        """
        self._check_coordinates(row, col)

        if shoot_state == self.ShootState.HIT:
            self.battle_field[row][col] = "H"
        elif shoot_state == self.ShootState.MISS:
            self.battle_field[row][col] = "M"


class Session:
    class GameDataCode(Enum):
        SESSION_STARTED = 0
        SESSION_CLOSED = 1
        GET_DATA = 2
        POST_DATA = 3
        COMPLETE = 4
        WAITING = 5

    class GameDataType(Enum):
        BATTLE_FIELD_REQUIRED = 0
        BATTLE_FIELD = 1
        NOT_YOUR_TURN = 2
        COORDINATE = 3
        SHOOT_STATE = 4
        RESULTS = 5

    sessions: list["Session"] = []
    next_session_id = 0

    @staticmethod
    def get_next_session_id():
        id = Session.next_session_id
        Session.next_session_id += 1
        return id

    @staticmethod
    def connect(user: "User") -> Optional["Session"]:
        players = set((user,))

        for u in user.get_users(user.server):
            if not u.session and u.is_looking_for_session:
                players.add(u)
            if len(players) >= MIN_PLAYERS_IN_SESSION:
                session = Session(user.server, players)

                for player in players:
                    if player == user:
                        continue
                    player.connect_session(session)

                session.start()
                return session

        return None

    @Log.log_logger.catch
    def __init__(self, server, players: set) -> None:
        self.server = server
        self.players: list = list(players)

        self.id = Session.get_next_session_id()

        self.logger = Log.Session(self.id)

        self.is_active = True

        self.data = Queue(100)

        self.session_start_time = time()

        Session.sessions.append(self)

    def add_data_packet(self, user: "User", packet: Packet) -> None:
        if packet.code == Packet.Code.SESSION_DATA:
            self.data.put({"player": user, "data": packet.data})

    def get_data_packet(self) -> dict:
        if not self.data.empty():
            packet = self.data.get()
            return packet
        else:
            return None

    def get_session_duration(self) -> float:
        return time() - self.session_start_time

    def get_fields(self) -> dict["User", tuple[BattleField]]:
        try:
            return self.battle_fields
        except AttributeError:
            return None

    def get_players(self) -> list["User"]:
        try:
            return self.players
        except AttributeError:
            return None

    def get_player_whose_turn(self) -> "User":
        try:
            return self.players[self.player_attacks]
        except AttributeError:
            return None

    def get_winner(self) -> "User":
        try:
            return self.winner
        except AttributeError:
            return None

    def Stop(self) -> None:
        self.is_active = False

        Session.sessions.remove(self)

    def _Stop(self) -> None:
        self.logger.broadcast("Stopping game session.")
        self.logger.info("Stopping game session.")

        for player in self.players:
            player.disconnect_session(False)
            if player.net.connected():
                try:
                    player.net.send(
                        Packet(
                            Packet.Code.SESSION_DATA,
                            {"code": self.GameDataCode.SESSION_CLOSED.value},
                        )
                    )
                except Exception:
                    continue

        if self in Session.sessions:
            Session.sessions.remove(self)

    @Log.log_logger.catch
    def _start(self):
        try:
            players = "\n"
            for i, player in enumerate(self.players):
                players += f"{i + 1}. '{player.name}'\n"
            self.logger.broadcast(f"Starting game session. Players: {players}")
            self.logger.info(f"Starting game session. Players: {players}")

            for player in self.players:
                player.net.send(
                    Packet(
                        Packet.Code.SESSION_DATA,
                        {
                            "code": self.GameDataCode.SESSION_STARTED.value,
                            "session_id": self.id,
                        },
                    )
                )

            self.battle_fields = {player: None for player in self.players}
            self.phase = "setup"
            self.player_attacks = -1  # Index of player in self.players
            self.player_attacked = 0  # Index of player in self.players
            self.winner = None
            self.losers = []

            # Activating session main handler
            self._session_handler()

        except Exception as e:
            Log.exception(
                f"An exception occurred during the processing of game session #{self.id}",
                e,
            )
            self.logger.exception(
                f"An exception occurred during the processing of game session #{self.id}",
                e,
            )
        finally:
            self._Stop()

    def _session_handler(self):
        """
        Main loop for handling an active game session.
        
        This loop continues as long as:
          - Every player’s network connection is active and they are currently in the session.
          - The session itself is active.
          - There are at least a minimum number of players (MIN_PLAYERS_IN_SESSION) required to proceed.
        """
        while (
            all(
                player.net.connected() and player.is_in_session()
                for player in self.players
            )
            and self.is_active
            and len(self.players) >= MIN_PLAYERS_IN_SESSION
        ):
            # SESSION PHASE: 'setup' during this phase, the server asks users for their ship placement and saves it
            if self.phase == "setup":
                # If any player's battle field is still missing (i.e. has not been set up yet)
                if any(field is None for field in self.battle_fields.values()):
                    # Retrieve a data packet from one of the players
                    packet = self.get_data_packet()
                    if packet:
                        player, data = packet["player"], packet["data"]

                        if data.get("code") == self.GameDataCode.POST_DATA.value:
                            if (
                                data.get("data")
                                and "type" in data["data"]
                                and data["data"]["type"]
                                == self.GameDataType.BATTLE_FIELD.value
                            ):
                                try:
                                    self.battle_fields[player] = (
                                        BattleField(data.get("data")["field"]),
                                        BattleField(),
                                    )
                                    player.net.send(
                                        Packet(
                                            Packet.Code.SESSION_DATA,
                                            {"code": self.GameDataCode.COMPLETE.value},
                                        )
                                    )

                                    self.logger.info(
                                        f"Player {player.name} battlefield accepted."
                                    )
                                except ValueError as e:
                                    player.net.send(
                                        Packet(
                                            Packet.Code.ERROR,
                                            {
                                                "error_code": Network.Errors.UNCORRECT_PACKET.value,
                                                "msg": e,
                                            },
                                        )
                                    )
                                    self.logger.error(
                                        f"Player {player.name} battlefield uncorrect."
                                    )
                            else:
                                player.net.send(
                                    Packet(
                                        Packet.Code.ERROR,
                                        {
                                            "error_code": Network.Errors.UNCORRECT_PACKET.value
                                        },
                                    )
                                )
                        elif data.get("code") == self.GameDataCode.GET_DATA.value:
                            if self.battle_fields[player] is None:
                                player.net.send(
                                    Packet(
                                        Packet.Code.SESSION_DATA,
                                        {
                                            "code": self.GameDataCode.POST_DATA.value,
                                            "data": {
                                                "type": self.GameDataType.BATTLE_FIELD_REQUIRED.value
                                            },
                                        },
                                    )
                                )
                            else:
                                wait_players = []
                                for player, fields in self.battle_fields.items():
                                    if fields is None:
                                        wait_players.append(player.name)

                                if wait_players:
                                    player.net.send(
                                        Packet(
                                            Packet.Code.SESSION_DATA,
                                            {
                                                "code": self.GameDataCode.WAITING.value,
                                                "player": " ".join(wait_players),
                                            },
                                        )
                                    )
                                else:
                                    player.net.send(
                                        Packet(
                                            Packet.Code.SESSION_DATA,
                                            {"code": self.GameDataCode.WAITING.value},
                                        )
                                    )
                else:
                    # If all battle fields have been received, change the phase to 'battle'
                    self.phase = "battle"
                    self.logger.info("Moving into a new phase: 'battle'")

                    self.logger.info(
                        f"Now attacking player {self.players[self.player_attacks].name}"
                    )

            elif self.phase == "battle":
                # Battle phase: process game actions during active battles.
                packet = self.get_data_packet()
                if packet:
                    player, data = packet["player"], packet["data"]

                    if self.winner:
                        # If a winner has already been determined, notify each player of the result.
                        if player == self.winner:
                            player.net.send(
                                Packet(
                                    Packet.Code.SESSION_DATA,
                                    {
                                        "code": self.GameDataCode.POST_DATA.value,
                                        "data": {
                                            "type": self.GameDataType.RESULTS.value,
                                            "winner": "you",
                                        },
                                    },
                                )
                            )
                        else:
                            player.net.send(
                                Packet(
                                    Packet.Code.SESSION_DATA,
                                    {
                                        "code": self.GameDataCode.POST_DATA.value,
                                        "data": {
                                            "type": self.GameDataType.RESULTS.value,
                                            "winner": self.winner.name,
                                        },
                                    },
                                )
                            )

                            if player in self.losers:
                                self.losers.remove(player)

                            if len(self.losers) == 0:
                                self.Stop()
                    else:
                        # No winner is declared yet, so handle gameplay data.
                        if data.get("code") == self.GameDataCode.POST_DATA.value:
                            if data.get("data") and "type" in data["data"]:
                                payload = data["data"]
                                if (
                                    payload["type"]
                                    == self.GameDataType.COORDINATE.value
                                ):
                                    player_attacked = self.players[self.player_attacked]
                                    player_attacks = self.players[self.player_attacks]

                                    if player != player_attacks:
                                        player.net.send(
                                            Packet(
                                                Packet.Code.SESSION_DATA,
                                                {
                                                    "code": self.GameDataCode.POST_DATA.value,
                                                    "data": {
                                                        "type": self.GameDataType.NOT_YOUR_TURN.value
                                                    },
                                                },
                                            )
                                        )
                                    else:
                                        # Retrieve the battlefields:
                                        #   - The attacked player's field (hidden from the attacker).
                                        #   - The attacker's view of the attacked player's field.
                                        player_attacked_field: BattleField = (
                                            self.battle_fields[player_attacked][0]
                                        )
                                        player_attacks_field: BattleField = (
                                            self.battle_fields[player_attacks][0]
                                        )
                                        player_attacks_view_field: BattleField = (
                                            self.battle_fields[player_attacks][1]
                                        )

                                        row, col = (
                                            payload["coords"]["row"],
                                            payload["coords"]["col"],
                                        )

                                        shoot_state = player_attacked_field.shoot(
                                            row, col
                                        )
                                        player_attacks_view_field.set(
                                            row, col, shoot_state
                                        )

                                        if player_attacked_field.is_all_ships_destroyed():
                                            self.logger.info(
                                                f"Player {player.name} win!"
                                            )
                                            player.net.send(
                                                Packet(
                                                    Packet.Code.SESSION_DATA,
                                                    {
                                                        "code": self.GameDataCode.POST_DATA.value,
                                                        "data": {
                                                            "type": self.GameDataType.RESULTS.value,
                                                            "winner": "you",
                                                        },
                                                    },
                                                )
                                            )

                                            self.winner = player

                                            for pl in self.players:
                                                if pl == self.winner:
                                                    continue
                                                self.losers.append(pl)
                                        else:
                                            if (
                                                shoot_state
                                                == BattleField.ShootState.HIT
                                            ):
                                                self.logger.info(
                                                    f"Player {player.name} hit"
                                                )
                                                player.net.send(
                                                    Packet(
                                                        Packet.Code.SESSION_DATA,
                                                        {
                                                            "code": self.GameDataCode.POST_DATA.value,
                                                            "data": {
                                                                "type": self.GameDataType.SHOOT_STATE.value,
                                                                "shoot_state": BattleField.ShootState.HIT.value,
                                                                "field": player_attacks_view_field.battle_field,
                                                            },
                                                        },
                                                    )
                                                )
                                            elif (
                                                shoot_state
                                                == BattleField.ShootState.MISS
                                            ):
                                                self.logger.info(
                                                    f"Player {player.name} missed"
                                                )
                                                player.net.send(
                                                    Packet(
                                                        Packet.Code.SESSION_DATA,
                                                        {
                                                            "code": self.GameDataCode.POST_DATA.value,
                                                            "data": {
                                                                "type": self.GameDataType.SHOOT_STATE.value,
                                                                "shoot_state": BattleField.ShootState.MISS.value,
                                                                "field": player_attacks_field.battle_field,
                                                            },
                                                        },
                                                    )
                                                )
                                                self.player_attacks = (
                                                    self.player_attacks + 1
                                                ) % len(self.players)
                                                self.player_attacked = (
                                                    self.player_attacked + 1
                                                ) % len(self.players)

                                                self.logger.info(
                                                    f"Now attacking player {self.players[self.player_attacks].name}"
                                                )

                                            elif (
                                                shoot_state
                                                == BattleField.ShootState.ALREADY_SHOT
                                            ):
                                                self.logger.info(
                                                    f"Player {player.name} already shot at same place"
                                                )
                                                player.net.send(
                                                    Packet(
                                                        Packet.Code.SESSION_DATA,
                                                        {
                                                            "code": self.GameDataCode.POST_DATA.value,
                                                            "data": {
                                                                "type": self.GameDataType.SHOOT_STATE.value,
                                                                "shoot_state": BattleField.ShootState.ALREADY_SHOT.value,
                                                            },
                                                        },
                                                    )
                                                )
                                            elif (
                                                shoot_state
                                                == BattleField.ShootState.UNKNOWN
                                            ):
                                                player.net.send(
                                                    Packet(
                                                        Packet.Code.ERROR,
                                                        {
                                                            "error_code": Network.Errors.UNCORRECT_PACKET.value
                                                        },
                                                    )
                                                )
                                else:
                                    player.net.send(
                                        Packet(
                                            Packet.Code.ERROR,
                                            {
                                                "error_code": Network.Errors.UNCORRECT_PACKET.value
                                            },
                                        )
                                    )
                            else:
                                player.net.send(
                                    Packet(
                                        Packet.Code.ERROR,
                                        {
                                            "error_code": Network.Errors.UNCORRECT_PACKET.value
                                        },
                                    )
                                )

                        elif data.get("code") == self.GameDataCode.GET_DATA.value:
                            if player == self.players[self.player_attacks]:
                                player.net.send(
                                    Packet(
                                        Packet.Code.SESSION_DATA,
                                        {
                                            "code": self.GameDataCode.POST_DATA.value,
                                            "data": {
                                                "type": self.GameDataType.BATTLE_FIELD.value,
                                                "field": self.battle_fields[player][
                                                    1
                                                ].battle_field,
                                                "player": self.players[
                                                    self.player_attacked
                                                ].name,
                                            },
                                        },
                                    )
                                )
                            else:
                                player.net.send(
                                    Packet(
                                        Packet.Code.SESSION_DATA,
                                        {
                                            "code": self.GameDataCode.POST_DATA.value,
                                            "data": {
                                                "type": self.GameDataType.NOT_YOUR_TURN.value
                                            },
                                        },
                                    )
                                )
            sleep(0.07)

    def start(self):
        Thread(target=self._start, daemon=True).start()
