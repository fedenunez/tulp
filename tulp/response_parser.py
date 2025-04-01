# response_parser.py
import re
from typing import Dict, List, Optional
from . import constants
from .logger import log

# Regex to match the start tag and capture the block name
# Example: <|||dev_file_start=stdout|||> captures 'stdout'
FILE_START_TAG_RE = re.compile(r"^<\|\|\|dev_file_start=(\w+)\|\|\|>$")

def parse_response(response_text: str) -> Dict[str, str]:
    """
    Parses the LLM's response text formatted with dev_reply and dev_file tags.

    Args:
        response_text: The raw string response from the LLM.

    Returns:
        A dictionary where keys are block names (e.g., "stdout", "stderr")
        and values are the content strings within those blocks.
        Also includes a special key `constants.TAG_REPLY_END` (value "True" or "False")
        indicating if the final reply end tag was found correctly. Returns an empty
        dict if the overall structure (reply start/end) is invalid.
    """
    blocks: Dict[str, str] = {}
    lines = response_text.strip().splitlines()

    # 1. Check for overall reply tags
    if not lines or lines[0] != constants.TAG_REPLY_START:
        log.error(f"Response missing start tag '{constants.TAG_REPLY_START}'. Raw response:\n{response_text[:500]}...")
        # Add the "False" end tag status to indicate failure
        blocks[constants.TAG_REPLY_END] = "False"
        return blocks

    # Find the end tag - check if it's the last non-empty line
    reply_end_found = False
    if lines and lines[-1] == constants.TAG_REPLY_END:
        reply_end_found = True
        # Store this information in the result dictionary
        blocks[constants.TAG_REPLY_END] = "True" # Use string value
        # Remove the reply start and end lines for block parsing
        lines = lines[1:-1]
        log.debug(f"Found {constants.TAG_REPLY_START} and {constants.TAG_REPLY_END}.")
    else:
        log.warning(f"Response missing or misplaced end tag '{constants.TAG_REPLY_END}'. Raw response end:\n...{response_text[-500:]}")
        # Mark end as not found
        blocks[constants.TAG_REPLY_END] = "False"
        # Remove only the start line if end tag wasn't the last line
        lines = lines[1:]


    # 2. Parse blocks between reply start and end
    current_block_name: Optional[str] = None
    current_content: List[str] = []

    for line in lines:
        start_match = FILE_START_TAG_RE.match(line)

        if start_match:
            # --- Start of a new block ---
            # Finish previous block if any - log warning if end tag was missing
            if current_block_name:
                log.warning(f"Found new start tag '{line}' before finding end tag for block '{current_block_name}'. Storing partial content for previous block.")
                # Store partial content before switching
                block_content_str = "\n".join(current_content).strip()
                blocks[current_block_name] = block_content_str
                # Reset just in case, though logic below does it too
                current_block_name = None
                current_content = []


            block_name = start_match.group(1)
            if block_name in constants.VALID_RESPONSE_BLOCK_NAMES:
                current_block_name = block_name
                current_content = [] # Reset content buffer
                log.debug(f"Started parsing block: '{current_block_name}'")
            else:
                log.warning(f"Ignoring block with unrecognized name: '{block_name}'")
                current_block_name = None # Stop collecting content until next valid start tag
                current_content = []

        elif line == constants.TAG_FILE_END:
            # --- End of the current block ---
            if current_block_name:
                # Store collected content
                # Join lines and strip leading/trailing whitespace from the final block content
                block_content_str = "\n".join(current_content).strip()
                blocks[current_block_name] = block_content_str
                log.debug(f"Finished parsing block: '{current_block_name}' ({len(block_content_str)} chars)")
                current_block_name = None # Reset for next block
                current_content = []
            else:
                # End tag found without a corresponding start tag being active
                log.warning(f"Found end tag '{constants.TAG_FILE_END}' without an active block. Ignoring.")

        else:
            # --- Content line ---
            if current_block_name:
                # Add line to the content of the currently active block
                current_content.append(line)
            # else: # Content outside any block - ignore? Or log? Ignore silently.
                # pass


    # Check if a block was left open at the end
    if current_block_name:
        log.warning(f"Response ended while block '{current_block_name}' was still open (missing {constants.TAG_FILE_END}). Storing partial content.")
        block_content_str = "\n".join(current_content).strip()
        blocks[current_block_name] = block_content_str

    # Final validation summary
    if len(blocks) <= 1 and blocks.get(constants.TAG_REPLY_END, "False") == "False": # Only contains end tag status
         log.warning("Parsed response dictionary contains no valid blocks and failed structure checks.")
    # Use BLOCK constants for validation checks
    elif constants.BLOCK_STDOUT not in blocks and constants.BLOCK_ERROR not in blocks:
         # Check if stdout/error are missing only if parsing seemed otherwise okay (end tag found)
         if has_reply_end(blocks):
             log.warning(f"Neither '{constants.BLOCK_STDOUT}' nor '{constants.BLOCK_ERROR}' block found in the response.")

    log.debug(f"Final parsed block keys: {list(blocks.keys())}")
    return blocks


# --- Helper functions to access parsed blocks ---

def has_reply_end(blocks_dict: Dict) -> bool:
    """Checks if the reply end tag was found and correctly placed."""
    # Compares string value set during parsing
    return blocks_dict.get(constants.TAG_REPLY_END, "False") == "True"

def block_exists(blocks_dict: Dict, block_name: str) -> bool:
    """Checks if a block name exists as a key in the parsed dictionary."""
    # Exclude the special TAG_REPLY_END key from this check
    return block_name in blocks_dict and block_name != constants.TAG_REPLY_END

def block_content(blocks_dict: Dict, block_name: str) -> str:
    """
    Returns the content of a specific block.
    Content is already stripped during parsing.
    Returns empty string if block doesn't exist.
    """
    # Exclude the special TAG_REPLY_END key
    if block_name == constants.TAG_REPLY_END:
        return ""
    return blocks_dict.get(block_name, "")

def block_is_not_empty(blocks_dict: Dict, block_name: str) -> bool:
    """
    Checks if a block key exists and its content is not empty.
    Relies on content being stripped during parsing.
    """
    # Exclude the special TAG_REPLY_END key
    if block_name == constants.TAG_REPLY_END:
        return False
    # Check if key exists and value is non-empty string
    # Use block_content to check the potentially empty string ""
    return block_exists(blocks_dict, block_name) and bool(block_content(blocks_dict, block_name))

