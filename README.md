# TULIP: TULIP Understands Language Instructions Promptly

A command line tool, in the best essence of POSIX tooling, that will help you to **process**, **filter**, and **create** data in this new Artificial Intelligence world.


## Examples:
The usage is endless, but anyway, here you have some ideas as inspirations:
### Data creation and extraction from unstructured data (a story of oranges and friends):
```
fede@liebre:~/repos/tulip$ tulip write a poem that names 3 persons \(given each a name\) and list how they shared 10 oranges | tee examples/oranges_poem.txt
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

fede@liebre:~/repos/tulip$ cat examples/oranges_poem.txt | python3 ./tulip.py write a list of persons and the number of oranges that they have as csv
Ann,3
Ben,3
Sue,4
```
### Typical Unix tooling replacement:
#### Sed
cat README.md | tulip replace all the occurrences of TULIP for **TULIP**
#### Awk
cat README.md | tulip print the second word of each line
#### grep, but advanced
cat tulip.py | tulip print the name of the functions and also the return line 

### Grammatical and syntax corrections:

cat README.md | tulip fix any grammatical or syntactical error > README.md.fixed

### Translations
cat README.md | tulip translate to Spanish > README.es.md

### Data filtering from formatted input
#### csv
```
cat list.csv | tulip print only the second column
Count
3
1
2

```
#### csv
```
cat persons.json | tulip 'list the names an ages of each person in a csv table, using ; as separator'

```


## From where comes the Recursive Acronym origins:

Just in case you want to know the origin, let's say that it comes from recursive generation some how:
```
fede@liebre:~/repos/openai/tulip$ python3 ./tulip.py "TULIP is a recursive acronym naming an opensource posix tool that process stdin input according to natural language instructions, processing the input by instructing an artificial intelligence. Write some options of what TULIP could stand for as recursive acronym"
TULIP could stand for:
- TULIP Understands Language Instructions Perfectly
- TULIP Uses Language Instructions to Process
- TULIP Understands Language Input Promptly
- TULIP Utilizes Language Instructions for Processing
- TULIP Unravels Language Instructions Precisely
```



## Why?

I think that I am a heavy user of unix tooling (e.g: awk, jq, sed, grep and so one), I have been using them since my early days and I use to thing that I can't survive without them. But then, chatGPT appears and I started to use more and more GPT for things that I use to use unix tooling. Some how I feel the pain of cut&paste and I was missing a way to doit faster and from within the terminal itself, so I came up with tulip, the swifknife for all my work. 


cat README.md | tulip make all TULIP be in bold and keep everything else unchanged
