#!/usr/bin/python3
import openai
import argparse
import sys
import os
import math
from . import tulplogger
from . import tulpconfig
from . import version

log = tulplogger.Logger()
config = tulpconfig.TulipConfig()



# Helper functions

## cleanup_output: clenaup output, removing artifacts
def cleanup_output(output):
    olines = output.splitlines()
    # gpt-3.5 usually adds unneeded markdown codeblock wrappers, try to remove them
    if len(olines) > 2:
        if olines[0].startswith("```") and olines[-1] == "```":
            log.debug("markdown codeblock wrapping detected and stripped!")
            return "\n".join(olines[1:-1])
    return output


## block_exists(blocks_dict, key):  test if a KEY exist and is not empty
def block_exists(blocks_dict, key):
    return key in blocks_dict and len(blocks_dict[key].strip()) > 0

## VALID_BLOCKS: define the valid answer blocks  blocks
VALID_BLOCKS=["(#output)","(#inner_message)","(#error)","(#context)","(#comment)","(#end)"]
## parse_response)response_text): parse a gpt response, returning a dict with each response section 
def parse_response(response_text):
    blocks_dict={}
    lines = response_text.splitlines()
    # (#end) is not specified by us, but sometimes gpt-3.5 wrote it so we just parse it so we can keep it out

    # parse blocks:
    parsingBlock=None
    for line in lines:
        if (line in VALID_BLOCKS):
            parsingBlock=line
            if parsingBlock not in blocks_dict:
               blocks_dict[parsingBlock]=""

        else:
            if parsingBlock:
                blocks_dict[parsingBlock] += line + "\n"
            else:
                if config.model == "gpt-3.5-turbo": 
                    log.error("""
Unknown error while processing: this is usually related to gpt not honoring our
output format, please try again and try to be more specific, you can also try
with a different model (e.g., TULP_MODEL=gpt-4 tulp ...)""")
                else:
                    log.error("""
Unknown error while processing: this is usually related to gpt not honoring
our output format, please try again and try to be more specific in your
request. You can also try to enable DEBUG log to inspect the raw answer (e.g.,
TULP_LOG_LEVEL=DEBUG tulp ...)""") 
                log.debug(f"ERROR: Invalid answer format: =====\n {response_text} \n=====")
                sys.exit(2)
    return blocks_dict


## pre_process_raw_input(input_text):  split all the input and create the raw_input_chunks with chunks of text ready to be send 
def pre_process_raw_input(input_text):
    raw_input_chunks=[]
    # Split input text into chunks to fit within max chars window
    max_chars = config.max_chars  # Maximum number of chars that we will send to GPT
    if len(input_text) > max_chars:
        warnMsg = f"""
Input is too large ({len(input_text)} characters). Typically, tulp does not handle inputs
larger than 5000 characters well. Regardless, tulp will divide the input into
chunks of fewer than {max_chars} characters and attempt to process all the input.

Please be aware that the quality of the final result may vary depending on the
task. Tasks that are line-based and do not require context will work great,
while tasks that require an overall view of the document may fail miserably.

You may adjust the TULP_MAX_CHARS environment variable to control the size of
the processing chunks, which may improve the results.

"""
        if config.model != "gpt-4":
           warnMsg = warnMsg + """You can also try to force the use of the gpt-4 model (TULP_MODEL=gpt-4), which
usually improves the quality of the result.
"""
        log.warning(warnMsg)
    input_lines = input_text.splitlines()

    # try to split it in lines of less than max_size
    compressed_lines = [""]

    for iline in input_lines:
        compresed_index = len(compressed_lines) - 1
        clen = len(compressed_lines[compresed_index]) 
        if clen + len(iline) < max_chars:
            compressed_lines[compresed_index] += iline + "\n"
        else:
            if clen != 0:
                if (len(iline) < max_chars):
                    compressed_lines.append(iline + "\n")
                else:
                    for i in range(0,math.floor(len(iline)/max_chars)+1):
                        input_chunk = iline[i*max_chars:(i+1)*max_chars] 
                        compressed_lines.append(input_chunk)
                    compressed_lines[compresed_index] += "\n"

    for line in compressed_lines:
        raw_input_chunks.append(line)

    return raw_input_chunks

def run():
    log.info(f"Running tulp v{version.VERSION} using model: {config.model}")
    openai_key = config.openai_api_key
    if not openai_key:
        log.error(f'OpenAI API key not found. Please set the TULP_OPENAI_API_KEY environment variable or add it to {tulpconfig.CONFIG_FILE}')
        log.error(f"If you don't have one, please create one at: https://platform.openai.com/account/api-keys")
        sys.exit(1)


    openai.api_key = openai_key
    prev_context=None


    # Define command line arguments
    parser = argparse.ArgumentParser(description="A command line interface for the OpenAI GPT language model")
    parser.add_argument("prompt", nargs="*", help="User prompt to send to the language model", type=str)

    # Parse command line arguments
    args = parser.parse_args()

    # If input is available on stdin, read it
    if not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()
    else:
        input_text = ""

    # If prompt is provided as argument, use it to construct the input text
    if args.prompt:
        prompt = " ".join(args.prompt)

    # If prompt is not provided and no input is available on stdin, prompt the user for input
    instructions=None
    if not args.prompt and not input_text:
        input_text = input("Enter your request: ").strip()
    elif args.prompt and not input_text:
        input_text = prompt
    elif not args.prompt and input_text:
        instructions = "Summarize the input"
    elif args.prompt and input_text:
        instructions = prompt

    getInstructionMessages=None
    if instructions:
        from . import filteringPrompt
        getInstructionMessages=filteringPrompt.getMessages
    else:
        from . import requestPrompt
        getInstructionMessages=requestPrompt.getMessages


    raw_input_chunks = pre_process_raw_input(input_text)

    for i in range(0,len(raw_input_chunks)):
        if (len(raw_input_chunks) > 1):
            log.info(f"Processing {i+1} of {len(raw_input_chunks)}...")
        else:
            log.info(f"Processing...")
        finish_reason = ""
        response_text = ""
        raw_input_chunk = raw_input_chunks[i]
        if raw_input_chunk:
            request = getInstructionMessages(instructions, raw_input_chunk , len(raw_input_chunks), i+1, prev_context)
            for req in request:
                log.debug(f"REQ: {req}")
            log.debug(f"Sending the request to OpenAI...")
            response = openai.ChatCompletion.create(
                model=config.model,
                messages=request,
                temperature=0
            )
            log.debug(f"ANS: {response}")
            response_text += response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason


        blocks_dict = parse_response(response_text)

        if block_exists(blocks_dict,"(#error)"):
            log.error("Error: Couldn't process your request:")
            log.error(blocks_dict["(#error)"])
            sys.exit(1)
        else:
            valid_answer = False

            if block_exists(blocks_dict,"(#inner_message)"):
                log.debug("(#inner_message) found!")

            if block_exists(blocks_dict,"(#output)"):
                valid_answer = True
                print(cleanup_output(blocks_dict["(#output)"]))

            if block_exists(blocks_dict,"(#comment)"):
                valid_answer = True
                log.info(blocks_dict["(#comment)"])

            if block_exists(blocks_dict,"(#context)"):
                prev_context = blocks_dict["(#context)"]
            else:
                prev_context = None

            if not valid_answer:
                log.error("Unknown error while processing, try with a different request, model response:")
                log.error(response_text)
                sys.exit(2)

        if finish_reason == "length":
            errorMsg = f"""Token limit exceeded:
GPT could not finish your response, the answer depleted the chatGPT token
limit. In order to overcome this error you may try to use a smaller MAX_CHARS
(currently ={config.max_chars}), using a different model or improving your
instructions.
"""

            log.error(errorMsg)
            sys.exit(2)

if __name__ == "__main__":
    run()
