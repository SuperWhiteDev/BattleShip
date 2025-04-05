from threading import Thread
from time import sleep
from log import Log

class Session:
    sessions = []

    @staticmethod
    def get_next_session_id():
        return len(Session.sessions)
    
    @Log.log_logger.catch
    def __init__(self, server, players : list) -> None:
        self.server = server
        self.players = players

        self.id = Session.get_next_session_id()

        self.logger = Log.Session(self.id)

        self.is_active = True
    
        Session.sessions.append(self)

    def Stop(self) -> None:
        self.is_active = False

        Session.sessions.remove(self)

    @Log.log_logger.catch
    def _start(self):
        try:
            players = "\n"
            for i, player in enumerate(self.players):
                players += f"{i+1}. '{player.name}'\n"
            self.logger.info(f"Starting game session. Players: {players}")

            for player in self.players:
                player.send_data(f"Session started ID={self.id}")

            while all(player.is_connected for player in self.players) and self.is_active:
                #Log.debug(f"Session working #{session.session_id}!")
                sleep(1.0)
        except Exception as e:
            Log.exception(f"An exception occurred during the processing of game session #{self.id}", e)
        finally:
            self.logger.info(f"Stopping game session.")

            for player in self.players:
                if player.is_connected:
                    try:
                        player.send_data("Session closed")
                    except OSError:
                        continue
    def start(self):
        Thread(target=self._start, daemon=True).start()