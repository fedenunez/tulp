import os
import sys
from . import tulpconfig

config = tulpconfig.TulipConfig()

class Logger:
    def __init__(self):
        self.log_level = config.log_level

    def error(self, message):
        if self.log_level in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
            print(f'[ERROR] {message}', file=sys.stderr)

    def warning(self, message):
        if self.log_level in ['WARNING', 'INFO', 'DEBUG']:
            print(f'[WARNING] {message}', file=sys.stderr)

    def info(self, message):
        if self.log_level in ['INFO', 'DEBUG']:
            print(f'[INFO] {message}', file=sys.stderr)

    def debug(self, message):
        if self.log_level == 'DEBUG':
            print(f'[DEBUG] {message}', file=sys.stderr)

if __name__ == '__main__':
    # Example usage
    logger = Logger()
    logger.error('This is an error message')
    logger.warning('This is a warning message')
    logger.info('This is an info message')
    logger.debug('This is a debug message')
