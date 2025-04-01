# core.py
import sys
import time
import re
from typing import List, Dict, Any, TYPE_CHECKING
from . import constants
from .logger import log
# Import the UPDATED parser functions and constants
from .response_parser import parse_response, has_reply_end, block_exists, block_content, block_is_not_empty
# Import output functions
from .output_handler import print_stdout, print_stderr, OutputFileWriter, cleanup_output

# Type hints
if TYPE_CHECKING:
    from .config import TulpConfig
    from .promptSerializer import RequestMessageSerializer
    LlmClientType = Any
    PromptFactoryType = Any

def process_request(
    llm_client: 'LlmClientType',
    prompt_factory: 'PromptFactoryType',
    user_request: str,
    stdin_chunks: List[str],
    config: 'TulpConfig',
    args: Any,
    inspect_manager: 'RequestMessageSerializer | None'
) -> int:
    """Processes request using the new tag format and parser."""
    if not stdin_chunks:
        stdin_chunks = [None] # Handle no-stdin case

    full_response_stdout = []
    final_stderr_content = ""
    last_response_parsed = {}

    for i, stdin_chunk in enumerate(stdin_chunks):
        is_last_chunk = (i == len(stdin_chunks) - 1)
        chunk_num_display = f"{i + 1}/{len(stdin_chunks)}"
        log.info(f"Processing chunk {chunk_num_display}...")

        response_text = ""
        finish_reason = ""
        continuation_count = config.continuation_retries
        current_continuation_attempt = 0

        # --- Initial Request ---
        request_messages = prompt_factory.getMessages(
            user_instructions=user_request,
            stdin_chunk=stdin_chunk,
            num_chunks=len(stdin_chunks),
            current_chunk_num=i + 1,
        )

        # Log request messages if needed
        if log._should_log('DEBUG'): # Check log level directly
            for msg_idx, req_msg in enumerate(request_messages):
                 log.debug(f"Chunk {chunk_num_display} Initial Req Msg {msg_idx+1} Role: {req_msg.get('role')}\nContent:\n{req_msg.get('content', '')[:500]}...")


        try:
            log.debug(f"Sending initial request for chunk {chunk_num_display} to LLM...")
            response = llm_client.generate(request_messages)
            log.debug(f"Initial LLM Response for chunk {chunk_num_display}: {response}")

            if inspect_manager:
                inspect_manager.save(request_messages, response, f"chunk_{i}_attempt_0")

            response_text += response.get("content", "")
            finish_reason = response.get("finish_reason", "")

            # --- Continuation Loop ---
            parsed_response = parse_response(response_text)

            # Check if continuation is needed using the new parser function
            needs_continuation = (
                continuation_count > 0 and
                not has_reply_end(parsed_response) and # Use new check
                not block_exists(parsed_response, constants.BLOCK_ERROR) and # Check block name
                finish_reason != "stop" and
                finish_reason != "error"
            )

            while needs_continuation:
                current_continuation_attempt += 1
                log.info(f"Response for chunk {chunk_num_display} seems incomplete (missing {constants.TAG_REPLY_END}). Requesting continuation ({current_continuation_attempt}/{config.continuation_retries})...")
                continuation_count -= 1

                request_messages.append(response) # Add previous assistant message
                request_messages.append({
                    "role": "user",
                    # Reference the new tag format in the continuation prompt
                    "content": f"Please continue generating the response exactly where you left off for chunk {chunk_num_display}. Ensure you follow the required format (starting with {constants.TAG_REPLY_START}, using {constants.TAG_FILE_START_TPL.format(block_name='...')}/{constants.TAG_FILE_END} blocks) and end the entire reply with {constants.TAG_REPLY_END} on a new line only when fully complete."
                })

                log.debug("Sending continuation request to LLM...")
                response = llm_client.generate(request_messages)
                log.debug(f"Continuation LLM Response: {response}")

                if inspect_manager:
                    inspect_manager.save(request_messages, response, f"chunk_{i}_attempt_{current_continuation_attempt}")

                new_content = response.get("content", "")
                if not new_content:
                    log.warning("Continuation request returned empty content.")
                    break

                response_text += "\n" + new_content
                finish_reason = response.get("finish_reason", "")

                # Re-parse the combined response
                parsed_response = parse_response(response_text)
                log.debug(f"Combined response after continuation {current_continuation_attempt} has reply end tag: {has_reply_end(parsed_response)}")

                # Re-evaluate if continuation is still needed
                needs_continuation = (
                    continuation_count > 0 and
                    not has_reply_end(parsed_response) and # Use new check
                    not block_exists(parsed_response, constants.BLOCK_ERROR) and # Check block name
                    finish_reason != "stop" and
                    finish_reason != "error"
                )
            # --- End Continuation Loop ---


            # --- Process Final Response for the Chunk ---
            last_response_parsed = parsed_response

            # Check reply end tag presence for logging
            if not has_reply_end(parsed_response):
                if config.continuation_retries > 0 and current_continuation_attempt == config.continuation_retries:
                     log.error(f"Max continuation retries ({config.continuation_retries}) reached for chunk {chunk_num_display}, but {constants.TAG_REPLY_END} still not found. Output might be incomplete.")
                elif finish_reason == "length":
                     log.error(f"LLM indicated response for chunk {chunk_num_display} truncated due to token limits ('{finish_reason}'). Output is likely incomplete.")
                elif finish_reason == 'error':
                     log.error(f"LLM client reported an error during generation for chunk {chunk_num_display}. Cannot continue.")
                     return 1
                else:
                     log.warning(f"{constants.TAG_REPLY_END} tag not found in the final response for chunk {chunk_num_display}. Output may be incomplete (finish_reason: '{finish_reason}').")

            # Check for LLM-reported error block using the new block name constant
            if block_is_not_empty(parsed_response, constants.BLOCK_ERROR):
                error_msg = block_content(parsed_response, constants.BLOCK_ERROR)
                log.error(f"LLM reported processing error for chunk {chunk_num_display}:")
                print(f"Tulp Error: {error_msg}", file=sys.stderr)
                return 1 # Exit on first error encountered

            # Process valid blocks
            # Retrieve stderr content using the new block name constant
            if block_exists(parsed_response, constants.BLOCK_STDERR):
                stderr_content = block_content(parsed_response, constants.BLOCK_STDERR)
                if stderr_content:
                    if is_last_chunk:
                        final_stderr_content = stderr_content
                    else:
                        log.debug(f"Stderr from chunk {chunk_num_display}:\n{stderr_content}")

            # Collect stdout content using the new block name constant
            if block_exists(parsed_response, constants.BLOCK_STDOUT):
                # Get raw content (parser already strips outer whitespace)
                chunk_stdout = parsed_response.get(constants.BLOCK_STDOUT, "")
                if chunk_stdout:
                    full_response_stdout.append(chunk_stdout)
                    log.info(f"Processed {constants.BLOCK_STDOUT} block for chunk {chunk_num_display} ({len(chunk_stdout)} chars).")
            else:
                 # Log warning if neither stdout nor error block is present
                 if not block_exists(parsed_response, constants.BLOCK_ERROR):
                     log.warning(f"No '{constants.BLOCK_STDOUT}' block found in response for chunk {chunk_num_display}.")

        except Exception as e:
            log.error(f"An unexpected error occurred during processing chunk {chunk_num_display}: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return 1
        # --- End Chunk Processing Try-Except ---
    # --- End Chunk Loop ---


    # --- Final Output Aggregation and Writing ---
    final_output_raw = "".join(full_response_stdout)
    final_output_cleaned = cleanup_output(final_output_raw)

    # Check for empty output conditions
    if not final_output_cleaned and not block_exists(last_response_parsed, constants.BLOCK_ERROR):
         if len(stdin_chunks) > 0 and stdin_chunks[0] is not None:
             log.warning("Processing finished, but the combined stdout content is empty after cleaning.")
         elif len(stdin_chunks) == 1 and stdin_chunks[0] is None:
              log.warning("Request finished, but the stdout content is empty after cleaning.")

    # Print final stderr if collected
    if final_stderr_content:
        print_stderr(final_stderr_content)

    # Write or print the final stdout
    exit_code = 0
    if config.write_file:
        writer = OutputFileWriter()
        ok, msg = writer.write_to_file(config.write_file, final_output_cleaned)
        if not ok:
            log.error(f"Failed to write final output to file: {msg}")
            print_stdout(final_output_cleaned)
            exit_code = 1
        else:
            log.info(f"Final output successfully written to {msg}")
    else:
        print_stdout(final_output_cleaned)

    return exit_code
