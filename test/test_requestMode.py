import json
from utils import execute

def test_request_code_creation_hello():
    cmd = "./main.py 'write a python program that print \"Hello tulp world\" ' | python"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == 'Hello tulp world'

def test_request_code_creation_countdown():
    cmd = "./main.py 'write a python program that prints a count down from 10 to 0, without any delay, and then prints Hello tulp world' | python"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == '10\n9\n8\n7\n6\n5\n4\n3\n2\n1\n0\nHello tulp world'

def test_request_command_creation_sed():
    cmd = "./main.py write the sed command execution needed to remplace all the ocurrances of failed to PASSED, reading from std input, just write the command ready to be run"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == "sed 's/failed/PASSED/g'"


def test_request_describe_a_command_xclip():
    cmd = "./main.py describe the following command: 'xclip -i -s c'"
    result = execute(cmd)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert "copy" in res 
    assert "standard input" in res
    assert "clipboard" in res
