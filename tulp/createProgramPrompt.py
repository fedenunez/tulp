from . import tulplogger
from . import version

log = tulplogger.Logger()

def getMessages(user_instructions, stdin, nof_chunks=None, next_chunk=None, context=None):
    request_messages = []
    user_system_instructions = f"""# Rules
- Your response should be split into blocks, valid blocks are: <|cli_inner_messages|>, <|cli_stdout|>, <|cli_stderr|>; the <|cli_stdout|> is mandatory.
- If you are continuing a response you started in the previous message, just continue from where you left off, without reopening the already opened block.
- You must finish your response with the end tag: <|cli_end|>
- Your task is to write a python program (into the <|cli_stdout|> block), 
- Writing the code in the <|cli_stdout|> block:
  - Start the program with an inline comment with the overall description of the software design
  - then write all the needed import, verify that all are included!
  - continue writing the program step by step, adding inline comments for each step to make it more understandable
  - verify at every step that you made the needed import before using any module

# Response template:
{""}<|cli_stdout|>
<write the output program in python. This block is mandatory.>
{""}<|cli_stderr|>
<An overall description of the wrote code, any extra explanation, comment, or reflection you may have regarding the generated <|cli_stdout|>. Do not ever make a reference like "This..." or "The above..." to refer to the created output. Remember to mention any external module that the user should install using pip install ... >

# Code functionality:
{user_instructions}
<|cli_end|>
"""
    request_messages.append({"role": "user","content": user_system_instructions})
    return request_messages

