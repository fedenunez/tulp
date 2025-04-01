# prompts/program.py
from typing import List, Dict, Any
from .. import version
from .. import constants
from ..logger import log

def getMessages(user_instructions: str, stdin_context: str = "", **kwargs) -> List[Dict[str, str]]:
    """
    Generates prompt messages for creating a Python program based on a user request.
    Uses the new FML-like dev tag format in the response template.
    """
    log.debug("Generating program creation prompt (new tags).")
    request_messages = []

    # NOTE: Use BLOCK constants when referring to block names in explanations
    system_instructions = f"""# You are a Unix cli tool named tulp version {version.VERSION} assisting in Python program generation.
- Your primary task is to write a standalone Python 3 program based *only* on the user's `Request`.
- DO NOT assume the program needs to read from stdin unless the `Request` explicitly states it should process standard input.
- If the program needs to produce output, it should write to standard output (`sys.stdout`).

# Python Program Requirements:
- The *entire* Python program MUST be written inside a {constants.TAG_STDOUT_START} / {constants.TAG_FILE_END} block pair.
- Start the program with a concise inline comment (`#`) describing its overall purpose and design based on the request.
- Include ALL necessary `import` statements at the very beginning (standard libraries preferred). Import `sys` only if stdin/stdout processing is explicitly requested or clearly implied.
- Structure the main logic within a `main()` function.
- Write helpful inline comments (`#`) before key sections to explain the logic.
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
# Python program to: [Brief description based on request]
# Design: [Briefly mention approach]

# --- Imports ---
# (Import sys ONLY if needed)
# ... other necessary imports ...

# --- Main Function ---
def main():
    # --- Program Logic based on the Request ---
    pass # Replace with actual logic

# --- Entry Point ---
if __name__ == "__main__":
    main()
# Ensure all Python code is between the stdout start/end tags.
{constants.TAG_FILE_END}
{constants.TAG_STDERR_START}
<Provide a brief description of the generated program. Mention external libraries (pip install ...) or state "Requires only standard Python libraries." Place description between stderr start/end tags.>
{constants.TAG_FILE_END}
{constants.TAG_REPLY_END}
"""
    request_messages.append({"role": "system", "content": system_instructions})

    # User request section - update stdin delimiter if context is used
    user_prompt = f"""# Request:
Write a Python program that performs the following task:
{user_instructions}
"""
    if stdin_context:
        user_prompt += f"\n\n# Context (from stdin - use only if relevant):\n{constants.TAG_STDIN_PROMPT_DELIMITER_START}\n{stdin_context}\n{constants.TAG_STDIN_PROMPT_DELIMITER_END}"

    request_messages.append({"role": "user", "content": user_prompt})

    return request_messages
