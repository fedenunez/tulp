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
    INPUT= """Therefore, after several iterations with `tulp.py`, "TULP" and I decided that the best name would be "TULP", and this is how we decided what "TULP" stands for:
```bash
fede@liebre:~/repos/openai/tulp$ python3 ./tulp.py "TULP is a recursive acronym naming an opensource posix tool that processes stdin input according to natural language instructions, processing the input by instructing an artificial intelligence. Write some options of what TULP could stand for as recursive acronym"
"""
    cmd = f"cat README.md | ./main.py fix my english"
    result = execute(cmd)
    res = result.stdout.decode().strip()
    assert result.returncode == 0
    assert INPUT in res
