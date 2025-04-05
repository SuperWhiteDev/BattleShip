import sys
from loguru import logger

LOG_FILE = "logs.log"

class Log:
    class User:
        def __init__(self, ip, name) -> None:
            self.ip = ip
            self.name = name
        def debug(self, string : str, *args, **kwargs) -> None:
            logger.debug(f"\"{self.name}\": " + string, *args, **kwargs)
        def info(self, string : str, *args, **kwargs) -> None:
            logger.info(f"\"{self.name}\": " + string, *args, **kwargs)
        def error(self, string : str, *args, **kwargs) -> None:
            logger.error(f"\"{self.name}\": " + string, *args, **kwargs)
        def exception(self, string : str, exeption : Exception, *args, **kwargs):
            logger.error(f"\"{self.name}\": " + string + f"! {exeption.__class__.__name__}: {exeption}", *args, **kwargs)
    class Session:
        def __init__(self, id) -> None:
            self.id = id
        def debug(self, string : str, *args, **kwargs) -> None:
            logger.debug(f"Session #{self.id}: " + string, *args, **kwargs)
        def info(self, string : str, *args, **kwargs) -> None:
            logger.info(f"Session #{self.id}: " + string, *args, **kwargs)
        def error(self, string : str, *args, **kwargs) -> None:
            logger.error(f"Session #{self.id}: " + string, *args, **kwargs)
        def exception(self, string : str, exeption : Exception, *args, **kwargs):
            logger.error(f"Session #{self.id}: " + string + f"! {exeption.__class__.__name__}: {exeption}", *args, **kwargs)

    log_logger = logger

    @staticmethod
    def init() -> None:
        logger.remove()
        logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <blue>{level}</blue> | <cyan>{message}</cyan>", level="DEBUG")
        logger.add(LOG_FILE, format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="100 MB", level="INFO")
    
    @staticmethod
    def debug(string : str, *args, **kwargs) -> None:
        logger.debug(string, *args, **kwargs)
    
    @staticmethod
    def info(string : str, *args, **kwargs) -> None:
        logger.info(string, *args, **kwargs)
    
    @staticmethod
    def warning(string : str, *args, **kwargs) -> None:
        logger.warning(string, *args, **kwargs)
    
    @staticmethod
    def error(string : str, *args, **kwargs) -> None:
        logger.error(string, *args, **kwargs)

    @staticmethod
    def exception(string : str, exeption : Exception, *args, **kwargs):
        logger.error(string + f"! {exeption.__class__.__name__}: {exeption}", *args, **kwargs)