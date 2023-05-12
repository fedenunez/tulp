# TULP: TULP Understands Language Promptly

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world, backed by chatGPT.

TULP allows you to harness the power of chatGPT by piping standard input content directly to chatGPT, getting the answer back on the shell.

[![tulp demo video](https://markdown-videos.deta.dev/youtube/mHAvlRXXp6I)](https://www.youtube.com/watch?v=mHAvlRXXp6I)

## Installation:

```bash
pip install tulp
```

## Usage:

TULP has 2 main operation modes:

1. **request:** Process the user request:
```bash
tulp [A written request or question]
```
2. **stdin processing:** Process or filter all the stdin input according to the user instructions, writing the processed output to stdout.
```bash
cat [MYFILE] | tulp [Processing instructions written in natural language]
```

In both cases, TULP will write to the standard output the answers and will write any other information to the standard error. You can safely pipe the output to your file or next piping command and will still get all the information and errors on stderr.

It is **important** to note that if your input is larger than 5000 characters, the input will be split into multiple chunks and processed by chatGPT in multiple requests. In this case, the result quality will really depend on the task (e.g., will work fine for translations or grammatical corrections, it will work terribly for summarizing). Anyway, **tulp works great when the input is less than 5000 chars**.

By default, tulp uses **gpt-3.5-turbo**, because it is cheaper and **faster**, but for complex tasks, it is always a **good idea to force the gpt-4 model**: tulp --model gpt-4 {a complex task}

### Options:
```
usage: tulp [-h] [--model {gpt-3.5-turbo,gpt-4}] [--max-chars MAX_CHARS] [-v] [-q] request

positional arguments:
  request               User request in natural language

optional arguments:
  -h, --help            show this help message and exit
  --model {gpt-3.5-turbo,gpt-4}
                        Select the LLM model to use, currently gpt-3.5-turbo or gpt-4
  --max-chars MAX_CHARS
                        Number of chars per message chunk per request
  -v                    Be verbose!
  -q                    Be quiet! Only print the answer and errors.
```


## Configuration 
The configuration file is located at ~/.tulp.conf. 

The following are the parameters that can be configured:
- **LOG_LEVEL**: The log level of Tulp. Valid options are DEBUG, INFO, WARNING, ERROR, and CRITICAL. The default value is INFO.
- **OPENAI_API_KEY**: The API key for OpenAI. The default value is an empty string.
- **MAX_CHARS**: The maximum number of characters processed in one chunk. The default value is 5000.
- **MODEL**: The OpenAI model to be used by Tulp. The default value is gpt-3.5-turbo, but gpt-4 is also available.

All these settings could be overridden by an environment variable using the prefix TULP\_ or by the different command line arguments described above. 
As environment variables, they will become: TULP_LOG_LEVEL, TULP_OPENAI_API_KEY, TULP_MAX_CHARS, or TULP_MODEL.
Command line arguments will override environmental variables and the configuration file.


Here is an example configuration file with the default values:
```INI
[DEFAULT]
LOG_LEVEL = INFO
OPENAI_API_KEY = <<<YOUR API KEY >>>>
MAX_CHARS = 10000
MODEL = gpt-3.5-turbo
```
## Examples:
The usage is endless, but anyway, here you have some ideas as inspiration:

### Random
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
## v0.6 | 2023-11-05
- Adds all the settings as command line arguments

