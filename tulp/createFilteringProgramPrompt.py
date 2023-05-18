from . import tulplogger
from . import version

log = tulplogger.Logger()

def getMessages(user_instructions, raw_input, nof_chunks=None, next_chunk=None, context=None):
    log.debug(f"getPromptForFiltering:  nof_chunks:{nof_chunks} ; next_chunk:{next_chunk}, context: {context}")
    request_messages = []

    user_system_instructions = f"""# Rules
- Your response should be split into blocks, valid blocks are: (#inner_messages), (#thoughts), (#output), (#comment); the (#output) is mandatory.
- Your task is to write a python program
- Writing the code in the (#output) block:
  - Start the program with an inline comment with the description of the code that you will write.
  - then write all the needed import, verify that all are included!
  - if and input file is needed: write the code that reads the stdin into a input buffer to be processed
  - continue writing the program step by step
  - add inline comments before each important code section explaining the functionality and rational behind it
  - verify at every step that you made the needed import before using any module

# Response template:
{""}(#output)
<write the output program in python. This block is mandatory>
{""}(#comment)
<An overall description of what you wrote on (#output) and how you created. Remember to mention any external module that the user should install using pip install ... >

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

