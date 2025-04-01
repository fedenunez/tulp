# arguments.py
import argparse
import os
from . import llms
from . import constants
from . import version
from .logger import log

def _validate_model_type(arg_value):
   """Argparse type checker for model names."""
   module = llms.get_model_module(arg_value)
   if not module:
       raise argparse.ArgumentTypeError(f"Invalid or unsupported model: '{arg_value}'.\nSupported patterns:\n{llms.get_models_description()}")
   log.debug(f"Model '{arg_value}' validated successfully.")
   return arg_value

class TulpArgs:
    """Parses and stores command-line arguments using argparse."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.args = cls._instance._parse()
        return cls._instance

    def _load_llm_arguments(self, parser):
        """Adds LLM-specific arguments dynamically to the parser."""
        llm_args = llms.get_arguments_definitions()
        if llm_args:
            llm_group = parser.add_argument_group('LLM Provider Arguments')
            for arg_def in llm_args:
                llm_group.add_argument(
                    f'--{arg_def["name"]}',
                    type=str, # Keep as string, config handles type conversion if needed
                    # Use lower snake case for dest to match attribute access
                    dest=arg_def["name"].lower(),
                    metavar=arg_def["name"].upper(), # Use upper case for metavar
                    help=f'{arg_def["description"]} (Config/Env: {constants.ENV_VAR_PREFIX}{arg_def["name"].upper()})',
                    default=None # Let config handle default precedence
                )

    def _parse(self):
        """Configures and runs the argparse parser."""
        parser = argparse.ArgumentParser(
            description=f"""TULP v{version.VERSION} - TULP Understands Language Promptly:
A command-line tool, in the best essence of POSIX tooling, that helps you
to **process**, **filter**, and **create** data using AI models.

Tulp supports different backends and models, automatically selected based on the model name.
Currently supported model patterns:
{llms.get_models_description()}
""",
            formatter_class=argparse.RawTextHelpFormatter
        )

        # Core Options
        parser.add_argument(
            '-x', '--execute', action='store_true',
            help='Allow Tulp to generate and execute Python code to fulfill the request (Code Interpreter mode).'
        )
        parser.add_argument(
            '-w', '--write', type=str, metavar='FILE',
            help='Write the main output (<|||stdout|||>) to FILE. Creates backups (.backup-N) if FILE exists.'
        )
        parser.add_argument(
            '--model', type=_validate_model_type, metavar='MODEL_NAME',
            help=f'Select the AI model to use (e.g., gpt-4o, claude-3-opus-20240229, groq.llama3-70b-8192). '
                 f'(Config/Env: {constants.ENV_VAR_PREFIX}MODEL, default: {constants.DEFAULT_MODEL})'
        )
        parser.add_argument(
            '--max-chars', type=int, metavar='NUM',
            help=f'Max characters per LLM request chunk when processing large stdin. '
                 f'(Config/Env: {constants.ENV_VAR_PREFIX}MAX_CHARS, default: {constants.DEFAULT_MAX_CHARS})'
        )
        parser.add_argument(
            '--cont', type=int, metavar='N',
            help=f'Automatically ask the model to continue N times if the response seems incomplete (missing <|||end|||>). '
                 f'(Config/Env: {constants.ENV_VAR_PREFIX}CONT, default: {constants.DEFAULT_CONTINUATION_RETRIES})'
        )
        parser.add_argument(
             '--inspect-dir', type=str, metavar='DIR',
             help=f'Save LLM request/response messages to timestamped subdirectories in DIR for debugging. '
                  f'(Config/Env: {constants.ENV_VAR_PREFIX}INSPECT_DIR)'
        )
        # parser.add_argument('--continue-file', type=str, help='Continue processing from the file, where file is a json file created by inspect-dir') # WIP

        # Logging Options
        log_group = parser.add_mutually_exclusive_group()
        log_group.add_argument(
            '-v', '--verbose', action='store_true', dest='v', # Keep dest 'v' for consistency
            help=f'Enable verbose logging (DEBUG level). Overrides -q, config, and env. '
                 f'(Config/Env: {constants.ENV_VAR_PREFIX}LOG_LEVEL=DEBUG)'
        )
        log_group.add_argument(
            '-q', '--quiet', action='store_true', dest='q', # Keep dest 'q' for consistency
            help=f'Enable quiet logging (ERROR level). Overrides config and env. '
                 f'(Config/Env: {constants.ENV_VAR_PREFIX}LOG_LEVEL=ERROR)'
        )

        # Load LLM specific arguments
        self._load_llm_arguments(parser)

        # Positional Argument
        parser.add_argument(
            'request', nargs=argparse.REMAINDER,
            help="User's request or processing instructions in natural language. Reads from stdin if processing piped data."
        )

        parsed_args = parser.parse_args()

        # Combine remainder args into a single request string
        if parsed_args.request:
            parsed_args.request = " ".join(parsed_args.request).strip()
        else:
             parsed_args.request = "" # Ensure request is always a string

        log.debug(f"Parsed arguments: {vars(parsed_args)}")
        return parsed_args

    def get_args(self):
        """Returns the parsed arguments object."""
        return self.args

# Function to get the singleton instance easily
def get_args():
    """Returns the singleton parsed arguments object."""
    return TulpArgs().get_args()
