# cli.py
import sys
import os
import time
from typing import TYPE_CHECKING # Use for type hints to avoid circular imports
from . import arguments
# Use the initializer and getter for config
from .config import initialize_config, get_config
from . import version
from . import constants
from .logger import log, set_global_log_level # Import set_global_log_level
from .input_handler import read_stdin, chunk_stdin
from . import core
from . import executor
from . import llms
from .promptSerializer import RequestMessageSerializer

# Use TYPE_CHECKING for type hints that would cause circular imports
if TYPE_CHECKING:
    # from .config import TulpConfig # Not needed now with get_config
    from .promptSerializer import RequestMessageSerializer as InspectManagerType # Alias for clarity


def _setup_inspect_dir(inspect_base_dir: str) -> 'InspectManagerType | None':
    """Creates the inspection directory and returns a manager instance."""
    if not inspect_base_dir:
        return None

    try:
        # Create the base inspect_dir folder if it doesn't exist
        os.makedirs(inspect_base_dir, exist_ok=True)

        # Create the timestamped subdirectory
        # Use timestamp that's safe for filenames across OSes
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        inspect_folder_path = os.path.join(inspect_base_dir, timestamp_str)
        os.makedirs(inspect_folder_path, exist_ok=True)

        log.info(f"Inspection enabled. Saving interaction details to: {inspect_folder_path}")

        # Define a simple manager class locally or use PromptSerializer directly if adaptable
        class InspectManager:
            def __init__(self, base_path):
                self.base_path = base_path
                self.counter = 0 # Add counter for unique filenames

            def save(self, request_messages, response=None, suffix=""):
                 # Use counter and suffix for more descriptive names
                 filename = os.path.join(self.base_path, f"{suffix}_{self.counter:03d}.json")
                 self.counter += 1
                 serializer = RequestMessageSerializer(filename) # Creates serializer for each save
                 try:
                     serializer.save(request_messages, response)
                     log.debug(f"Saved inspection data to {filename}")
                 except Exception as e:
                     log.error(f"Failed to save inspection data to {filename}: {e}")

        return InspectManager(inspect_folder_path)

    except Exception as e:
        log.error(f"Failed to create inspect directory '{inspect_base_dir}': {e}")
        return None

def run():
    """Main entry point for the Tulp CLI application."""
    exit_code = 0
    llm_client = None # Define outside try block for potential cleanup
    try:
        # 1. Parse Arguments (Singleton)
        args = arguments.get_args()

        # 2. Initialize Configuration (Singleton, requires args)
        # This call ensures config is loaded using args for overrides
        initialize_config(args)
        # Now use get_config() to access the initialized instance
        config = get_config()
        log.debug(f"Running tulp v{version.VERSION} with model: {config.model}")

        # 3. Initialize LLM Client (Can raise errors)
        # Pass the initialized config object
        llm_client = llms.get_model_client(config.model, config)

        # 4. Read Standard Input
        input_text = read_stdin()

        # 5. Determine User Request
        user_request = args.request
        if not user_request and input_text:
            # Default action for stdin without explicit request
            user_request = "Process the input data following standard Unix filter principles. If it looks like structured data (e.g., CSV, JSON, YAML), maintain or transform the structure as appropriate. If it's plain text, summarize it concisely."
            log.info(f"No specific request provided with stdin, using default action: '{user_request}'")
        elif not user_request and not input_text:
             # No request and no stdin: Check for specific modes or prompt user
            if args.execute: # -x without request/stdin doesn't make sense
                 log.error("Execution mode (-x) requires a request or stdin data with a default action.")
                 sys.exit(1)
            # Interactive mode - prompt user for request
            try:
                print("Enter your request (Ctrl+D or empty line to finish):", file=sys.stderr)
                user_request = sys.stdin.read().strip() # Read potentially multi-line input
                if not user_request:
                    log.error("No request provided.")
                    sys.exit(1)
            except EOFError:
                log.error("No request provided (EOF detected).")
                sys.exit(1)
            except KeyboardInterrupt:
                 log.warning("\nRequest cancelled by user.")
                 sys.exit(130) # Standard exit code for Ctrl+C

        log.debug(f"User request: '{user_request}'")

        # 6. Chunk Stdin if necessary
        # Pass input_text which might be empty, and the config object
        stdin_chunks = chunk_stdin(input_text, config)

        # 7. Setup Inspection Directory if requested
        inspect_manager = _setup_inspect_dir(config.inspect_dir)

        # 8. Select Mode and Prompt Factory & Execute
        if args.execute:
            log.info("Mode: Code Execution (-x enabled)")
            if input_text: # If there was stdin, use the filtering program prompt
                from .prompts import filtering_program as prompt_factory
                log.debug("Using filtering_program prompt factory.")
                exit_code = executor.handle_execution_request(
                    llm_client, prompt_factory, user_request, stdin_chunks, config, args, inspect_manager
                )
            else: # No stdin, use the general program prompt
                from .prompts import program as prompt_factory
                log.debug("Using program prompt factory.")
                # Pass empty list for stdin_chunks if input_text was empty
                exit_code = executor.handle_execution_request(
                    llm_client, prompt_factory, user_request, [], config, args, inspect_manager
                )
        else:
            log.info("Mode: Standard Processing / Request")
            if input_text: # If there was stdin, use the filtering prompt
                from .prompts import filtering as prompt_factory
                log.debug("Using filtering prompt factory.")
                exit_code = core.process_request(
                    llm_client, prompt_factory, user_request, stdin_chunks, config, args, inspect_manager
                )
            else: # No stdin, use the direct request prompt
                from .prompts import request as prompt_factory
                log.debug("Using request prompt factory.")
                 # Pass empty list for stdin_chunks if input_text was empty
                exit_code = core.process_request(
                    llm_client, prompt_factory, user_request, [], config, args, inspect_manager
                )

    # --- Exception Handling ---
    except ValueError as ve:
        # Specific errors likely from config or setup (e.g., missing API key)
        log.error(f"Configuration or setup error: {ve}")
        exit_code = 2
    except RuntimeError as re:
        # Catch errors like config not initialized
        log.error(f"Runtime error: {re}")
        exit_code = 2
    except ImportError as ie:
         log.error(f"Missing dependency: {ie}. Please ensure all requirements are installed.")
         # Suggest installation based on error message content
         err_str = str(ie).lower()
         if 'openai' in err_str: log.error("Try running: pip install openai")
         elif 'anthropic' in err_str: log.error("Try running: pip install anthropic")
         elif 'google.generativeai' in err_str or 'google.ai' in err_str: log.error("Try running: pip install google-generativeai")
         elif 'groq' in err_str: log.error("Try running: pip install groq")
         elif 'ollama' in err_str: log.error("Try running: pip install ollama")
         exit_code = 3
    except ConnectionError as ce:
         # Specific error for connection issues (e.g., Ollama host down)
         log.error(f"Connection error: {ce}")
         exit_code = 4
    except KeyboardInterrupt:
         log.warning("\nOperation cancelled by user.")
         exit_code = 130 # Standard exit code for Ctrl+C
    except Exception as e:
        # Catch-all for unexpected errors
        log.error(f"An unexpected error occurred: {e}")
        import traceback
        # Log full traceback only if in debug mode
        # Access log level via the config instance
        try:
            config = get_config() # Try to get config again for log level check
            if config.log_level == "DEBUG":
                 log.debug(traceback.format_exc())
        except Exception: # If getting config fails, just log basic debug trace
             log.debug(traceback.format_exc()) # Log traceback if debug enabled
        exit_code = 1

    # --- Cleanup and Exit ---
    finally:
        # Potential cleanup tasks (e.g., close network connections if llm_client needs it)
        # if llm_client and hasattr(llm_client, 'close'):
        #     llm_client.close()
        log.debug(f"Tulp finished with exit code: {exit_code}")
        sys.exit(exit_code)

# Make the script executable
if __name__ == "__main__":
    run()
