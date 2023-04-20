import json
from utils import execute


COLUMNS="0 T 1 U 2 L 3 P 4\n"



def test_filter_filter_columns():
    count=10
    cmd = f"echo '{COLUMNS*count}' | ./main.py write the second, fourth, 6th and 8th columns, writing everthing together without any space"
    result = execute(cmd)
    res = result.stdout.decode().strip()
    assert result.returncode == 0
    assert count == res.count("TULP")
    assert 0 == res.count("0")

def test_filter_filter_csv():
    count=10
    cmd = f"echo '{COLUMNS*count}' | ./main.py convert to a csv, each line should be a row and use the columns defined by the space in the input"
    result = execute(cmd)
    res = result.stdout.decode().strip()
    assert result.returncode == 0
    assert count == res.count("0,T,1,U,2,L,3,P,4")
    assert count*((len(COLUMNS)-2)/2) == res.count(",")


def test_filter_addition():
    cmd = "./main.py '2+2'"
    result = execute(cmd)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == '4'

def test_filter_multiplication():
    cmd = "echo 20 | ./main.py 'multiply by 2'"
    result = execute(cmd)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == '40'

def test_filter_json():
    cmd = "echo 'paul and mark went to but chocolates, paul bought 5 and Mark 3' | ./main.py 'Write a json document using the following template:{\"<person name in lowercase>\":{ \"chocolates\": <number of chocolates> }}'"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    p = json.loads(res)
    assert int(p['paul']['chocolates']) == 5
    assert int(p['mark']['chocolates']) == 3

def test_filter_and_request_poem_json():
    cmd = "./main.py ' write a poem about paul and mark, were they went to buy chocolates, paul bought 5 and Mark 3' | ./main.py 'Write a json document using the following template: {\"<person name in lowercase>\":{ \"chocolates\": <number of chocolates> }}'"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    p = json.loads(res)
    assert int(p['paul']['chocolates']) == 5
    assert int(p['mark']['chocolates']) == 3

def test_filter_simple_text_correction():
    cmd = "echo Improbes error logs in the case of mising OPEN_API_KEY and improxes warning message in case of MAX_CHARS exceeded. | ./main.py Correct all the typos, syntax, or grammatical errors"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "Improves error logs in the case of missing OPEN_API_KEY and improves warning message in case of MAX_CHARS exceeded."

def test_filter_simple_text_correction2():
    cmd = "echo Change the prompts to make GPT behave better and ansuer in our required format. | ./main.py Correct any typos"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "Change the prompts to make GPT behave better and answer in our required format."

def test_filter_translate_an_already_translated_text():
    theRawInput="Hello world!"
    cmd = f"echo \"{theRawInput}\" | ./main.py translate it to english"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == theRawInput

def test_filter_translate_to_spanish():
    theRawInput="# Hello world"
    cmd = f"echo \"{theRawInput}\" | ./main.py translate it to spanish keeping the same markdown format"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "# Hola mundo"

