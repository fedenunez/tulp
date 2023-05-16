from . import tulplogger
from . import version

log = tulplogger.Logger()

def getMessages(user_instructions, raw_input, nof_chunks=None, next_chunk=None, context=None):
    log.debug(f"getPromptForFiltering:  nof_chunks:{nof_chunks} ; next_chunk:{next_chunk}, context: {context}")
    request_messages = []

    user_system_instructions = f"""# Rules
- Your response should be split into blocks, valid blocks are: (#inner_messages), (#output), (#comment); the (#output) is mandatory.
- Your task is to write a python program (into the (#output) block), 
- Writing the code in the (#output) block:
  - Start the program with an inline comment with the overall description of the software design
  - then write all the needed import, verify that all are included!
  - if the request is to process or filter the input, now add the code that will load the input into the buffer.
  - continue writing the program step by step, adding inline comments for each step to make it more understandable
  - verify at every step that you made the needed import before using any module

# Response template:
{""}(#output)
<write the output program in python. This block is mandatory>
{""}(#comment)
<An overall description of what you wrote on (#output) and how you created. Any extra explanation, comment, or reflection you may have regarding the generated (#output). Do not ever make a reference like "This..." or "The above..." to refer to the created output. Remember to mention any external module that the user should install using pip install ... >

# Request:
You must create a python program that fulfil:
{user_instructions}

"""
    if len(raw_input) > 1:
        user_system_instructions += "I will write the first chunk of the input file, It is a cropped version of a real file, The created program will get the full file at the input."
    request_messages.append({"role": "user","content": user_system_instructions})
    request_messages.append({"role": "user", "content": f"""# input:
{raw_input}"""})
    return request_messages

