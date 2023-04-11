# TULP: TULP Understands Language Perfectly

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world, backed by chatGPT.

## Installation:

```
pip install tulp
``` 



## Usage:

TULP has 2 main operations modes:

1. stdin processing: Process or filter all the stdin input according to the user instructions:
```
cat [MYFILE] | tulp [Processing instructions written in natural language]
```
2. request: Process the user request:
```
tulp [A written request or question]
```
In both cases, TULP will write to the standard output the answers and will write any other information to the standard error.

It is important to note that if your input is larger than 4000 characters, the input will be split into multiple requests and the results may vary. It works great when the input is less than that.

## Configuration 
The configuration file is located at ~/.tulp.conf. Define your own ~/.tulp.conf file or define the same environment variable but using prefix TULP. 

The following are the parameters that can be configured:
- LOG_LEVEL: The log level of Tulip. Valid options are DEBUG, INFO, WARNING, ERROR, and CRITICAL. The default value is INFO.
- OPENAI_API_KEY: The API key for OpenAI. The default value is an empty string.
- MAX_CHARS: The maximum number of characters processed in one chunk. The default value is 5000.
- MODEL: The openai model used by Tulip. The default value is gpt-3.5-turbo, but gpt-4 is also available

As environment variables they will become: TULP_LOG_LEVEL, TULP_OPENAI_API_KEY, TULP_MAX_CHARS or TULP_MODEL

Here is an example configuration file with the default values:
```
[DEFAULT]
LOG_LEVEL = INFO
OPENAI_API_KEY = <<<YOUR API KEY >>>>
MAX_CHARS = 10000
MODEL = gpt-3.5-turbo
```
## Examples:
The usage is endless, but anyway, here you have some ideas as inspirations:
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
cat README.md | TULP_MAX_CHARS=10000 TULP_MODEL=gpt-4 tulp fix typos and syntax errors > README.fix.md

### Translations
cat README.md | tulp translate to Spanish > README.es.md

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


## Origin of the name
I used ```tulp.py``` to create "TULP". In some way, everything is recursive in "TULP", so it makes sense to use a recursive acronym.

Therefore, after several iterations with ```tulp.py```, "TULP" and I decided that the best name would be "TULP", and this is how we decided what "TULP" stands for:
```
fede@liebre:~/repos/openai/tulp$ python3 ./tulp.py "TULP is a recursive acronym naming an opensource posix tool that process stdin input according to natural language instructions, processing the input by instructing an artificial intelligence. Write some options of what TULP could stand for as recursive acronym"
TULP could stand for:
- TULP Understands Language Perfectly
- TULP Uses Language to Process
- TULP Understands Language Promptly
- TULP Utilizes Language for Processing
- TULP Unravels Language Precisely
```



## Why?

I am a heavy user of unix tooling (e.g: awk, jq, sed, grep and so on), I have been using them since my early days and I use to think that I can't survive without them. But then, chatGPT appears and I started to use more and more GPT for things that I use to use unix tooling. Somehow I feel the pain of cut&paste and I was missing a way to do it faster and from within the terminal itself, so I came up with ```tulp```
