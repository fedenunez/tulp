# config.py
import os
import configparser
import re # Import re for section matching
from . import constants
from .logger import log

# Regex to find the start of a section like [section]
SECTION_RE = re.compile(r"^\s*\[.+?\]")

class TulpConfig:
    """
    Handles loading configuration from a file and environment variables.
    Uses a Singleton pattern for easy access throughout the application.
    """
    _instance = None

    def __new__(cls, args=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        if not cls._instance._initialized and args is not None:
             cls._instance._initialize(args)
        elif not cls._instance._initialized and args is None:
             log.warning("TulpConfig re-accessed without args before full initialization.")
             # Or raise RuntimeError("TulpConfig must be initialized with args first.")
        return cls._instance

    def _initialize(self, args):
        """Initializes the configuration instance."""
        if self._initialized:
            return
        self._initialized = True

        self.config = configparser.ConfigParser(interpolation=None) # Disable interpolation for simplicity
        self.config_file_path = os.path.expanduser(constants.DEFAULT_CONFIG_FILE_PATH)
        config_string_to_parse = ""

        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    start_parsing = False
                    valid_lines = []
                    for line in lines:
                        # Check if the line marks the start of a section
                        if SECTION_RE.match(line):
                            start_parsing = True
                        # Once a section starts, include all subsequent lines
                        if start_parsing:
                            valid_lines.append(line)

                    if valid_lines:
                        config_string_to_parse = "".join(valid_lines)
                        log.debug(f"Pre-processed config content before parsing:\n{config_string_to_parse[:500]}...") # Log preview
                        self.config.read_string(config_string_to_parse)
                        log.debug(f"Successfully parsed configuration from: {self.config_file_path}")
                    else:
                        log.debug(f"No valid INI section found in {self.config_file_path}. File might be empty or contain only comments/invalid lines.")
            else:
                 log.debug(f"Configuration file not found: {self.config_file_path}")

        except configparser.Error as e:
            log.error(f"Error parsing configuration content from '{self.config_file_path}': {e}. Using defaults.")
            # Reset config object to ensure clean state after parsing error
            self.config = configparser.ConfigParser(interpolation=None)
        except IOError as e:
             log.error(f"Error reading configuration file '{self.config_file_path}': {e}. Using defaults.")
             self.config = configparser.ConfigParser(interpolation=None)
        except Exception as e:
            log.error(f"Unexpected error processing configuration file '{self.config_file_path}': {e}. Using defaults.")
            self.config = configparser.ConfigParser(interpolation=None)


        # --- Continue with loading settings as before ---

        # Determine log level (CLI > ENV > Config > Default)
        cli_log_level = (args.v and "DEBUG") or (args.q and "ERROR") if args else None
        self.log_level = cli_log_level or self._get_value("LOG_LEVEL", constants.DEFAULT_LOG_LEVEL)

        # Set global log level
        from . import logger
        logger.set_global_log_level(self.log_level)
        log.debug(f"Log level set to: {self.log_level}")

        # Load other general settings (CLI > ENV > Config > Default)
        max_chars_arg = getattr(args, 'max_chars', None)
        model_arg = getattr(args, 'model', None)
        thinking_level_arg = getattr(args, 'thinking_level', None)
        cont_arg = getattr(args, 'cont', None)
        write_arg = getattr(args, 'write', None)
        execute_arg = getattr(args, 'execute', None)
        inspect_dir_arg = getattr(args, 'inspect_dir', None)

        self.max_chars = int(max_chars_arg if max_chars_arg is not None else self._get_value("MAX_CHARS", str(constants.DEFAULT_MAX_CHARS)))
        self.model = model_arg if model_arg is not None else self._get_value("MODEL", constants.DEFAULT_MODEL)
        self.thinking_level = thinking_level_arg if thinking_level_arg is not None else self._get_value("THINKING_LEVEL", constants.DEFAULT_THINKING_LEVEL)
        self.continuation_retries = int(cont_arg if cont_arg is not None else self._get_value("CONT", str(constants.DEFAULT_CONTINUATION_RETRIES)))
        self.write_file = write_arg if write_arg is not None else self._get_value("WRITE_FILE", None)
        self.execute_code = bool(execute_arg) if execute_arg is not None else self._get_value("EXECUTE_CODE", "False").lower() in ('true', '1', 't', 'y', 'yes')
        self.inspect_dir = inspect_dir_arg if inspect_dir_arg is not None else self._get_value("INSPECT_DIR", None)

        log.debug(f"Using config file: {self.config_file_path}")
        log.debug(f"Max chars: {self.max_chars}")
        log.debug(f"Model: {self.model}")
        log.debug(f"Thinking Level: {self.thinking_level}")
        log.debug(f"Continuation retries: {self.continuation_retries}")
        log.debug(f"Write file: {self.write_file}")
        log.debug(f"Execute code: {self.execute_code}")
        log.debug(f"Inspect dir: {self.inspect_dir}")

        # Load LLM-specific arguments
        self._load_llm_arguments(args)


    def _get_value(self, key: str, default_value: str = None) -> str:
        """
        Retrieves a configuration value, checking ENV, then config file, then default.
        Keys are expected in UPPER_SNAKE_CASE.
        """
        env_var_name = f"{constants.ENV_VAR_PREFIX}{key.upper()}"
        value = os.environ.get(env_var_name)

        if value is None:
            # Config file lookup
            # Use the safe get() method with fallback on the pre-parsed config object
            try:
                # configparser automatically looks in [DEFAULT] if section is not specified
                # or if getting from DEFAULTSECT directly
                value = self.config.get(configparser.DEFAULTSECT, key.upper(), fallback=default_value)
            except Exception as e:
                log.error(f"Error getting config key '{key.upper()}' from config object: {e}. Using default.")
                value = default_value
        # else: Value was found in environment variables

        # Final check if value is still None (e.g., key not in config, fallback was None)
        if value is None:
            value = default_value

        source = "environment variable" if os.environ.get(env_var_name) is not None else "config file/default"
        log.debug(f"Config value for {key.upper()}: '{value}' (Source: {source}, Default used if None: '{default_value}')")
        return value


    def get_llm_argument(self, arg_name: str) -> str | None:
        """Gets a loaded LLM-specific argument."""
        attr_name = arg_name.lower()
        return getattr(self, attr_name, None)

    def _load_llm_arguments(self, args):
        """Loads LLM-specific arguments from CLI > ENV > Config file."""
        try:
             from . import llms
        except ImportError:
             log.error("Failed to import llms module while loading arguments.")
             return

        for llm_arg_def in llms.get_arguments_definitions():
            arg_name = llm_arg_def["name"]
            config_key = arg_name.upper()
            default_value = llm_arg_def["default"]
            attr_name = arg_name.lower()

            cli_value = getattr(args, attr_name, None) if args else None
            final_value = cli_value if cli_value is not None else self._get_value(config_key, default_value)
            setattr(self, attr_name, final_value)

            log_value = final_value
            if "key" in attr_name.lower() and final_value is not None:
                 log_value = final_value[:4] + "****" + final_value[-4:] if len(str(final_value)) > 8 else "****"
            log.debug(f"LLM Arg {arg_name}: '{log_value}'")

# --- Singleton Access ---
_tulp_config_instance = None

def initialize_config(args=None):
    """Initializes the singleton config instance. Must be called once with args."""
    global _tulp_config_instance
    if _tulp_config_instance is None:
         log.debug("Initializing TulpConfig singleton...")
         _tulp_config_instance = TulpConfig(args)
    elif not _tulp_config_instance._initialized and args is not None:
         log.debug("Completing TulpConfig initialization...")
         _tulp_config_instance._initialize(args)
    return _tulp_config_instance

def get_config():
    """Returns the singleton TulpConfig instance. Assumes initialize_config was called."""
    global _tulp_config_instance
    if _tulp_config_instance is None or not _tulp_config_instance._initialized:
        raise RuntimeError("TulpConfig not initialized. Call initialize_config(args) first.")
    return _tulp_config_instance
