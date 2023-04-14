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

def print_yellow(text):
    """Prints text in yellow"""
    print_color(text, YELLOW)

def print_orange(text):
    """Prints text in orange"""
    print_color(text, ORANGE)

def print_red(text):
    """Prints text in red"""
    print_color(text, RED)

def print_bold(text):
    """Prints text in bold"""
    print_color(text, BOLD)

def print_grey(text):
    """Prints text in bold"""
    print_color(text, GREY)

class Logger:
    def __init__(self):
        self.log_level = config.log_level

    def error(self, message):
        if self.log_level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            print_red(f'[ERROR] {message}')

    def warning(self, message):
        if self.log_level in ['WARNING', 'INFO', 'DEBUG']:
            print_orange(f'[WARNING] {message}')

    def info(self, message):
        if self.log_level in ['INFO', 'DEBUG']:
            print_bold(f'[INFO] {message}')

    def debug(self, message):
        if self.log_level == 'DEBUG':
            print_grey(f'[DEBUG] {message}')

if __name__ == '__main__':
    # Example usage
    logger = Logger()
    logger.error('This is an error message')
    logger.warning('This is a warning message')
    logger.info('This is an info message')
    logger.debug('This is a debug message')
