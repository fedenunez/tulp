# input_handler.py
import sys
import math
from typing import List, TYPE_CHECKING
from .logger import log

# Use TYPE_CHECKING to avoid circular import for type hints
if TYPE_CHECKING:
    from .config import TulpConfig

def read_stdin() -> str:
    """Reads stdin if available, otherwise returns an empty string."""
    input_text = ""
    if not sys.stdin.isatty():
        try:
            # Use utf-8 decoding by default, ignore errors for robustness
            input_text = sys.stdin.buffer.read().decode('utf-8', errors='ignore').strip()
            log.info(f"Read {len(input_text)} characters from stdin.")
        except Exception as e:
            log.error(f"Error reading stdin: {e}")
            input_text = "" # Ensure it's an empty string on error
    else:
        log.debug("No stdin detected (tty).")
    return input_text

def chunk_stdin(input_text: str, config: 'TulpConfig') -> List[str]:
    """
    Splits the input text into chunks based on max_chars configuration.
    Tries to split by lines first, then by character count if a line is too long.
    """
    if not input_text:
        return []

    max_chars = config.max_chars
    stdin_chunks = []

    if len(input_text) <= max_chars:
        log.debug(f"Input text fits within max_chars ({len(input_text)} <= {max_chars}). No chunking needed.")
        return [input_text]

    # Log warning about large input
    warnMsg = f"""
Input is large ({len(input_text)} characters). Tulp will divide the input into
chunks of fewer than {max_chars} characters and attempt to process them sequentially.

Please be aware that the quality of the final result may vary. Tasks that are
line-based and don't require context across chunks may work well, while tasks
requiring an overall view of the document (like summarization) may perform poorly.

You can adjust the chunk size via the --max-chars argument or the
TULP_MAX_CHARS environment variable. Using a model with a larger context
window (like gpt-4-turbo or claude-3 models) might also improve results for
context-dependent tasks.
"""
    log.warning(warnMsg)

    # Attempt to split by lines first
    compressed_lines = [""]
    input_lines = input_text.splitlines() # Use splitlines() to handle different newline types

    for line in input_lines:
        current_chunk_index = len(compressed_lines) - 1
        current_chunk_len = len(compressed_lines[current_chunk_index])

        # Check if adding the new line (plus a newline char) exceeds max_chars
        # Need to account for the newline character only if the chunk isn't empty
        line_len_with_newline = len(line) + (1 if current_chunk_len > 0 else 0)

        if current_chunk_len == 0 or (current_chunk_len + line_len_with_newline <= max_chars):
             # Add line to current chunk (add newline if chunk not empty)
            separator = "\n" if current_chunk_len > 0 else ""
            compressed_lines[current_chunk_index] += separator + line
        else:
            # Current chunk is full, start a new one or split the line
            if len(line) <= max_chars:
                # Line fits in a new chunk by itself
                compressed_lines.append(line)
            else:
                # Line itself is too long, split it by character count
                log.warning(f"A single line ({len(line)} chars) exceeds max_chars ({max_chars}). Splitting the line.")
                start_index = 0
                while start_index < len(line):
                    end_index = start_index + max_chars
                    line_chunk = line[start_index:end_index]
                    compressed_lines.append(line_chunk)
                    start_index = end_index


    # Final list of chunks - filter out potential empty strings if any were created
    stdin_chunks = [chunk for chunk in compressed_lines if chunk]

    log.info(f"Input text split into {len(stdin_chunks)} chunks.")
    for i, chunk in enumerate(stdin_chunks):
        log.debug(f"Chunk {i+1} size: {len(chunk)} chars")

    return stdin_chunks
