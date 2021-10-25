"""Custom Logging"""
import logging

# Reset
COLOUR_OFF = "\033[0m"       # Text Reset

# Regular Colors
BLACK = "\033[0;30m"        # Black
RED = "\033[0;31m"          # Red
GREEN = "\033[0;32m"        # Green
YELLOW = "\033[0;33m"       # Yellow
BLUE = "\033[0;34m"         # Blue
PURPLE = "\033[0;35m"       # Purple
CYAN = "\033[0;36m"         # Cyan
GREY = "\033[0;37m"        # Grey
WHITE = "\033[0;38m"        # White

# Bold
BBLACK = "\033[1;30m"       # Black
BRED = "\033[1;31m"         # Red
BGREEN = "\033[1;32m"       # Green
BYELLOW = "\033[1;33m"      # Yellow
BBLUE = "\033[1;34m"        # Blue
BPURPLE = "\033[1;35m"      # Purple
BCYAN = "\033[1;36m"        # Cyan
BGREY = "\033[1;37m"       # Grey
BWHITE = "\033[1;38m"       # White

# Underline
UBLACK = "\033[4;30m"       # Black
URED = "\033[4;31m"         # Red
UGREEN = "\033[4;32m"       # Green
UYELLOW = "\033[4;33m"      # Yellow
UBLUE = "\033[4;34m"        # Blue
UPURPLE = "\033[4;35m"      # Purple
UCYAN = "\033[4;36m"        # Cyan
UWHITE = "\033[4;37m"       # White

# Background
ON_BLACK = "\033[40m"       # Black
ON_RED = "\033[41m"         # Red
ON_GREEN = "\033[42m"       # Green
ON_YELLOW = "\033[43m"      # Yellow
ON_BLUE = "\033[44m"        # Blue
ON_PURPLE = "\033[45m"      # Purple
ON_CYAN = "\033[46m"        # Cyan
ON_WHITE = "\033[47m"       # White

logging.getLogger('twitchio').setLevel(logging.DEBUG)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)
logging.getLogger("spotipy.client").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
logging.getLogger("twitchio.websocket").setLevel(logging.DEBUG)
logging.getLogger("twitchio.client").setLevel(logging.ERROR)
logging.basicConfig(filename="data/logs.log", level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s', datefmt='%d/%m/%Y %H:%M:%S')


def setupLogger(logger):
    """Setup Custom Logger"""
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] | %(message)s', '%d/%m/%Y %H:%M:%S')
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    logger.setLevel(5)

    def decorateEmit(formatHandler):
        def new(*args):
            levelno = args[0].levelno
            if levelno >= logging.CRITICAL:
                colour = BPURPLE
            elif levelno >= logging.ERROR:
                colour = BRED
            elif levelno >= logging.WARNING:
                colour = BYELLOW
            elif levelno >= logging.INFO:
                colour = BGREY
            elif levelno >= logging.DEBUG:
                colour = BGREEN
            elif levelno == 5:
                colour = BBLUE
                args[0].levelname = "CHAT"
            elif levelno == 6:
                colour = BCYAN
                args[0].levelname = "COMMAND"
            elif levelno == 7:
                colour = BWHITE
                args[0].levelname = "BOT MESSAGE"
            elif levelno == 8:
                colour = BGREEN
                args[0].levelname = "SPOTIFY"
            else:
                colour = COLOUR_OFF
            args[0].levelname = "{0}{1}\033[0;0m".format(colour, args[0].levelname)
            args[0].name = "{0}{1}\033[0;0m".format(BBLACK, args[0].name)
            return formatHandler(*args)
        return new

    streamHandler.emit = decorateEmit(streamHandler.emit)
    logger.addHandler(streamHandler)
