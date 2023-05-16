from . import tulplogger
from . import version

log = tulplogger.Logger()

def getMessages(user_instructions, raw_input, nof_chunks=None, next_chunk=None, context=None):
    request_messages = []
    user_system_instructions = f"""# Rules
- Your response should be split into blocks, valid blocks are: (#inner_messages), (#output), (#comment); the (#output) is mandatory.
- Your task is to write a python program (into the (#output) block), 
- Writing the code in the (#output) block:
  - Start the program with an inline comment with the overall description of the software design
  - then write all the needed import, verify that all are included!
  - continue writing the program step by step, adding inline comments for each step to make it more understandable
  - verify at every step that you made the needed import before using any module

# Response template:
{""}(#output)
<write the output program in python. This block is mandatory.>
{""}(#comment)
<An overall description of the wrote code, any extra explanation, comment, or reflection you may have regarding the generated (#output). Do not ever make a reference like "This..." or "The above..." to refer to the created output. Remember to mention any external module that the user should install using pip install ... >

# Code functionality:
{user_instructions}

"""
    request_messages.append({"role": "user","content": user_system_instructions})
    return request_messages

