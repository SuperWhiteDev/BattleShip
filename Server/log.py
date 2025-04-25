import sys
from os import mkdir, path
from loguru import logger
from settings import CONSOLE_LOGGING_SESSION_LOGS

LOG_FILE = "logs/logs.log"


class Log:
    class User:
        def __init__(self, ip, name) -> None:
            self.ip = ip
            self.name = name

        def debug(self, string: str, *args, **kwargs) -> None:
            logger.debug(f'"{self.name}": ' + string, *args, **kwargs)

        def info(self, string: str, *args, **kwargs) -> None:
            logger.info(f'"{self.name}": ' + string, *args, **kwargs)

        def error(self, string: str, *args, **kwargs) -> None:
            logger.error(f'"{self.name}": ' + string, *args, **kwargs)

        def exception(self, string: str, exception: Exception, *args, **kwargs):
            logger.error(
                f'"{self.name}": '
                + string
                + f"! {exception.__class__.__name__}: {exception}",
                *args,
                **kwargs,
            )

    class Session:
        def __init__(self, session_id) -> None:
            self.session_id = session_id

            self.logger = logger.bind(session_id=self.session_id)
            self._sink_id = logger.add(
                f"logs/session{self.session_id}.log",
                level="DEBUG",
                filter=lambda record: record["extra"].get("session_id")
                == self.session_id,
                format="Session #{extra[session_id]}: {time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
            )

        def debug(self, string: str, *args, **kwargs) -> None:
            self.logger.debug(string, *args, **kwargs)

        def info(self, string: str, *args, **kwargs) -> None:
            self.logger.info(string, *args, **kwargs)

        def error(self, string: str, *args, **kwargs) -> None:
            self.logger.error(string, *args, **kwargs)

        def exception(self, string: str, exception: Exception, *args, **kwargs) -> None:
            self.logger.error(
                string + f"! {exception.__class__.__name__}: {exception}",
                *args,
                **kwargs,
            )
        def broadcast(self, string: str, *args, **kwargs) -> None:
            logger.info(f"Session #{self.session_id}: " + string, *args, **kwargs)

    log_logger = logger

    @staticmethod
    def init() -> None:
        if not path.exists("logs/"):
            mkdir("logs/")

        logger.remove()

        if CONSOLE_LOGGING_SESSION_LOGS:
            logger.add(
                sys.stdout,
                colorize=True,
                format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <blue>{level}</blue> | <cyan>{message}</cyan>",
                level="DEBUG",
            )
        else:
            logger.add(
                sys.stdout,
                colorize=True,
                format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <blue>{level}</blue> | <cyan>{message}</cyan>",
                level="DEBUG",
                filter=lambda record: "session_id" not in record["extra"]
            )
        logger.add(
            LOG_FILE,
            format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
            rotation="100 MB",
            level="INFO",
        )

    @staticmethod
    def debug(string: str, *args, **kwargs) -> None:
        logger.debug(string, *args, **kwargs)

    @staticmethod
    def info(string: str, *args, **kwargs) -> None:
        logger.info(string, *args, **kwargs)

    @staticmethod
    def warning(string: str, *args, **kwargs) -> None:
        logger.warning(string, *args, **kwargs)

    @staticmethod
    def error(string: str, *args, **kwargs) -> None:
        logger.error(string, *args, **kwargs)

    @staticmethod
    def exception(string: str, exception: Exception, *args, **kwargs):
        logger.error(
            string + f"! {exception.__class__.__name__}: {exception}", *args, **kwargs
        )
