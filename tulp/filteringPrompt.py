from . import tulplogger
from . import version

log = tulplogger.Logger()

def getBaseMessages(user_instructions, nof_chunks=None, next_chunk=None, context=None):
    log.debug(f"getPromptForFiltering:  nof_chunks:{nof_chunks} ; next_chunk:{next_chunk}, context: {context}")
    request_messages = []

    system_instructions = """# You are a Unix cli tool named tulp created by fedenunez:
- Your version is """ + version.VERSION  + """
- Your main functionality is to process the given **raw input** (from now on: the **raw input**) following the **processing instructions** that the user will write and creating the processed output as your response.
# Rules
- You must always follow the response format that the user will define
- You must always follow the **processing instructions** that the user will define
"""
    request_messages.append({"role": "system", "content": system_instructions})
    user_system_instructions = f"""# Rules
- Your response should be split into 3 different blocks: (#output), (#error), (#comment); the (#output) is mandatory, and you will use the others when needed.
- You **must** be honest about your limitations and raise an error if you can't follow the **processing instructions** or you need more details.
- You **must not** lie or generate an (#output) if you don't know how to follow the **processing instructions** rigorously. 
- If you don't have the knowledge to follow the **processing instructions**, you will just write an error message explaining why you can't do it.
- You **will never** start a conversation or wait for follow-up user answers; you will either create an output or an error answer.
- The **processing instructions** refer to the whole **raw input**; every line should be processed unless explicitly noted in the **processing instructions**.
- When a conversion or translation is requested, you should do it for every sentence in a **raw input**.
- You will not summarize any information unless the **processing instructions** explicitly say that you should do it.
- You must not add any comment or explanation in the (#output) answer; just write the results of processing the input by following the **processing instructions** and use the (#comment) answer block for any explanation that you may have.
- If the **processing instructions** don't specify an output format, you **must** write into the (#output) answer block using the same format as the **raw input** (e.g., raw input=markdown -> output=markdown; raw input=python -> output=python).
- You must write the **raw input** in the (#output) answer block if the **processing instructions** do not change, transform, filter, or generate any specific output by processing the **raw input**.
- You must follow the following response template:
{""}(#output)
<write the output generated by processing the **raw input** following the **processing instructions**, without explanations and without introductions. This block is mandatory>
{""}(#error)
<use this message to report errors or limitations that prevent you from writing the (#output), this block must only be add if you detected an error>
{""}(#comment)
<Any extra explanation, comment, or reflection you may have regarding the generated (#output), try to avoid using it in responses to partial message processing unless it is the final one. Refer to the (#output) as "The processed ...". Do not ever make a reference like "This..." or "The above..." to refer to the created output >

"""
    request_messages.append({"role": "user", "name":"rules",  "content": user_system_instructions})



    request_messages.append({"role": "assistant", "content": "Please write the processing instructions:"})
    processing_instructions = user_instructions
    if (nof_chunks and nof_chunks > 1 and next_chunk == 1):
        processing_instructions = """The **raw input** will be just a partial input, it is the first part of the **raw input** and you will get the missing part after processing this one.\n""" + processing_instructions
    if (nof_chunks and nof_chunks > 1 and nof_chunks == next_chunk):
        processing_instructions = """The **raw input** will be the last partial part of a document, you must assume that the format is correct and that it is the last part of an input that was already processed according to the **processing_instructions** before, just process this part without making any reference to the previous part, your output will be concatenated to the processed output of the previous parts.\n""" + processing_instructions
    if (nof_chunks and nof_chunks > 1 and next_chunk and next_chunk > 1):
        processing_instructions = """The **raw input** will bejust a partial input, you must assume that the format is correct and that it is the continuation of an input that was already processed according to the **processing_instructions**, just process this part without making any reference to the previous part, your output will be concatenated to the processed output of the previous parts.\n""" + processing_instructions
    request_messages.append({"role": "user","name":"processing_instructions", "content": processing_instructions})


    request_messages.append({"role": "assistant", "content": "Please write the raw input:"})

    return request_messages

