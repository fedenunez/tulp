#!/usr/bin/python3

import sys
import os
import re
import math
from . import tulpargs
from . import tulplogger
from . import tulpconfig
from . import version
from . import TulpOutputFileWriter
from . import promptSerializer


log = tulplogger.Logger()
config = tulpconfig.TulipConfig()
args = tulpargs.TulpArgs().get()
llmclient: object  # will be defined in main
inspectFolder = None

# Helper functions

## cleanup_output: clenaup output, removing artifacts
def cleanup_output(output):
    olines = output.strip().splitlines()

    # Remove all white lines at the start or end of olines
    while olines and len(olines) > 1 and  not olines[0].strip():
        olines.pop(0)
    while olines and len(olines) > 1 and not olines[-1].strip():
        olines.pop()

    blockRe = re.compile(r'^```',re.MULTILINE)
    # gpt-3.5 usually adds unneeded markdown codeblock wrappers, try to remove them
    if len(blockRe.findall(output)) == 2 and len(olines) > 2:
        if olines[0].startswith("```") and olines[-1] == "```":
            log.info("markdown codeblock wrapping detected and stripped!")
            return "\n".join(olines[1:-1])
    return output


## block_exists(blocks_dict, key):  test if a KEY exist and is not empty
def block_exists(blocks_dict, key):
    return key in blocks_dict

def block_isnotempty(blocks_dict, key):
    return key in blocks_dict and len(blocks_dict[key]["content"].strip()) > 0


## VALID_BLOCKS: define the valid answer blocks  blocks
END_FLAG="(#end)"
VALID_BLOCKS=["(#stdout)","(#thoughts)","(#inner_message)","(#error)","(#context)","(#stderr)",END_FLAG]
## parse_response)response_text): parse a gpt response, returning a dict with each response section 
def parse_response(response_text):
    blocks_dict={}
    lines = response_text.strip().splitlines()

    # Remove any empty lines at the end
    while lines and len(lines) and not lines[-1].strip():
        lines.pop()

    # Find end tag
    if len(lines) > 1:
        lastLine = lines[-1]
        if lastLine.endswith(END_FLAG):
            lines[-1] = lastLine[:-len(END_FLAG)]
            blocks_dict[END_FLAG] = {}


    # parse blocks:
    parsingBlock=None
    for line in lines:
        splitted_line = line.split(" ")
        key = None
        if (len(splitted_line) >= 1):
            key = splitted_line[0]
            if (len(splitted_line) > 2):
                outputType = " ".join(splitted_line[1:])
            else:
                outputType = None
        if (key in VALID_BLOCKS):
            parsingBlock=key
            if parsingBlock not in blocks_dict:
               blocks_dict[parsingBlock]={}
               blocks_dict[parsingBlock]["type"]=outputType
               blocks_dict[parsingBlock]["content"] = ""


        else:
            if parsingBlock:
                blocks_dict[parsingBlock]["content"] += line + "\n"
            else:
                if config.model == "gpt-3.5-turbo": 
                    log.error("""
Unknown error while processing: this is usually related to gpt not honoring our
output format, please try again and try to be more specific, you can also try
with a different model (e.g., TULP_MODEL=gpt-4 tulp ...)""")
                else:
                    log.error("""
Unknown error while processing: this is usually related to llm not honoring
our output format, please try again and try to be more specific in your
request. You can also try to enable DEBUG log to inspect the raw answer (e.g.,
TULP_LOG_LEVEL=DEBUG tulp ...)""") 
                log.debug(f"ERROR: Invalid answer format: =====\n {response_text} \n=====")
                sys.exit(2)
    return blocks_dict


## pre_process_stdin(input_text):  split all the input and create the stdin_chunks with chunks of text ready to be send 
def pre_process_stdin(input_text):
    stdin_chunks=[]
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

    # try to split it in lines of less than max_size
    compressed_lines = [""]

    input_lines = input_text.splitlines()

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
        stdin_chunks.append(line)

    return stdin_chunks


def processExecutionRequest(promptFactory, user_request, stdin_chunks=None):
    retries = 0
    max_retries = 5
    if (not stdin_chunks):
        stdin_chunks = [""]
    requestMessages = promptFactory.getMessages(user_request, stdin_chunks[0], len(stdin_chunks))
    while retries < max_retries:
        for req in requestMessages:
            log.debug(f"REQ: {req}")
        log.debug(f"Sending the request to model...")
        response = llmclient.generate(requestMessages)
        log.debug(f"ANS: {response}")
        response_text = response["content"]
        finish_reason = response["finish_reason"]
        blocks_dict = parse_response(response_text)
        if block_exists(blocks_dict,END_FLAG):
            log.info("End found as expected!")
        if block_isnotempty(blocks_dict,"(#stderr)"):
            log.info(blocks_dict["(#stderr)"]["content"])
        if block_isnotempty(blocks_dict,"(#stdout)"):
            oType = ""
            generatedCode = cleanup_output(blocks_dict["(#stdout)"]["content"])
            log.debug(f"The generated code:\n{generatedCode}")
            from . import executePython
            input_text="".join(stdin_chunks)
            if args.w:
                ok, filename = TulpOutputFileWriter.TulpOutputFileWriter().write_to_file(args.w, generatedCode)
                if ok: 
                    log.info(f"Wrote created program at: {filename}")
                else:
                    log.error(f"Error while writing created code: {filename}")
            log.info(f"Executing generated code...")
            boutput, berror, ecode  = executePython.execute_python_code(generatedCode, input_text)
            log.debug(f"Execution results: {boutput}, {berror}, {ecode}")
            if (ecode != 0 and berror.find("Traceback") != -1 ):
                retries += 1
                log.warning(f"Error while executing the code, I will try to fix it!")
                requestMessages = promptFactory.getMessages(user_request, stdin_chunks[0], len(stdin_chunks))
                rMsg = { "role": response["role"], "content": response["content"] }
                requestMessages.append(rMsg)
                requestMessages.append({"role": "user","content": f"The execution of the program failed with error:\n{berror}\n\nPlease try to write a new (#stdout) that fixes the error"})
            else:
                break;
    if retries == max_retries:
        log.error("while executing generated code, max retries reached, giving up.")
    else:
        if (ecode != 0):
            log.error(f"Error executing the program:\n{berror}")
        else:
            log.info("Code was executed correctly.")

    print(boutput)
    return ecode

def processRequest(promptFactory,user_request, stdin_chunks=None):
    if not stdin_chunks:
        stdin_chunks = [""] 
    for i in range(0,len(stdin_chunks)):
        if (len(stdin_chunks) > 1):
            log.info(f"Processing {i+1} of {len(stdin_chunks)}...")
        else:
            log.info(f"Processing...")
        finish_reason = ""
        response_text = ""
        stdin_chunk = stdin_chunks[i]
        if user_request:
            requestMessages = promptFactory.getMessages(user_request, stdin_chunk , len(stdin_chunks), i+1)
            for req in requestMessages:
                log.debug(f"REQ: {req}")
            log.debug(f"Sending the request to llm...")
            response = llmclient.generate(requestMessages)
            log.debug(f"ANS: {response}")
            response_text += response["content"]
            finish_reason = response["finish_reason"]

            # Strip (#stdout) if present, some models are adding the output
            # block at the start of the continuation assuming that it is always
            # opened in this case and removing it before appending the response
            def strip_output_block(text):
                text_stripped = text.lstrip()
                if text_stripped.startswith("(#stdout)\n"):
                    return text_stripped[len("(#stdout)\n"):]
                elif text_stripped.startswith("(#stdout)"):
                    return text_stripped[len("(#stdout)"):]
                return text

            if (inspectFolder):
                p = promptSerializer.RequestMessageSerializer(f"{inspectFolder}/{0}.json")
                p.save(requestMessages, response)
              
            continue_counter = args.cont
            # Check if continuation is needed
            while continue_counter and continue_counter > 0 and not block_exists(parse_response(response_text), END_FLAG):
                log.info(f"Continuation needed, continuation {args.cont - continue_counter} of a maximum of {args.cont}")
                continue_counter -= 1
                requestMessages.append({"role": "assistant", "content": response["content"]})
                requestMessages.append({"role": "user", "content": "Continue from your last character. Remember to finish using (#end) when you are done and to maintain the answering format."})

                response = llmclient.generate(requestMessages)

                if (inspectFolder):
                    p = promptSerializer.RequestMessageSerializer(f"{inspectFolder}/{args.cont - continue_counter}.json")
                    p.save(requestMessages, response)

                response_text += strip_output_block(response["content"])
                finish_reason = response["finish_reason"]


        blocks_dict = parse_response(response_text)

        if block_isnotempty(blocks_dict,"(#error)"):
            log.error("Error: Couldn't process your request:")
            log.error(blocks_dict["(#error)"]["content"])
            sys.exit(1)
        else:
            valid_answer = False

            if not block_exists(blocks_dict,END_FLAG):
                if args.cont and args.cont > 0 and continue_counter == 0:
                    log.error("It looks like {args.cont} was not enough to fulfill your request, we consumed all continuation tries but the LLM didn't finish answering...")
                elif not args.cont:
                    log.error("If the LLM didn't finish answering, manually check if the answer is complete, try adding a --cont argument so tulp can ask the LLM to continue.")
                else:
                    log.warning("If the LLM didn't finish answering, manually check if the answer is complete, if not you may try adding a --cont argument so tulp can ask the LLM to continue.")

            if block_isnotempty(blocks_dict,"(#inner_message)"):
                log.debug("(#inner_message) found!")

            if block_isnotempty(blocks_dict,"(#stdout)"):
                valid_answer = True
                oType = ""
                if blocks_dict["(#stdout)"]["type"]:
                    oType = f'(type: {blocks_dict["(#stdout)"]["type"]})'
                log.info(f"Writting generated output {oType}") 
                print(cleanup_output(blocks_dict["(#stdout)"]["content"]))

            if block_isnotempty(blocks_dict,"(#stderr)"):
                valid_answer = True
                log.info(blocks_dict["(#stderr)"]["content"])

            if block_isnotempty(blocks_dict,"(#context)"):
                prev_context = blocks_dict["(#context)"]
            else:
                prev_context = None

            if not valid_answer:
                log.error("Unknown error while processing, try with a different request, model response:")
                log.error(response_text)
                sys.exit(2)

        if finish_reason == "length":
            errorMsg = f"""Token limit exceeded:
LLM could not finish your response, the answer depleted the token limit. In
order to overcome this error you may try to use a smaller MAX_CHARS (currently
={config.max_chars}), using a different model or improving your instructions.
"""
            log.error(errorMsg)
            sys.exit(2)

def run():
    log.debug(f"Running tulp v{version.VERSION} using model: {config.model}")

    global llmclient
    from . import llms
    llmclient = llms.getModelClient(config.model,config)

    # If input is available on stdin, read it
    input_text = ""
    if not sys.stdin.isatty():
        input_text = sys.stdin.buffer.read().decode('ascii', errors='ignore').strip()

    user_request=None
    if 'continue_file' in args and args.continue_file:
        log.info(f"continue from file: {args.continue_file}")
    elif not args.request and not input_text:
        user_request = input("Enter your request: ").strip()
    elif args.request and not input_text:
        user_request = args.request
    elif not args.request and input_text:
        user_request = "Summarize the input"
    elif args.request and input_text:
        user_request = args.request

    if input_text:
        stdin_chunks = pre_process_stdin(input_text)


    if args.inspect_dir:
        import os
        import time
        # Create the inspect_dir folder if it doesn't exist
        os.makedirs(args.inspect_dir, exist_ok=True)
    
        # Compute the current Unix timestamp
        timestamp = int(time.time())
        
        # Create the folder inspect_dir/timestamp
        inspect_folder_path = os.path.join(args.inspect_dir, str(timestamp))
        os.makedirs(inspect_folder_path, exist_ok=True)
        
        # Define a global variable inspectFolder with the created path
        global inspectFolder
        inspectFolder = inspect_folder_path
        log.info(f"Will write all the interaction at {inspect_folder_path}")



    if input_text and user_request:
        # A filtering request:
        if (args.x):
            from . import createFilteringProgramPrompt
            sys.exit(processExecutionRequest(createFilteringProgramPrompt, user_request, stdin_chunks))
        else:
            from . import filteringPrompt
            sys.exit(processRequest(filteringPrompt, user_request, stdin_chunks))
    elif 'continue_file' in args and args.continue_file:
        ps = promptSerializer.RequestMessageSerializer(args.continue_file)
        if (args.x):
            sys.exit(processExecutionRequest(ps.getPromptFactory(), True))
        else:
            from . import requestPrompt
            sys.exit(processRequest(ps.getPromptFactory(), True))
    else:
        # A request
        if (args.x):
            from . import createProgramPrompt
            sys.exit(processExecutionRequest(createProgramPrompt, user_request))
        else:
            from . import requestPrompt
            sys.exit(processRequest(requestPrompt, user_request))



if __name__ == "__main__":
    run()
