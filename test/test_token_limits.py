import subprocess
import json

def test_output_is_too_long():
    count=100
    BASESTR=" the input is already long \n"
    cmd = f"echo '{BASESTR*count}' | ./main.py repeat the input 100 times"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res = result.stderr.decode().strip()
    assert result.returncode != 0
    assert "Token limit exceeded" in res

