# arguments.py
import argparse
import sys
from . import llms
from . import constants
from . import version
from .logger import log


def _validate_model_type(arg_value):
    """Argparse type checker for model names."""
    module = llms.get_model_module(arg_value)
    if not module:
        raise argparse.ArgumentTypeError(
            f"Invalid or unsupported model: '{arg_value}'.\n"
            f"Run 'tulp -h' to see supported model patterns."
        )
    log.debug(f"Model '{arg_value}' validated successfully.")
    return arg_value


# Human-readable model descriptions (instead of ugly regex)
MODEL_HELP = """
Supported Models:
  OpenAI      gpt-*, chatgpt-*, o1-*, o3-*, codex-*    Requires OPENAI_API_KEY
  Anthropic   claude-*                                  Requires ANTHROPIC_API_KEY
  Google      gemini-*                                  Requires GEMINI_API_KEY
  Groq        groq.<model-id>                           Requires GROQ_API_KEY
  Ollama      ollama.<model-name>                       Requires Ollama running

Examples: gpt-4o, gpt-5-mini, o3-mini, claude-3-opus, gemini-2.5-flash
"""


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
            llm_group = parser.add_argument_group('API Keys (also settable via env vars or ~/.tulp.conf)')
            for arg_def in llm_args:
                env_var = f'{constants.ENV_VAR_PREFIX}{arg_def["name"].upper()}'
                llm_group.add_argument(
                    f'--{arg_def["name"].replace("_", "-")}',
                    type=str,
                    dest=arg_def["name"].lower(),
                    metavar='KEY',
                    help=f'{arg_def["description"]} [env: {env_var}]',
                    default=None
                )

    def _parse(self):
        """Configures and runs the argparse parser."""
        parser = argparse.ArgumentParser(
            prog='tulp',
            description=f'TULP v{version.VERSION} - Process, filter, and create data using AI models.',
            epilog=MODEL_HELP,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Version
        parser.add_argument(
            '-V', '--version', action='version',
            version=f'tulp {version.VERSION}'
        )

        # Core Options
        parser.add_argument(
            '-x', '--execute', action='store_true',
            help='Generate and execute Python code (Code Interpreter mode)'
        )
        parser.add_argument(
            '-w', '--write', type=str, metavar='FILE',
            help='Write output to FILE (creates backups if exists)'
        )
        parser.add_argument(
            '-m', '--model', type=_validate_model_type, metavar='MODEL',
            help=f'AI model to use (default: {constants.DEFAULT_MODEL})'
        )
        parser.add_argument(
            '-t', '--thinking-level', type=str, choices=['low', 'medium', 'high'],
            metavar='LEVEL',
            help=f'Reasoning effort: low, medium, high (default: {constants.DEFAULT_THINKING_LEVEL})'
        )
        parser.add_argument(
            '--max-chars', type=int, metavar='N',
            help=f'Max chars per chunk for large inputs (default: {constants.DEFAULT_MAX_CHARS})'
        )
        parser.add_argument(
            '--cont', type=int, metavar='N',
            help='Auto-continue N times if response incomplete'
        )
        parser.add_argument(
            '--inspect-dir', type=str, metavar='DIR',
            help='Save request/response JSON to DIR for debugging'
        )

        # Logging Options
        log_group = parser.add_mutually_exclusive_group()
        log_group.add_argument(
            '-v', '--verbose', action='store_true', dest='v',
            help='Verbose output (DEBUG level)'
        )
        log_group.add_argument(
            '-q', '--quiet', action='store_true', dest='q',
            help='Quiet output (ERROR level only)'
        )

        # Load LLM specific arguments
        self._load_llm_arguments(parser)

        # Positional Argument
        parser.add_argument(
            'request', nargs=argparse.REMAINDER, metavar='REQUEST',
            help='Instructions in natural language (reads stdin if piped)'
        )

        parsed_args = parser.parse_args()

        # Combine remainder args into a single request string
        if parsed_args.request:
            parsed_args.request = " ".join(parsed_args.request).strip()
        else:
            parsed_args.request = ""

        log.debug(f"Parsed arguments: {vars(parsed_args)}")
        return parsed_args

    def get_args(self):
        """Returns the parsed arguments object."""
        return self.args


# Function to get the singleton instance easily
def get_args():
    """Returns the singleton parsed arguments object."""
    return TulpArgs().get_args()
