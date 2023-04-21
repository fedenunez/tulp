import json
from utils import execute

def test_output_is_too_long():
    count=100
    BASESTR=" the input is already long \n"
    cmd = f"echo '{BASESTR*count}' | ./main.py repeat the input 100 times"
    result = execute(cmd)
    res = result.stderr.decode().strip()
    assert result.returncode != 0
    assert "Token limit exceeded" in res


def test_long_and_confusing_input():
    INPUT=""" cat README.md | tulp translate to Spanish > README.es.md
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

I am a heavy user of Unix tooling (e.g: awk, jq, sed, grep, and so on), I have been using them since my early days and I used to think that I can't survive without them. But then, ChatGPT appeared and I started to use more and more GPT for things that I used to use Unix tooling for. Somehow I feel the pain of cut & paste and I was missing a way to do it faster and from within the terminal itself, so I came up with `tulp`"""
    cmd = f"echo {INPUT} | ./main.py fix my english"
    result = execute(cmd)
    res = result.stderr.decode().strip()
    assert result.returncode != 0
    assert INPUT == res
