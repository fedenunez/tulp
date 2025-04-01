# output_handler.py
import os
import sys
import re
from .logger import log

# --- Output Cleaning ---

# Regex to find potential markdown code block fences (```) at start/end
# Make it non-greedy (.*?) if language identifier might contain weird chars
CODE_BLOCK_RE = re.compile(r"^\s*```[a-zA-Z]*\n(.*?)\n```\s*$", re.DOTALL | re.MULTILINE)

def cleanup_output(output: str) -> str:
    """
    Cleans up the generated output:
    - Removes leading/trailing whitespace and blank lines.
    - Removes markdown code block fences (```) if they wrap the entire output.
    """
    # Strip leading/trailing whitespace first
    cleaned = output.strip()

    # Check if the entire string is wrapped in ```...```
    match = CODE_BLOCK_RE.match(cleaned)
    if match:
        # Extract content inside the fences
        inner_content = match.group(1).strip()
        log.info("Stripping markdown code block fences (```).")
        return inner_content # Return the stripped inner content
    else:
         # If no wrapping fences found, return the originally stripped string
        return cleaned


# --- Output Printing ---

def print_stdout(content: str):
    """Prints the cleaned main output (stdout block) to the actual stdout."""
    # Cleaning is now done *before* calling this typically, but apply again for safety
    cleaned_content = cleanup_output(content)
    if cleaned_content:
        # Write directly to stdout buffer to avoid potential print() issues with encoding/newlines
        try:
            sys.stdout.buffer.write(cleaned_content.encode('utf-8'))
            # Add a newline if the content doesn't already end with one,
            # mimicking print()'s default behavior for interactive use.
            if not cleaned_content.endswith('\n'):
                 sys.stdout.buffer.write(b'\n')
            sys.stdout.flush() # Ensure it's written immediately
            log.info(f"Printed {len(cleaned_content)} chars to stdout.")
        except Exception as e:
             log.error(f"Error writing to stdout: {e}")
    else:
        log.info("stdout content was empty.")

def print_stderr(content: str):
    """Prints the stderr block content directly to the actual stderr (using logger)."""
    # stderr content is usually informational, just strip whitespace
    trimmed_content = content.strip()
    if trimmed_content:
        # Log as info, as it's auxiliary output from the LLM
        log.info(f"\n--- LLM Message ---\n{trimmed_content}\n-------------------")


# --- File Writing ---

class OutputFileWriter:
    """Handles writing output to a file with automatic backup."""

    def write_to_file(self, file_path: str, content: str) -> tuple[bool, str]:
        """
        Writes content to file_path. Creates backups if the file exists.

        Args:
            file_path: The target file path.
            content: The string content to write.

        Returns:
            A tuple (success: bool, message: str). Message is filename on success, error on failure.
        """
        if not file_path:
             log.error("File path for writing cannot be empty.")
             return False, "No file path specified."

        full_path = os.path.abspath(file_path)
        log.info(f"Attempting to write output to file: {full_path}")

        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(full_path)
            if parent_dir: # Only create if not writing to current dir
                 os.makedirs(parent_dir, exist_ok=True)

            # Handle existing file backup
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                     error_msg = f"Error: Output path '{full_path}' exists and is a directory."
                     log.error(error_msg)
                     return False, error_msg
                backup_path = self._find_backup_path(full_path)
                os.rename(full_path, backup_path)
                log.warning(f"Output file '{os.path.basename(full_path)}' exists. Moved existing file to '{os.path.basename(backup_path)}'.")

            # Write the new content using UTF-8 encoding
            with open(full_path, "w", encoding='utf-8') as f:
                bytes_written = f.write(content)
            log.info(f"Successfully wrote {bytes_written} chars to '{full_path}'.")
            return True, full_path

        except OSError as e:
            error_msg = f"OS error writing to file '{full_path}': {e}"
            log.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error writing to file '{full_path}': {e}"
            log.error(error_msg)
            return False, error_msg

    def _find_backup_path(self, original_path: str) -> str:
        """Finds the next available backup file name (e.g., file.txt.backup-1)."""
        base, ext = os.path.splitext(original_path)
        counter = 0
        while True:
            counter += 1
            # Ensure backup name doesn't clash with potential future directories if counter gets huge
            backup_path = f"{base}.backup-{counter}{ext}"
            if not os.path.exists(backup_path):
                return backup_path

