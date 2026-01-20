# constants.py

# --- FML Tags (for user output if needed, separate from internal dev tags) ---
# FML_FILE_START = "<|||file_start={filepath}|||>"
# FML_FILE_END = "<|||file_end|||>"
# FML_DIR = "<|||dir={dirpath}|||>"

# --- Internal Development Tags (Used in Prompts and Parsing) ---

# Overall Reply Tags
TAG_REPLY_START = "<|||reply_start|||>"
TAG_REPLY_END = "<|||reply_end|||>" # Signals completion

# File Block Tags
TAG_FILE_START_TPL = "<|||dev_file_start={block_name}|||>"
TAG_FILE_END = "<|||dev_file_end|||>"

# Specific Block Names (used within TAG_FILE_START_TPL)
BLOCK_STDOUT = "stdout"
BLOCK_STDERR = "stderr"
BLOCK_ERROR = "error"
# Keep others if prompts/logic might use them
BLOCK_CONTEXT = "context"
BLOCK_THOUGHTS = "thoughts"
BLOCK_INNER_MESSAGE = "inner_message" # For assistant prefill examples

# --- Pre-formatted Start Tags (for convenience in prompts) ---
TAG_STDOUT_START = TAG_FILE_START_TPL.format(block_name=BLOCK_STDOUT)
TAG_STDERR_START = TAG_FILE_START_TPL.format(block_name=BLOCK_STDERR)
TAG_ERROR_START = TAG_FILE_START_TPL.format(block_name=BLOCK_ERROR)
TAG_CONTEXT_START = TAG_FILE_START_TPL.format(block_name=BLOCK_CONTEXT)
TAG_THOUGHTS_START = TAG_FILE_START_TPL.format(block_name=BLOCK_THOUGHTS)
TAG_INNER_MESSAGE_START = TAG_FILE_START_TPL.format(block_name=BLOCK_INNER_MESSAGE)


# --- Tag for Stdin Delimitation within User Prompts ---
# Using a unique delimiter avoids confusion with file tags
TAG_STDIN_PROMPT_DELIMITER_START = "<|||stdin_prompt_start|||>"
TAG_STDIN_PROMPT_DELIMITER_END = "<|||stdin_prompt_end|||>"


# --- Validation ---
# List of valid block *names* expected between start/end tags in the response
VALID_RESPONSE_BLOCK_NAMES = [
    BLOCK_STDOUT,
    BLOCK_STDERR,
    BLOCK_ERROR,
    BLOCK_CONTEXT,
    BLOCK_THOUGHTS,
    BLOCK_INNER_MESSAGE, # Allow in response if used by assistant prefill
]

# --- Configuration ---
DEFAULT_CONFIG_FILE_PATH = "~/.tulp.conf"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_MAX_CHARS = 1000000
DEFAULT_MODEL = "gpt-5-mini" # Default model setting
DEFAULT_CONTINUATION_RETRIES = 0 # Default for --cont
DEFAULT_THINKING_LEVEL = "low" # Default reasoning effort for supported models

# --- Environment Variable Prefix ---
ENV_VAR_PREFIX = "TULP_"

# --- Execution ---
MAX_EXECUTION_RETRIES = 5

# --- Logging Levels ---
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# --- Other ---
DEFAULT_INSPECT_SUBDIR_FORMAT = "%Y%m%d_%H%M%S"
