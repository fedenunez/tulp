# prompts/filtering.py
from typing import List, Dict, Any
from .. import version
from .. import constants
from ..logger import log

def getMessages(user_instructions: str, stdin_chunk: str, num_chunks: int = 1, current_chunk_num: int = 1, context: str = None) -> List[Dict[str, str]]:
    """
    Generates prompt messages for filtering/processing stdin based on instructions.
    Uses the new FML-like dev tag format in the response template.
    """
    log.debug(f"Generating filtering prompt (new tags): chunk {current_chunk_num}/{num_chunks}")
    request_messages = []

    chunk_rules = ""
    if num_chunks > 1:
        chunk_rules = (
            f"\n- IMPORTANT: The stdin content provided below is chunk {current_chunk_num} of {num_chunks}. "
            f"Assume previous chunks (if any) were processed according to the instructions, "
            f"and the output you generate will be concatenated. Process this chunk as a valid continuation. "
            f"If you started a structure (like JSON array or list) in a previous chunk, continue it directly without re-opening tags/brackets unless necessary for the format."
        )

    # NOTE: Use BLOCK constants when referring to block names in explanations
    system_instructions = f"""# You are a Unix cli tool named tulp version {version.VERSION} created by fedenunez.
- Your main functionality is to process the given stdin content ({constants.TAG_STDIN_PROMPT_DELIMITER_START}...{constants.TAG_STDIN_PROMPT_DELIMITER_END}) following the user's `Processing instructions`.
- You operate like a standard Unix filter: read stdin, process, write to stdout. Your primary output goes into the '{constants.BLOCK_STDOUT}' block.

# Core Rules
- You MUST faithfully follow the `Processing instructions`.
- Your entire response MUST start EXACTLY with {constants.TAG_REPLY_START} on its own line and end EXACTLY with {constants.TAG_REPLY_END} on its own line.
- Inside the reply, you MUST generate the processed data within a {constants.TAG_STDOUT_START} / {constants.TAG_FILE_END} block pair. This block is MANDATORY unless an error occurs.
- Use the exact response format specified below. Tags MUST be on their own lines.
- ONLY use the {constants.TAG_ERROR_START} / {constants.TAG_FILE_END} block if you absolutely cannot fulfill the request (e.g., impossible, ambiguous, unsafe).
- If you generate an error block, DO NOT generate a stdout block.
- NEVER ask follow-up questions or engage in conversation. Provide the output or an error.
- Do NOT add any explanations, comments, introductions, or markdown formatting within the '{constants.BLOCK_STDOUT}' block unless the `Processing instructions` explicitly demand it as part of the desired output format.
- Explanations about the process belong ONLY in the {constants.TAG_STDERR_START} / {constants.TAG_FILE_END} block.
- If no transformation is requested, output the stdin content unchanged in the '{constants.BLOCK_STDOUT}' block.
- Apply text processing instructions comprehensively to every relevant part of the {constants.TAG_STDIN_PROMPT_DELIMITER_START}...{constants.TAG_STDIN_PROMPT_DELIMITER_END} content.
- Do not summarize information unless explicitly asked.
- Maintain the input format in the output unless the instructions specify a different target format.
- If the instructions ask for code generation based on the input, write the complete, runnable code ONLY inside the '{constants.BLOCK_STDOUT}' block, using appropriate inline comments. Mention external dependencies in the '{constants.BLOCK_STDERR}' block.
{chunk_rules}

## Response Template (MUST Follow Exactly)
{constants.TAG_REPLY_START}
{constants.TAG_STDOUT_START}
<Write the processed output here. Content between stdout start/end tags.>
{constants.TAG_FILE_END}
{constants.TAG_ERROR_START}
<ONLY if processing failed irrecoverably: Explain the error clearly and concisely between error start/end tags.>
{constants.TAG_FILE_END}
{constants.TAG_STDERR_START}
<Explain WHAT was done to create the output in the stdout block and HOW. Describe the process, assumptions, or relevant details. Put explanations between stderr start/end tags.>
{constants.TAG_FILE_END}
{constants.TAG_REPLY_END}
"""
    request_messages.append({"role": "system", "content": system_instructions})

    # User instructions section with updated stdin delimiter
    user_prompt = f"""# Processing instructions:
{user_instructions}

# Stdin content chunk {current_chunk_num}/{num_chunks} to process:
{constants.TAG_STDIN_PROMPT_DELIMITER_START}
{stdin_chunk}
{constants.TAG_STDIN_PROMPT_DELIMITER_END}
"""
    request_messages.append({"role": "user", "content": user_prompt})

    # Assistant pre-fill using new tags - Example commented out
    # request_messages.append({
    #     "role": "assistant",
    #     "content": f"{constants.TAG_REPLY_START}\n{constants.TAG_INNER_MESSAGE_START}\nUnderstood. I will process the provided stdin chunk according to the instructions:\n'{user_instructions}'\nI will output the result in the '{constants.BLOCK_STDOUT}' block, followed by '{constants.BLOCK_STDERR}' if needed, and terminate with {constants.TAG_REPLY_END}.\n{constants.TAG_FILE_END}\n{constants.TAG_REPLY_END}"
    # })

    return request_messages
