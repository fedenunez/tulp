#!/usr/bin/python3
import openai
import argparse
import sys
import os
import math
import tuliplogger


def run():
    log = tuliplogger.Logger()

    def get_openai_key():
        key = os.environ.get('OPENAI_API_KEY')
        if key:
            return key.strip()
        try:
            with open(os.path.expanduser('~/.gptcli.conf')) as f:
                return f.readline().strip()
        except:
            return None

    openai_key = get_openai_key()
    if not openai_key:
        print('OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or add it to ~/.gptcli.conf')
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
        import filteringPrompt
        instructionFunction=filteringPrompt.getBaseMessages
    else:
        import requestPrompt
        instructionFunction=requestPrompt.getBaseMessages

    user_messages=[]
    # Split input text into chunks to fit within max token window
    max_tokens = 1570  # Maximum number of tokens the GPT model can handle at once
    if len(input_text) > max_tokens:
        log.warning(f"Warning: input is to big, we will split processing in chunks of less than {max_tokens}")
    input_lines = input_text.splitlines()
    # try to split it in lines or max_size
    compressed_lines = [""]

    for iline in input_lines:
        compresed_index = len(compressed_lines) - 1
        clen = len(compressed_lines[compresed_index]) 
        if clen + len(iline) < max_tokens:
            compressed_lines[compresed_index] += iline + "\n"
        else:
            if clen != 0:
                if (len(iline) < max_tokens):
                    compressed_lines.append(iline + "\n")
                else:
                    for i in range(0,math.floor(iline)/max_tokens+1):
                        input_chunk = iline[i*max_tokens:(i+1)*max_tokens] 
                        compressed_lines.append(input_chunk)
                    compressed_lines[compresed_index] += "\n"

    for line in compressed_lines:
         user_messages.append( {"role": "user", "content": line})



    for i in range(0,len(user_messages)):
        log.info(f"PROCESSING {i+1} of {len(user_messages)}:")
        response_text = ""
        message = user_messages[i]
        if message:
            request = instructionFunction(instructions, len(user_messages), i+1, prev_context)
            if True:
                request.append(message)
                response = openai.ChatCompletion.create(
                    #model="gpt-4", 
                    model="gpt-3.5-turbo",
                    messages=request,
                    #max_tokens=max_tokens,
                    temperature=0
                )
                for req in request:
                    log.debug(f"REQ: {req}")
                log.debug(f"ANS: {response}")
                response_text += response.choices[0].message.content
            else:
                response_text += f"(#output)\nsimulated request"



        lines = response_text.splitlines()
        valid_blocks=["(#output)","(#error)","(#context)"]
        blocks_dict={}

        # parse blocks:
        parsingBlock=None
        for line in lines:
            if (line in valid_blocks):
                parsingBlock=line
                blocks_dict[parsingBlock]=""

            else:
                if parsingBlock:
                    blocks_dict[parsingBlock] += line + "\n"
                else:
                    log.error(f"Unknown error while processing: output before quotes?, try a different input: {line} - {parsingBlock}")
                    log.error(response_text)
                    sys.exit(2)


        if "(#error)" in blocks_dict:
            log.error("Error: Couldn't process your request:")
            log.error(blocks_dict["(#error)"])
            sys.exit(1)
        elif "(#output)" in blocks_dict:
            print(blocks_dict["(#output)"])
            if "(#context)" in blocks_dict:
                prev_context = blocks_dict["(#context)"]
            else:
                prev_context = None
        else:
            log.error("Unknown error while processing, try with a different request, model response:")
            log.error(response_text)
            sys.exit(2)

if __name__ == "__main__":
    run()
