# logger.py
import os
import sys
from . import constants

YELLOW = '\033[33m'
ORANGE = '\033[38;5;208m'
RED = '\033[31m'
BOLD = '\033[1m'
RESET = '\033[0m'
GREY = '\033[90m'
GREY_10 = "\033[38;5;242m"
GREY_11 = "\033[38;5;243m"
GREY_13 = "\033[38;5;245m"
GREY_14 = "\033[38;5;246m"
GREY_15 = "\033[38;5;247m"
GREY_16 = "\033[38;5;248m"
GREY_17 = "\033[38;5;249m"
GREY_18 = "\033[38;5;250m"

# Global log level setting
_global_log_level = constants.DEFAULT_LOG_LEVEL.upper()

def set_global_log_level(level: str):
    """Sets the global logging level."""
    global _global_log_level
    level_upper = level.upper()
    if level_upper in constants.LOG_LEVELS:
        _global_log_level = level_upper
    else:
        print(f"[ERROR] Invalid log level: {level}. Using {_global_log_level}.", file=sys.stderr)

def get_global_log_level() -> str:
    """Gets the global logging level."""
    return _global_log_level

# Determine if colors should be used
_use_colors = False
if sys.stderr.isatty():
    if os.name == 'posix' and os.getenv('TERM') in ['xterm', 'xterm-color', 'xterm-256color', 'screen', 'screen-256color']:
        _use_colors = True

def _print_color(text, color):
    """Prints text in the specified color to stderr."""
    if _use_colors:
        print(f"{color}{text}{RESET}", file=sys.stderr)
    else:
        print(text, file=sys.stderr)

class Logger:
    """
    A simple logger class that writes messages to stderr with optional color.
    Uses a global log level setting but can override it per instance.
    """
    def __init__(self, instance_log_level: str = None):
        self._instance_log_level = instance_log_level.upper() if instance_log_level else None
        if self._instance_log_level and self._instance_log_level not in constants.LOG_LEVELS:
            print(f"[WARNING] Invalid instance log level '{instance_log_level}'. Using global level.", file=sys.stderr)
            self._instance_log_level = None

    def _get_effective_level(self) -> str:
        """Determines the effective log level (instance or global)."""
        return self._instance_log_level or get_global_log_level()

    def _should_log(self, message_level: str) -> bool:
        """Checks if a message at a given level should be logged."""
        effective_level = self._get_effective_level()
        level_hierarchy = constants.LOG_LEVELS # Assumes order: DEBUG, INFO, WARNING, ERROR, CRITICAL
        try:
            return level_hierarchy.index(message_level.upper()) >= level_hierarchy.index(effective_level)
        except ValueError:
            return False # Unknown level

    def error(self, message):
        if self._should_log('ERROR'):
            _print_color(f'[ERROR] {message}', RED)

    def warning(self, message):
        if self._should_log('WARNING'):
            _print_color(f'[WARNING] {message}', ORANGE)

    def info(self, message):
        if self._should_log('INFO'):
            _print_color(f'[INFO] {message}', GREY_18)

    def debug(self, message):
        if self._should_log('DEBUG'):
            _print_color(f'[DEBUG] {message}', GREY_11)

# Default logger instance
log = Logger()

# Example usage (if run directly)
if __name__ == '__main__':
    print("Testing logger...")
    set_global_log_level("DEBUG")
    print(f"Global log level: {get_global_log_level()}")
    log.debug('This is a debug message (global level)')
    log.info('This is an info message (global level)')
    log.warning('This is a warning message (global level)')
    log.error('This is an error message (global level)')

    print("\nTesting with instance level INFO:")
    info_logger = Logger("INFO")
    info_logger.debug('This debug message should NOT appear (instance level)')
    info_logger.info('This info message SHOULD appear (instance level)')
    info_logger.warning('This warning message SHOULD appear (instance level)')
    info_logger.error('This error message SHOULD appear (instance level)')

    print("\nTesting quiet mode (global level ERROR):")
    set_global_log_level("ERROR")
    log.debug('This debug message should NOT appear (quiet mode)')
    log.info('This info message should NOT appear (quiet mode)')
    log.warning('This warning message should NOT appear (quiet mode)')
    log.error('This error message SHOULD appear (quiet mode)')
