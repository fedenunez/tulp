# executor.py
import subprocess
import sys
import re
from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from .logger import log
from . import constants
# Import the UPDATED parser functions and relevant constants
from .response_parser import parse_response, has_reply_end, block_exists, block_content, block_is_not_empty
from .output_handler import cleanup_output, OutputFileWriter

# Type hints
if TYPE_CHECKING:
    from .config import TulpConfig
    from .promptSerializer import RequestMessageSerializer
    LlmClientType = Any
    PromptFactoryType = Any

def execute_python_code(code: str, input_data: str) -> Tuple[str, str, int]:
    """Executes the given Python code string in a subprocess."""
    # ... (This function remains unchanged internally) ...
    log.info("Executing Python code in subprocess...")
    try:
        code_bytes = code.encode('utf-8')
        input_bytes = input_data.encode('utf-8')
        process = subprocess.Popen(
            [sys.executable, "-c", code_bytes],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout_res_bytes, stderr_res_bytes = process.communicate(input=input_bytes)
        return_code = process.returncode
        stdout_res = stdout_res_bytes.decode('utf-8', errors='replace')
        stderr_res = stderr_res_bytes.decode('utf-8', errors='replace')
        log.info(f"Code execution finished with return code: {return_code}")
        if stderr_res.strip():
            log.debug(f"Code stderr:\n-------\n{stderr_res.strip()}\n-------")
        if stdout_res.strip():
             log.debug(f"Code stdout:\n-------\n{stdout_res.strip()}\n-------")
        return stdout_res, stderr_res, return_code
    except FileNotFoundError:
        log.error(f"Error: Python executable not found at '{sys.executable}'. Check your Python installation.")
        return "", "Python executable not found.", 1
    except Exception as e:
        log.error(f"Error during code execution setup: {e}")
        return "", f"Failed to start Python process: {e}", 1

def handle_execution_request(
    llm_client: 'LlmClientType',
    prompt_factory: 'PromptFactoryType',
    user_request: str,
    stdin_chunks: List[str],
    config: 'TulpConfig',
    args: Any,
    inspect_manager: 'RequestMessageSerializer | None'
) -> int:
    """Handles code generation and execution using the new tag format."""
    retries = 0
    max_retries = constants.MAX_EXECUTION_RETRIES
    combined_stdin = "".join(stdin_chunks) if stdin_chunks else ""
    stdin_context_chunk = stdin_chunks[0] if stdin_chunks else ""

    request_messages = prompt_factory.getMessages(user_request, stdin_context_chunk)
    last_llm_response = None

    while retries < max_retries:
        log.info(f"Attempt {retries + 1}/{max_retries} to generate and execute code...")

        # Log request messages if needed
        if log._should_log('DEBUG'):
            for i, req in enumerate(request_messages):
                content_preview = req.get('content', '')[:500] + ('...' if len(req.get('content', '')) > 500 else '')
                log.debug(f"Request Message {i+1} Role: {req.get('role', 'N/A')}\nContent:\n-------\n{content_preview}\n-------")

        log.debug("Sending request to LLM for code generation...")
        try:
            response = llm_client.generate(request_messages)
            last_llm_response = response
            log.debug(f"LLM Response: {response}")

            if inspect_manager:
                inspect_manager.save(request_messages, response, f"exec_attempt_{retries}")

            response_text = response.get("content", "")
            if not response_text:
                 log.warning("LLM returned an empty response content.")
                 if retries < max_retries -1:
                      log.warning("Retrying due to empty LLM response.")
                      request_messages.append(response)
                      # Use new constants in retry message
                      request_messages.append({"role": "user", "content": f"You returned an empty response. Please provide the Python code in the {constants.TAG_STDOUT_START}/{constants.TAG_FILE_END} block as requested."})
                      retries += 1
                      continue
                 else:
                      log.error("LLM returned empty response after retries. Giving up.")
                      return 1

            # Parse using the new parser
            blocks = parse_response(response_text)

            # Check for reply end tag - less critical here, but good practice
            if not has_reply_end(blocks):
                 log.warning(f"LLM response for code generation might be incomplete (missing {constants.TAG_REPLY_END}).")

            # Log stderr from LLM if present, using new block name
            if block_is_not_empty(blocks, constants.BLOCK_STDERR):
                log.info(f"[LLM stderr] {block_content(blocks, constants.BLOCK_STDERR)}")

            # Check for LLM-reported errors first, using new block name
            if block_is_not_empty(blocks, constants.BLOCK_ERROR):
                 error_msg = block_content(blocks, constants.BLOCK_ERROR)
                 log.error(f"LLM reported an error during code generation: {error_msg}")
                 return 1

            # Check if code block exists and is not empty, using new block name constant
            if not block_is_not_empty(blocks, constants.BLOCK_STDOUT):
                log.error(f"LLM did not provide Python code in the '{constants.BLOCK_STDOUT}' block.")
                if retries < max_retries - 1:
                    log.warning(f"Retrying code generation as '{constants.BLOCK_STDOUT}' block was missing or empty.")
                    request_messages.append(response)
                    # Use constants.BLOCK_STDOUT in the explanation part of the user message
                    request_messages.append({
                        "role": "user",
                        "content": f"The previous response did not contain Python code in the required {constants.TAG_STDOUT_START}/{constants.TAG_FILE_END} block. Please generate the Python code as requested and place it *only* inside the '{constants.BLOCK_STDOUT}' block, ensuring it is not empty."
                    })
                    retries += 1
                    continue
                else:
                    log.error(f"Missing '{constants.BLOCK_STDOUT}' block after retries. Giving up.")
                    return 1

            # Extract and clean the code from the correct block constant name
            generated_code_raw = block_content(blocks, constants.BLOCK_STDOUT)
            generated_code = cleanup_output(generated_code_raw) # Clean markdown etc.
            log.debug(f"Generated Python code:\n-------\n{generated_code}\n-------")

            # Optionally write the generated code to a file
            if config.write_file:
                writer = OutputFileWriter()
                ok, msg = writer.write_to_file(config.write_file, generated_code)
                if ok: log.info(f"Generated code written to: {msg}")
                else: log.error(f"Failed to write generated code: {msg}")

            # --- Execute the generated code ---
            log.info("Executing the generated Python code...")
            code_stdout, code_stderr, exit_code = execute_python_code(generated_code, combined_stdin)

            if exit_code == 0:
                log.info("Code executed successfully.")
                if code_stdout:
                    try:
                        sys.stdout.buffer.write(code_stdout.encode('utf-8'))
                        if not code_stdout.endswith('\n'): sys.stdout.buffer.write(b'\n')
                        sys.stdout.flush()
                    except Exception as print_err:
                         log.error(f"Error printing execution result to stdout: {print_err}")
                if code_stderr.strip():
                     log.info(f"Code execution produced stderr output:\n{code_stderr.strip()}")
                return 0 # Success

            else:
                # --- Execution Failed - Prepare for Retry ---
                log.warning(f"Code execution failed with exit code {exit_code}.")
                error_output = code_stderr.strip() or code_stdout.strip()
                log.error(f"Execution error output:\n-------\n{error_output or '<No error output captured>'}\n-------")

                if retries >= max_retries - 1:
                    log.error("Max retries reached for code execution. Giving up.")
                    if code_stdout: print(code_stdout, file=sys.stdout)
                    return exit_code

                # --- Prepare messages for the retry attempt ---
                log.info("Asking LLM to fix the code based on the execution error...")
                request_messages.append(response) # Append the response that generated the failing code
                # User message for code execution failure - uses constants.BLOCK_STDOUT correctly
                request_messages.append({
                    "role": "user",
                    "content": f"The Python code you provided in the '{constants.BLOCK_STDOUT}' block failed during execution. "
                               f"Error output:\n```\n{error_output}\n```\n"
                               f"Please analyze the original request, the generated code, and the error. Provide a corrected version of the Python program in the {constants.TAG_STDOUT_START}/{constants.TAG_FILE_END} block. "
                               f"Ensure all necessary imports are included and the logic correctly addresses the initial request, fixing the identified error."
                })
                retries += 1
                # Loop continues

        except Exception as e:
            log.error(f"An unexpected error occurred during the execution loop: {e}")
            import traceback
            log.debug(traceback.format_exc())
            return 1

    log.error("Execution handling finished unexpectedly after loop.")
    return 1
