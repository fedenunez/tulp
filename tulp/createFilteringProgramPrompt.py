from . import tulplogger
from . import version

log = tulplogger.Logger()

def getMessages(user_instructions, raw_input, nof_chunks=None, next_chunk=None, context=None):
    log.debug(f"getPromptForFiltering:  nof_chunks:{nof_chunks} ; next_chunk:{next_chunk}, context: {context}")
    request_messages = []

    chunk_rules = ""
    if ( nof_chunks and nof_chunks > 1):
        chunk_rules = "\n- The raw_input will be chunked in multiple parts, you must process one chuck at a time, assume that when you process a raw_input it is a chunk and all the previous chunks were already processed and the (#output) for them is already created, the (#output) that you create for the current raw_input will be concatenated to the previous (#output), you must also asume that the raw_input format is a valid continuation from the previous chunks."


    system_instructions = """# You are a Unix cli tool named tulp created by fedenunez:
- Your version is """ + version.VERSION  + """
"""
    request_messages.append({"role": "system", "content": system_instructions})
    user_system_instructions = f"""# Rules
- Your response should be split into blocks, valid blocks are: (#inner_messages),(#output), (#comment); the (#output) is mandatory.
- Your task is to write a python code (into the (#output) block) that process the standard input to fullfil my request.
- Writing the code in the (#output) block:
  - Start the program with an inline comment with the overall description of the program
  - then write all the needed import, verify that all are included!
  - the write the code that reads the standard input
  - continue writing the program step by step, you must add inline comments to make it more understandable
  - verify at every step that you made the needed import before using any module

# Response template:
{""}(#output)
<write the output program in python. This block is mandatory>
{""}(#comment)
<An overall description of what you wrote on (#output) and how you created. Any extra explanation, comment, or reflection you may have regarding the generated (#output). Do not ever make a reference like "This..." or "The above..." to refer to the created output. Remember to mention any external module that the user should install using pip install ... >

# Processing instructions:
You must create a python program that will take a file from the standard input and process it so it can fullfil this request:
{user_instructions}

I will write an example input file, that is a cropped version of a real file, use it as a reference of the input file format.
"""
    request_messages.append({"role": "user","content": user_system_instructions})
    request_messages.append({"role": "user", "content": f"""# example input:
{raw_input}"""})
    return request_messages

