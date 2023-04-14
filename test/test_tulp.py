import subprocess
import json

def test_tulp_addition():
    cmd = "python ./main.py '2+2'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == '4'

def test_tulp_multiplication():
    cmd = "echo 20 | python ./main.py 'multiply by 2'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    assert result.stdout.decode().strip() == '40'

def test_tulp_json():
    cmd = "echo 'paul and mark went to but chocolates, paul bought 5 and Mark 3' | python ./main.py 'create a json document with a persons dictionary to access each person and add chocolates property with the number of chocolates each has, using all keys on lowercase'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    p = json.loads(res)
    assert p['paul']['chocolates'] == 5
    assert p['mark']['chocolates'] == 3

def test_tulp_poem_json():
    cmd = "./main.py ' write a poem about paul and mark, were they went to buy chocolates, paul bought 5 and Mark 3' | python ./main.py 'create a json document with a persons dictionary to access each person and add chocolates property with the number of chocolates each has, using all keys on lowercase'"
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert result.returncode == 0
    res = result.stdout.decode().strip()
    p = json.loads(res)
    assert p['paul']['chocolates'] == 5
    assert p['mark']['chocolates'] == 3

