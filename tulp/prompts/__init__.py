# prompts/__init__.py

# This file makes the 'prompts' directory a Python package.
# We can optionally add helper functions or import specific prompt modules here
# for easier access, but for now, direct imports from cli.py or core.py are fine.

# Example of pre-loading (optional):
# from . import request
# from . import filtering
# from . import program
# from . import filtering_program

# Or a factory function (optional):
# def get_prompt_factory(prompt_type: str):
#     if prompt_type == "request":
#         from . import request
#         return request
#     elif prompt_type == "filtering":
#         from . import filtering
#         return filtering
#     elif prompt_type == "program":
#          from . import program
#          return program
#     elif prompt_type == "filtering_program":
#          from . import filtering_program
#          return filtering_program
#     else:
#         raise ValueError(f"Unknown prompt type: {prompt_type}")

# Make specific modules easily importable (e.g., from tulp import prompts)
from . import filtering
from . import filtering_program
from . import program
from . import request

__all__ = ['filtering', 'filtering_program', 'program', 'request']

