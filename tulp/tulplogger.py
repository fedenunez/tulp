import os
import sys
from . import tulpconfig

config = tulpconfig.TulipConfig()

YELLOW = '\033[33m'
ORANGE = '\033[38;5;208m'
RED    = '\033[31m'
BOLD   = '\033[1m'
RESET  = '\033[0m'
GREY   = '\033[90m'
#GREY_0 = "\033[38;5;232m"
GREY_10 = "\033[38;5;242m"
GREY_11 = "\033[38;5;243m"
GREY_13 = "\033[38;5;245m"
GREY_14 = "\033[38;5;246m"
GREY_15 = "\033[38;5;247m"
GREY_16 = "\033[38;5;248m"
GREY_17 = "\033[38;5;249m"
GREY_18 = "\033[38;5;250m"




useColors = False
if sys.stderr.isatty():
    if os.name == 'posix' and os.getenv('TERM') in ['xterm', 'xterm-color', 'xterm-256color', 'screen', 'screen-256color']:
        useColors = True



def print_color(text, color):
    """Prints text in the specified color"""
    if useColors:
        print(f"{color}{text}{RESET}",file=sys.stderr)
    else:
        print(text,file=sys.stderr)

class Logger:
    def __init__(self):
        self.log_level = config.log_level

    def error(self, message):
        if self.log_level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            print_color(f'[ERROR] {message}',RED)

    def warning(self, message):
        if self.log_level in ['WARNING', 'INFO', 'DEBUG']:
            print_color(f'[WARNING] {message}',ORANGE)

    def info(self, message):
        if self.log_level in ['INFO', 'DEBUG']:
            print_color(f'[INFO] {message}',GREY_18)

    def debug(self, message):
        if self.log_level == 'DEBUG':
            print_color(f'[DEBUG] {message}',GREY_11)

if __name__ == '__main__':
    # Example usage
    logger = Logger()
    logger.error('This is an error message')
    logger.warning('This is a warning message')
    logger.info('This is an info message')
    logger.debug('This is a debug message')
