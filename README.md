# TULP: TULP Understands Language Perfectly

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world, backed by chatGPT.

TULP allows you to harness the power of chatGPT by piping standard input content directly to chatGPT, getting the answer back on the shell.

<a href="https://asciinema.org/a/576555" target="_blank"><img src="https://asciinema.org/a/576555.svg" width=640  /></a>

## Installation:

```
pip install tulp
```

## Usage:

TULP has 2 main operation modes:

1. **request:** Process the user request:
```
tulp [A written request or question]
```
2. **stdin processing:** Process or filter all the stdin input according to the user instructions, writing the processed output to stdout.
```
cat [MYFILE] | tulp [Processing instructions written in natural language]
```

In both cases, TULP will write to the standard output the answers and will write any other information to the standard error. You can safely pipe the output to your file or next piping command and will still get all the information and errors on stderr.

It is **important** to note that if your input is larger than 5000 characters, the input will be split into multiple chunks and processed by chatGPT in multiple requests. In this case, the result quality will really depend on the task (e.g., will work fine for translations or grammatical corrections, it will work terribly for summarizing). Anyway, **tulp works great when the input is less than 5000 chars**.

By default, tulp uses **gpt-3.5-turbo**, because it is cheaper and **faster**, but for complex tasks, it is always a **good idea to force the gpt-4 model**: TULP_MODEL=gpt-4 tulp {a complex task}

## Configuration 
The configuration file is located at ~/.tulp.conf. Define your own ~/.tulp.conf file or define the same environment variable but using the prefix TULP_. 

The following are the parameters that can be configured:
- **LOG_LEVEL**: The log level of Tulp. Valid options are DEBUG, INFO, WARNING, ERROR, and CRITICAL. The default value is INFO.
- **OPENAI_API_KEY**: The API key for OpenAI. The default value is an empty string.
- **MAX_CHARS**: The maximum number of characters processed in one chunk. The default value is 5000.
- **MODEL**: The OpenAI model to be used by Tulp. The default value is gpt-3.5-turbo, but gpt-4 is also available.

As environment variables, they will become: TULP_LOG_LEVEL, TULP_OPENAI_API_KEY, TULP_MAX_CHARS, or TULP_MODEL.

Here is an example configuration file with the default values:
```
[DEFAULT]
LOG_LEVEL = INFO
OPENAI_API_KEY = <<<YOUR API KEY >>>>
MAX_CHARS = 10000
MODEL = gpt-3.5-turbo
```
## Examples:
The usage is endless, but anyway, here you have some ideas as inspiration:
### Typical Unix tooling replacement:
#### Sed
```
cat README.md | tulp replace all the occurrences of TULP for **TULP**
```
#### Awk
```
cat README.md | tulp print the second word of each line
```
#### grep, but advanced
```
cat tulp.py | tulp print the name of the functions and also the return line 
```

### Grammatical and syntax corrections:
```
cat README.md | tulp fix any grammatical or syntactical error > README.md.fixed
```

Or even better:
```
cat README.md | TULP_MAX_CHARS=10000 TULP_MODEL=gpt-4 tulp fix typos and syntax errors > README.fix.md
```

### Translations
```
cat README.md | tulp translate to Spanish > README.es.md
```
### Data filtering from formatted input
#### csv
```
cat list.csv | tulp print only the second column
Count
3
1
2
```

### csv

```
cat persons.json | tulp 'list the names and ages of each person in a csv table, using ; as separator'
```
### Data creation and extraction from unstructured data (a story of oranges and friends):
```
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
I used ```tulp.py``` to create "TULP". In some way, everything is recursive in "TULP", so it makes sense to use a recursive acronym.

Therefore, after several iterations with ```tulp.py```, "TULP" and I decided that the best name would be "TULP", and this is how we decided what "TULP" stands for:
```
fede@liebre:~/repos/openai/tulp$ python3 ./tulp.py "TULP is a recursive acronym naming an opensource posix tool that processes stdin input according to natural language instructions, processing the input by instructing an artificial intelligence. Write some options of what TULP could stand for as recursive acronym"
TULP could stand for:
- TULP Understands Language Perfectly
- TULP Uses Language to Process
- TULP Understands Language Promptly
- TULP Utilizes Language for Processing
- TULP Unravels Language Precisely
```

# Why?

I am a heavy user of Unix tooling (e.g: awk, jq, sed, grep, and so on), I have been using them since my early days and I used to think that I can't survive without them. But then, ChatGPT appeared and I started to use more and more GPT for things that I used to use Unix tooling for. Somehow I feel the pain of cut & paste and I was missing a way to do it faster and from within the terminal itself, so I came up with ```tulp```
