# TULP: TULP Understands Language Promptly 

TULP is a command-line tool inspired by POSIX utilities, designed to help you **process**, **filter**, and **create** data in the realm of Artificial Intelligence. It now includes enhanced capabilities to utilize various AI APIs, such as groq, ollama, anthropic, and gemini.

With TULP, you can leverage the power of multiple AI models by piping standard input content directly to these models and receiving the output in your shell.

[![Watch the TULP demo video](https://markdown-videos.deta.dev/youtube/mHAvlRXXp6I)](https://www.youtube.com/watch?v=mHAvlRXXp6I)

## Installation

To install TULP, run:
```bash
pip install tulp
```
To keep it up to date, use:
```bash
pip install --upgrade tulp
```

**Note:** If you encounter issues with google-generativeai dependencies during installation, try upgrading pip:
```bash
pip install --upgrade pip
```

## Usage

TULP offers three main operation modes:

1. **Request Mode:** Process a user request.
   ```bash
   tulp [Your request or question]
   ```

2. **Stdin Processing Mode:** Process or filter all stdin input based on user instructions, outputting the processed data to stdout.
   ```bash
   cat [MYFILE] | tulp [Processing instructions in natural language]
   ```

3. **Code Interpretation Mode:** Add `-x` to any of the previous operations, and TULP will attempt to **create, debug, and execute** a program to fulfill the request.
   ```bash
   cat examples/titanics.csv | tulp -x how many persons survived
   ```

In all cases, TULP outputs answers to standard output and any additional information to standard error. You can safely pipe the output to a file or another command, while still receiving all information and errors on stderr.

**Important:** If your input exceeds 5000 characters, it will be split into multiple chunks and processed by the selected AI model in multiple requests. The result quality may vary depending on the task (e.g., translations or grammatical corrections work well, summarizing may not). TULP performs best with inputs under 5000 characters.

By default, TULP uses **gpt-4o** for its cost-effectiveness and speed. For complex tasks, specifying the model is recommended:
```bash
tulp --model {model_name} {a complex task}
```

### Options

```
usage: tulp [-h] [-x] [-w W] [--model MODEL] [--max-chars MAX_CHARS] [--cont CONT] [-v] [-q] [--groq_api_key GROQ_API_KEY]
            [--ollama_host OLLAMA_HOST] [--anthropic_api_key ANTHROPIC_API_KEY] [--openai_api_key OPENAI_API_KEY]
            [--openai_baseurl OPENAI_BASEURL] [--gemini_api_key GEMINI_API_KEY]
            ...

TULP Understands Language Promptly:
A command-line tool inspired by POSIX utilities, designed to help you
**process**, **filter**, and **create** data in the realm of Artificial
Intelligence.

TULP supports different backends and models, automatically selecting the backend for each model. Supported models include:

   - groq.* : Any groq model ID prefixed with 'groq.', using the GROQCLOUD API and requiring a GROQ_API_KEY. Check available models at https://console.groq.com/docs/models
   - ollama.* : Any ollama model prefixed with 'ollama', running on the ollama_host.
   - claude-.* : Any Anthropic claude model (https://docs.anthropic.com/claude/docs/models-overview), requiring an ANTHROPIC_API_KEY
   - gpt-.* : Any OpenAI model (https://platform.openai.com/docs/models), requiring an openai_api_key
   - gemini.* : Any Google gemini model (https://ai.google.dev/gemini-api/docs/models/gemini), requiring a gemini_api_key

Positional arguments:
  request               User request, instructions written in natural language

Options:
  -h, --help            Show this help message and exit
  -x                    Allow TULP to create a program and execute it to fulfill the task (code interpret)
  -w W                  Write the output (or the created program for execution) to a file. If the file exists, a backup will be created before overwriting it.
  --model MODEL         Select the OpenAI LLM model to use (default: gpt-4-turbo)
  --max-chars MAX_CHARS Number of characters per message chunk per request (Default 40000)
  --cont CONT           Automatically ask the model to continue until it finishes answering the request up to the given times
  -v                    Be verbose!
  -q                    Be quiet! Only print the answer and errors.
  --groq_api_key GROQ_API_KEY
                        GROQ cloud API KEY
  --ollama_host OLLAMA_HOST
                        Define custom ollama host, default is http://127.0.0.1:11434
  --anthropic_api_key ANTHROPIC_API_KEY
                        Anthropic API key
  --openai_api_key OPENAI_API_KEY
                        OpenAI cloud API KEY
  --openai_baseurl OPENAI_BASEURL
                        Change the server, e.g., use http://localhost:11434/v1/ to connect to your local ollama server
  --gemini_api_key GEMINI_API_KEY
                        Gemini cloud API KEY
```

## Configuration

The configuration file is located at `~/.tulp.conf`.

Configurable parameters include:
- **LOG_LEVEL**: The log level of TULP. Options are DEBUG, INFO, WARNING, ERROR, and CRITICAL. Default is INFO.
- **API_KEYS**: API keys for supported AI models (OpenAI, GROQ, Ollama, Anthropic, Gemini). Default is an empty string for each.
- **MAX_CHARS**: Maximum number of characters processed in one chunk. Default is 40000.
- **MODEL**: The AI model used by TULP. Default is gpt-4o, but other models are available.

These settings can be overridden by environment variables using the prefix TULP_ or by command-line arguments described above. As environment variables, they become: TULP_LOG_LEVEL, TULP_API_KEYS, TULP_MAX_CHARS, or TULP_MODEL. Command-line arguments override environmental variables and the configuration file.

Example configuration file with default values:
```INI
[DEFAULT]
LOG_LEVEL = INFO
${MODEL}_API_KEYS = <<<YOUR API KEYS FOR GROQ, OLLAMA, ANTHROPIC, OPENAI, GEMINI>>>
MAX_CHARS = 40000
MODEL = gpt-4o
```

## Examples

TULP's usage is versatile. Here are some examples for inspiration:

### Random

#### The Meaning of Life for Different Models

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

#### Create a Plot from Raw Memory Output Printed by gdb

Command:
```bash
cat <<EOF | tulp convert this to a python list of 2 element tuples |  tulp -x write a python function to scatter plot these points using matplotlib  
(gdb) p *polygon._points._M_ptr._M_impl._M_start@4
$21 = {{x = 0.441429973, y = -0.176619753}, {x = 0.476210177, y = -0.104575738}, {x = 0.674865067, y = -0.0814191923}, {x = 0.640084863, y = -0.199776307}}
EOF
```

Result:

![matplotlib @rela](./examples/rela_plot.png)

### Grammatical and Syntax Correction of Clipboard Content in Linux

The corrected version will be in the clipboard:
```bash
xsel -b | tulp fix my english | xsel -b
```

### Typical Unix Tooling Replacement

#### Sed
```bash
cat README.md | tulp replace all the occurrences of TULP for **TULP**
```

#### Awk
```bash
cat README.md | tulp print the second word of each line
```

#### Advanced Grep
```bash
cat tulp.py | tulp print the name of the functions and also the return line 
```

### Grammatical and Syntax Corrections
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

### Data Filtering from Formatted Input

#### CSV
```bash
cat list.csv | tulp print only the second column
Count
3
1
2
```

#### JSON to CSV
```bash
cat persons.json | tulp 'list the names and ages of each person in a csv table, using ; as separator'
```

### Data Creation and Extraction from Unstructured Data

A story of oranges and friends:
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

## Origin of the Name

I used `tulp.py` to create "TULP". In some way, everything is recursive in "TULP", so it makes sense to use a recursive acronym.

After several iterations with `tulp.py`, "TULP" and I decided that the best name would be "TULP", and this is how we decided what "TULP" stands for:
```bash
fede@liebre:~/repos/openai/tulp$ python3 ./tulp.py "TULP is a recursive acronym naming an opensource posix tool that processes stdin input according to natural language instructions, processing the input by instructing an artificial intelligence. Write some options of what TULP could stand for as recursive acronym"
TULP could stand for:
- TULP Understands Language Perfectly
- TULP Uses Language to Process
- TULP Understands Language Promptly
- TULP Utilizes Language for Processing
- TULP Unravels Language Precisely
```

## Why?

As a heavy user of Unix tools like awk, jq, sed, and grep, I relied on them heavily. However, with the advent of ChatGPT, I began using GPT for tasks I previously used Unix tools for. I felt the inconvenience of cut & paste and wanted a faster way to do it directly from the terminal, leading to the creation of `tulp`.

## Changelog

### v2.6.3 | 2024-09-16
- Adds support to openai chatgpt-\* models, like `chatgpt-4o-latest`, and the option to use "openai." prefix to select any future openai model.

- Improved output end detection and cleaning of spurious code blocks.

### v2.6.2 | 2024-08-29
- Improved output end detection and cleaning of spurious code blocks.

### v2.6.1 | 2024-08-29
- Changed gemini dependencies due to installation issues on some platforms.

### v2.6 | 2024-08-29
- **Refactor:** Renamed internal blocks, now the LLM knows the input as stdin.
- **New Features:** 
  - Added `--inspect-dir` option to save each iteration with the LLM to a directory for review, aiding in debugging and understanding interactions.
- **Bug Fixes:** Corrected a typo in the codebase.
- **Enhancements:** 
  - Integrated Gemini API dependencies to support interactions with Gemini LLMs.
  - Increased default maximum characters for responses to handle longer outputs.
  - Updated error messages for token limit exceedance to provide better context and guidance.

### v2.5 | 2024-07-27
- Fixed the --cont issue.
- Added Gemini API dependencies.
- Increased the default maximum characters.

### v2.3 | 2024-05-19
- Added -cont option to allow TULP to automatically request the LLM to continue if an incomplete response is found.
- Added automatic handling of RECITATION for Gemini LLM.

### v2.2 | 2024-05-14
- Fixed code execution (-x option).

### v2.1 | 2024-05-14
- Improved formatting of messages for Gemini.
- Changed to use gpt-4o model by default.

### v2.0 | 2024-05-04
- Added support for groq, ollama, anthropic, and gemini AI models.
- Changed to use gpt-4-turbo model by default.

### v1.0 | 2024-02-14
- Changed to use gpt-4-0125-preview model by default.
- Updated to use openapi v1.0.
- Changed default max-chars to 40000.

### v0.7 | 2023-05-23
- Added Code Interpretation, -x option.

### v0.6 | 2023-05-11
- Added all the settings as command-line arguments.

