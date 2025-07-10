import subprocess
from threading import Timer


def run_maskgen(command):
    proc = subprocess.Popen(
        command.split(" "),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    timer = Timer(
        5, proc.kill
    )  # if application doesn't return within 5 sec, return error
    try:
        timer.start()
        stdout, stderr = proc.communicate()
        if proc.returncode == 0:
            return True, stdout.strip()
        else:
            return False, stderr.strip()
    except Exception as e:
        return False, str(e)
    finally:
        timer.cancel()


def run_command(command):
    """
    Runs a shell command and returns whether it succeeded and its output.

    Returns:
        (bool, str): (success, output or error message)
    """
    try:
        result = subprocess.run(
            command.split(" "), check=True, capture_output=True, text=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Return both stdout and stderr if there's an error
        if e.stdout or e.stderr:
            stdout = e.stdout or ""
            stderr = e.stderr or ""
            error_output = f"{stdout.strip()}\n{stderr.strip()}"
        else:
            error_output = str(e)
        return False, error_output.strip()
