# TULP: TULP Understands Language Promptly | v2.0 

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world, now with enhanced capabilities to utilize various AI APIs including groq, ollama, anthropic, and gemini.

TULP allows you to harness the power of multiple AI models by piping standard input content directly to these models, getting the answer back on the shell.

[![tulp demo video](https://markdown-videos.deta.dev/youtube/mHAvlRXXp6I)](https://www.youtube.com/watch?v=mHAvlRXXp6I)

## Installation:

```bash
pip install tulp
```

## Usage:

TULP has 3 main operation modes:

1. **request:** Process the user request:
```bash
tulp [A written request or question]
```
2. **stdin processing:** Process or filter all the stdin input according to the user instructions, writing the processed output to stdout.
```bash
cat [MYFILE] | tulp [Processing instructions written in natural language]
```
3. **Code Interpretation:** Add a -x to any of the previous operations, and Tulp will try to **create, debug, and execute** a program that gets the request done!.
```
cat examples/titanics.csv | tulp -x how many persons survived
```


In both cases, TULP will write to the standard output the answers and will write any other information to the standard error. You can safely pipe the output to your file or next piping command and will still get all the information and errors on stderr.

It is **important** to note that if your input is larger than 5000 characters, the input will be split into multiple chunks and processed by the selected AI model in multiple requests. In this case, the result quality will really depend on the task (e.g., will work fine for translations or grammatical corrections, it will work terribly for summarizing). Anyway, **tulp works great when the input is less than 5000 chars**.

By default, tulp uses **gpt-4o**, because it is cheaper and **faster**, but for complex tasks, it is always a **good idea to specify the model**: tulp --model {model_name} {a complex task}

### Options:
```
usage: tulp [-h] [-x] [-w W] [--model MODEL] [--max-chars MAX_CHARS] [--cont CONT] [-v] [-q] [--groq_api_key GROQ_API_KEY]
            [--ollama_host OLLAMA_HOST] [--anthropic_api_key ANTHROPIC_API_KEY] [--openai_api_key OPENAI_API_KEY]
            [--openai_baseurl OPENAI_BASEURL] [--gemini_api_key GEMINI_API_KEY]
            ...

TULP Understands Language Promptly:
A command line tool, in the best essence of POSIX tooling, that will help you
to **process**, **filter**, and **create** data in this new Artificial
Intelligence world.

Tulp support different backends and models, the backend will be automatically selected for each model, currently supported models should match:

   - groq.* : Any groq model id using the prefix 'groq.', will use GROQCLOUD API and requires GROQ_API_KEY definition. Check available modules at https://console.groq.com/docs/models
   - ollama.* : Any ollama model with the prefix 'ollama', the model should be running in the ollama_host.
   - claude-.* : Any Anthropic claude model (https://docs.anthropic.com/claude/docs/models-overview), requires ANTHROPIC_API_KEY
   - gpt-.* : Any OpenAI model (https://platform.openai.com/docs/models), requires openai_api_key definition
   - gemini.* : Any Google gemini model (https://ai.google.dev/gemini-api/docs/models/gemini), requires gemini_api_key definition

positional arguments:
  request               User request, instructions written in natural language

options:
  -h, --help            show this help message and exit
  -x                    Allow tulp to create a program and execute it to fulfill the task (code interpret)
  -w W                  Write the output (or the created program for execution) to the file. If the file exists, a backup will be created before overwriting it.
  --model MODEL         Select the openai LLM model to use (default: gpt-4-turbo)
  --max-chars MAX_CHARS
                        Number of chars per message chunk per request (Default 40000)
  --cont CONT           Autmatically ask the model to continue until it finishes the answering the request up to the given times
  -v                    Be verbose!
  -q                    Be quiet! Only print the answer and errors.
  --groq_api_key GROQ_API_KEY
                        GROQ cloud API KEY
  --ollama_host OLLAMA_HOST
                        Define custom ollama host, by default it will connect to http://127.0.0.1:11434
  --anthropic_api_key ANTHROPIC_API_KEY
                        Anthropic api key
  --openai_api_key OPENAI_API_KEY
                        OpenAI cloud API KEY
  --openai_baseurl OPENAI_BASEURL
                        Use it to change the server, e.g.: use http://localhost:11434/v1/ to connect to your local ollama server
  --gemini_api_key GEMINI_API_KEY
                        gemini cloud API KEY

```

## Configuration 
The configuration file is located at ~/.tulp.conf. 

The following are the parameters that can be configured:
- **LOG_LEVEL**: The log level of Tulp. Valid options are DEBUG, INFO, WARNING, ERROR, and CRITICAL. The default value is INFO.
- **API_KEYS**: The API keys for the supported AI models (OpenAI, GROQ, Ollama, Anthropic, Gemini). The default value is an empty string for each.
- **MAX_CHARS**: The maximum number of characters processed in one chunk. The default value is 40000.
- **MODEL**: The AI model to be used by Tulp. The default value is gpt-4o but other models are also available.

All these settings could be overridden by an environment variable using the prefix TULP\_ or by the different command line arguments described above. 
As environment variables, they will become: TULP_LOG_LEVEL, TULP_API_KEYS, TULP_MAX_CHARS, or TULP_MODEL.
Command line arguments will override environmental variables and the configuration file.


Here is an example configuration file with the default values:
```INI
[DEFAULT]
LOG_LEVEL = INFO
${MODEL}_API_KEYS = <<<YOUR API KEYS FOR GROQ, OLLAMA, ANTHROPIC, OPENAI, GEMINI>>>
MAX_CHARS = 40000
MODEL = gpt-4o
```


## Examples:
The usage is endless, but anyway, here you have some ideas as inspiration:

### Random
#### The meaning of life for different models:

```
+ tulp -q --model gpt-4-turbo tell me the meaning of life in just 3 words
42, not known


+ tulp -q --model gpt-3.5-turbo tell me the meaning of life in just 3 words
Live, love, learn.

+ tulp -q --model claude-3-opus-20240229 tell me the meaning of life in just 3 words
Love conquers all.

+ tulp -q --model gemini-1.5-pro-latest tell me the meaning of life in just 3 words
The answer is 42.

+ tulp -q --model groq.gemma-7b-it tell me the meaning of life in just 3 words
The meaning of life is to find purpose and fulfillment in the present moment.


+ tulp -q --model groq.llama3-70b-8192 tell me the meaning of life in just 3 words
Find Your Purpose

+ tulp -q --model groq.mixtral-8x7b-32768 tell me the meaning of life in just 3 words
Impossible task.

+ tulp -q --model ollama.phi3:instruct tell me the meaning of life in just 3 words
echo "Meaning of Life"
```

#### Create a plot directly from raw memory output printed by gdb:
Command:
```bash
cat <<EOF | tulp convert this to a python list of 2 element tuples |  tulp write a python function to scatter plot these points using matplotlib | python 
(gdb) p *polygon._points._M_ptr._M_impl._M_start@4
$21 = {{x = 0.441429973, y = -0.176619753}, {x = 0.476210177, y = -0.104575738}, {x = 0.674865067, y = -0.0814191923}, {x = 0.640084863, y = -0.199776307}}
EOF
```

Result:

![matplotlib @rela](./examples/rela_plot.png)

### Grammatical and Syntax Correction of Clipboard Content in Linux (The Corrected Version Will Be in the Clipboard)

```bash
xsel -b | tulp fix my english | xsel -b
```


### Typical Unix tooling replacement:
#### Sed
```bash
cat README.md | tulp replace all the occurrences of TULP for **TULP**
```
#### Awk
```bash
cat README.md | tulp print the second word of each line
```
#### grep, but advanced
```bash
cat tulp.py | tulp print the name of the functions and also the return line 
```

### Grammatical and syntax corrections:
```bash
cat README.md | tulp fix all the typos, syntax and grammatical errors > README.fix.md
```

Or even better:
```bash
cat README.md | TULP_MAX_CHARS=10000 TULP_MODEL=gpt-4 tulp fix all the typos, syntax and grammatical errors > README.fix.md
```

### Translations
```bash
cat README.md | tulp translate to Spanish > README.es.md
```
### Data filtering from formatted input
#### csv
```bash

cat list.csv | tulp print only the second column
Count
3
1
2
```

### csv

```bash
cat persons.json | tulp 'list the names and ages of each person in a csv table, using ; as separator'
```
### Data creation and extraction from unstructured data (a story of oranges and friends):
```bash
fede@liebre:~/repos/tulp$ tulp write a poem that names 3 persons \(given each a name\) and list how they shared 10 oranges | tee examples/oranges_poem.txt
Roses are red,
Violets are blue,
Here's a poem,
About sharing oranges too.

There were three friends,
Whose names were Ann, Ben, and Sue,
They had 10 oranges,
And didn't know what to do.

Ann suggested they split them,
Equally, three each,
But Ben said that wasn't fair,
As Sue was too weak.

So they decided to give Sue,
An extra orange or two,
And split the rest evenly,
So everyone had a fair view.

And that's how Ann, Ben, and Sue,
Shared their 10 oranges,
With kindness and fairness,
And no one had any grudges.

fede@liebre:~/repos/tulp$ cat examples/oranges_poem.txt | python3 ./tulp.py write a list of persons and the number of oranges that they have as csv
Ann,3
Ben,3
Sue,4
```

# Origin of the name
I used `tulp.py` to create "TULP". In some way, everything is recursive in "TULP", so it makes sense to use a recursive acronym.

Therefore, after several iterations with `tulp.py`, "TULP" and I decided that the best name would be "TULP", and this is how we decided what "TULP" stands for:
```bash
fede@liebre:~/repos/openai/tulp$ python3 ./tulp.py "TULP is a recursive acronym naming an opensource posix tool that processes stdin input according to natural language instructions, processing the input by instructing an artificial intelligence. Write some options of what TULP could stand for as recursive acronym"
TULP could stand for:
- TULP Understands Language Perfectly
- TULP Uses Language to Process
- TULP Understands Language Promptly
- TULP Utilizes Language for Processing
- TULP Unravels Language Precisely
```

# Why?

I am a heavy user of Unix tooling (e.g: awk, jq, sed, grep, and so on), I have been using them since my early days and I used to think that I couldn't survive without them. But then, ChatGPT appeared, and I started to use more and more GPT for things that I used to use Unix tooling for. Somehow I feel the pain of cut & paste, and I was missing a way to do it faster and from within the terminal itself, so I came up with `tulp`.

# Changelog
## v2.5 | 2024-07-27
- Fixes the --cont issue.
- Adds Gemini API dependencies.
- Increases the default maximum characters.


## v2.3 | 2024-05-19
- Adds -cont option to allow tulp to automatically request the LLM to continue if an incomplete response is found.
- Adds automatic handling of RECITATION for Gemini LLM.


## v2.2 | 2024-05-14
- Fixes code execution (-x option)

## v2.1 | 2024-05-14
- Improves formating of messages for gemini
- Changed to use gpt-4o model by default

## v2.0 | 2024-05-04
- Added support for groq, ollama, anthropic, and gemini AI models.
- Changed to use gpt-4-turbo model by default

## v1.0 | 2024-02-14
- Changed to use gpt-4-0125-preview model by default
- Updated to use openapi v1.0
- Changes default max-chars to 40000

## v0.7  | 2023-05-23 
- Adds Code Interpretation, -x option
## v0.6 | 2023-05-11
- Adds all the settings as command line arguments


