# tulp/__init__.py

# Expose the main entry point and version
from .cli import run
from .version import VERSION

__version__ = VERSION
__all__ = ['run', 'VERSION']
