# prompts/filtering_program.py
from typing import List, Dict, Any
from .. import version
from .. import constants
from ..logger import log

def getMessages(user_instructions: str, stdin_example_chunk: str, **kwargs) -> List[Dict[str, str]]:
    """
    Generates prompt messages for creating a Python program to filter/process stdin.
    Uses the new FML-like dev tag format in the response template.
    """
    log.debug("Generating filtering program prompt (new tags).")
    request_messages = []

    # NOTE: Use BLOCK constants when referring to block names in explanations
    system_instructions = f"""# You are a Unix cli tool named tulp version {version.VERSION} assisting in Python program generation.
- Your task is to write a standalone Python 3 program based *only* on the user's `Request`.
- The program you create MUST read all data from standard input (`sys.stdin`) and write its final processed result to standard output (`sys.stdout`).
- The program should function robustly like a standard Unix filter tool.

# Python Program Requirements:
- The *entire* Python program MUST be written inside a {constants.TAG_STDOUT_START} / {constants.TAG_FILE_END} block pair.
- Start the program with a concise inline comment (`#`) describing its purpose.
- Include ALL necessary `import` statements at the very beginning (standard libraries preferred). Import `sys`.
- The core logic should typically be within a `main()` function.
- Read data from `sys.stdin`. Handle potential large inputs if appropriate (e.g., process line by line if possible).
- Perform the processing as described in the user's `Request`.
- Write the final processed result to `sys.stdout`. Use `print()` or `sys.stdout.write()`.
- Add brief, helpful inline comments (`#`) before key sections to explain the logic.
- Ensure the generated code is complete, runnable, and syntactically correct Python 3.
- Use a `if __name__ == "__main__":` block to call `main()`.

# Response Format (MUST Follow Exactly):
- Your entire response MUST start EXACTLY with {constants.TAG_REPLY_START} and end EXACTLY with {constants.TAG_REPLY_END}.
- Inside the reply, include the mandatory {constants.TAG_STDOUT_START} / {constants.TAG_FILE_END} block containing the Python code.
- Include the {constants.TAG_STDERR_START} / {constants.TAG_FILE_END} block for explanations.
- Tags MUST be on their own lines.

## Response Template
{constants.TAG_REPLY_START}
{constants.TAG_STDOUT_START}
# Python program to process stdin: [Brief description based on request]
import sys
# ... other necessary imports ...

def main():
    # Read all stdin data (adjust if line-by-line is better)
    input_data = sys.stdin.read()

    # --- Processing Logic based on the Request ---
    processed_data = input_data # Placeholder
    # --------------------------------------------

    # Write the final result to stdout
    print(processed_data)

if __name__ == "__main__":
    main()
# Ensure all Python code is between the stdout start/end tags.
{constants.TAG_FILE_END}
{constants.TAG_STDERR_START}
<Provide a brief description of the generated Python program: what it does and its main logic steps. IMPORTANT: If the code requires any external libraries (not part of Python's standard library), list them here and specify the pip install command (e.g., "Requires 'pandas'. Install with: pip install pandas"). Otherwise, state "Requires only standard Python libraries." Place description between stderr start/end tags.>
{constants.TAG_FILE_END}
{constants.TAG_REPLY_END}
"""
    request_messages.append({"role": "system", "content": system_instructions})

    # User request section with updated stdin delimiter
    user_prompt = f"""# Request:
Create a Python program that reads from stdin, processes the input according to the following requirement, and prints the result to stdout:
{user_instructions}

# Example Stdin Content:
(This is just a small sample to illustrate the input format.)
{constants.TAG_STDIN_PROMPT_DELIMITER_START}
{stdin_example_chunk}
{constants.TAG_STDIN_PROMPT_DELIMITER_END}
"""
    request_messages.append({"role": "user", "content": user_prompt})

    return request_messages
