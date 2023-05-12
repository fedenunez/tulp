import subprocess
def execute_python_code(code, input_data):
    process = subprocess.Popen(
        ["python", "-c", code],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate(input=input_data.encode())
    return_code = process.returncode
    return stdout.decode(), stderr.decode(), return_code

