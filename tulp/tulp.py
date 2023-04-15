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

# gpt-3.5 usually adds unneeded markdown codeblock wrappers, try to remove them
def cleanup_output(output):
    olines = output.splitlines()
    if len(olines) > 2:
        if olines[0].startswith("```") and olines[-1] == "```":
            log.debug("markdown codeblock wrapping detected and stripped!")
            return "\n".join(olines[1:-1])
    return output




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

    instructionFunction=None
    if instructions:
        from . import filteringPrompt
        instructionFunction=filteringPrompt.getBaseMessages
    else:
        from . import requestPrompt
        instructionFunction=requestPrompt.getBaseMessages

    user_messages=[]
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
         user_messages.append( {"role": "user", "content": line})

    for i in range(0,len(user_messages)):
        if (len(user_messages) > 1):
            log.info(f"Processing {i+1} of {len(user_messages)}...")
        else:
            log.info(f"Processing...")
        response_text = ""
        message = user_messages[i]
        if message:
            request = instructionFunction(instructions, len(user_messages), i+1, prev_context)
            request.append(message)
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

        lines = response_text.splitlines()
        # (#end) is not specified by us, but sometimes gpt-3.5 wrote it so we just parse it so we can keep it out
        valid_blocks=["(#output)","(#error)","(#context)","(#comment)","(#end)"]
        blocks_dict={}

        # parse blocks:
        parsingBlock=None
        for line in lines:
            if (line in valid_blocks):
                parsingBlock=line
                if parsingBlock not in blocks_dict:
                   blocks_dict[parsingBlock]=""

            else:
                if parsingBlock:
                    blocks_dict[parsingBlock] += line + "\n"
                else:
                    if config.model == "gpt-3.5-turbo": 
                        log.error("Unknown error while processing: this is usually related to gpt not honoring our output format, please try again or try with a different model (TULP_MODEL=gpt-4 maybe?)")
                        log.debug(f"ERROR: Invalid answer format: =====\n {response_text} \n=====")
                    else:
                        log.error("Unknown error while processing: this is usually related to gpt not honoring our output format, please try again or use TULP_LOG_LEVEL=DEBUG to inspect the raw answer")
                        log.debug(f"ERROR: Invalid answer format: =====\n {response_text} \n=====")
                    sys.exit(2)

        if "(#error)" in blocks_dict:
            log.error("Error: Couldn't process your request:")
            log.error(blocks_dict["(#error)"])
            sys.exit(1)
        else:
            valid_answer = False
            if "(#output)" in blocks_dict:
                valid_answer = True
                print(cleanup_output(blocks_dict["(#output)"]))
            if "(#comment)" in blocks_dict:
                valid_answer = True
                log.info(blocks_dict["(#comment)"])
            if "(#context)" in blocks_dict:
                prev_context = blocks_dict["(#context)"]
            else:
                prev_context = None
            if not valid_answer:
                log.error("Unknown error while processing, try with a different request, model response:")
                log.error(response_text)
                sys.exit(2)

if __name__ == "__main__":
    run()
