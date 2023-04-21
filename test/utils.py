import subprocess

def execute(cmd):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #if not result.returncode == 0:
    #    print(result)
    return result


