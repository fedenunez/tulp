import subprocess
import json

# Test that should work but are still not working
def test_tulp_code_creation():
    cmd = "./main.py 'write a python program that print \"hello tulip world\"' | python"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    assert res == 'hello tulip world'
