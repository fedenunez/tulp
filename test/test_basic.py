import subprocess
import json


COLUMNS="0 T 1 U 2 L 3 P 4\n"

def test_filter_columns():
    count=5
    cmd = f"echo '{COLUMNS*count}' | ./main.py write the second, fourth, 6th and 8th columns, writing everthing together without any space"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = result.stdout.decode().strip()
    assert result.returncode == 0
    assert count == res.count("TULP")
    assert 0 == res.count("0")

def test_filter_csv():
    count=10
    cmd = f"echo '{COLUMNS*count}' | ./main.py convert to a csv, each line should be a row and use the columns defined by the space in the input"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = result.stdout.decode().strip()
    assert result.returncode == 0
    assert count == res.count("0,T,1,U,2,L,3,P,4")
    assert count*((len(COLUMNS)-2)/2) == res.count(",")


def test_addition():
    cmd = "./main.py '2+2'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == '4'

def test_multiplication():
    cmd = "echo 20 | ./main.py 'multiply by 2'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == '40'

def test_json():
    cmd = "echo 'paul and mark went to but chocolates, paul bought 5 and Mark 3' | ./main.py 'Write a json document using the following template:{\"<person name in lowercase>\":{ \"chocolates\": <number of chocolates> }}'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    p = json.loads(res)
    assert int(p['paul']['chocolates']) == 5
    assert int(p['mark']['chocolates']) == 3

def test_poem_json():
    cmd = "./main.py ' write a poem about paul and mark, were they went to buy chocolates, paul bought 5 and Mark 3' | ./main.py 'Write a json document using the following template: {\"<person name in lowercase>\":{ \"chocolates\": <number of chocolates> }}'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    p = json.loads(res)
    assert int(p['paul']['chocolates']) == 5
    assert int(p['mark']['chocolates']) == 3

def test_simple_text_correction():
    cmd = "echo Improbes error logs in the case of mising OPEN_API_KEY and improxes warning message in case of MAX_CHARS exceeded. | ./main.py Correct all the typos, syntax, or grammatical errors"

    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "Improves error logs in the case of missing OPEN_API_KEY and improves warning message in case of MAX_CHARS exceeded."

def test_simple_text_correction2():
    cmd = "echo Change the prompts to make GPT behave better and ansuer in our required format. | ./main.py Correct any typos"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "Change the prompts to make GPT behave better and answer in our required format."

def test_translate_an_already_translated_text():
    theRawInput="Hello world!"
    cmd = f"echo \"{theRawInput}\" | ./main.py translate it to english"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == theRawInput

def test_translate_to_spanish():
    theRawInput="# Hello world!"
    cmd = f"echo \"{theRawInput}\" | ./main.py translate it to spanish keeping the same markdown format"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "# ¡Hola mundo!"

