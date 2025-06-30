import subprocess
from threading import Timer
import time


def docker_copy_file_to(container_name, local_file, container_dest_path):
    try:
        subprocess.run(
            ["docker", "cp", local_file, f"{container_name}:{container_dest_path}"],
            check=True
        )
        print(f"Copied {local_file} to {container_name}:{container_dest_path}")
    except subprocess.CalledProcessError as e:
        print("Error copying file to container:", e)

def run_maskgen(command):
    proc = subprocess.Popen(command.split(" "),
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
    timer = Timer(10, proc.kill)
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
    
    time.sleep(1) # Give the program a moment to start and print
    # output = proc.stdout.read()
    # print(f"Subprocess output: {output}")


def run_command(command):
    """
    Runs a shell command and returns whether it succeeded and its output.

    Returns:
        (bool, str): (success, output or error message)
    """
    try:
        result = subprocess.run(
            command.split(" "),
            check=True,
            capture_output=True,
            text=True
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

def docker_get_file(container_name, container_file_path, host_destination_path):
    try:
        subprocess.run(
            ["docker", "cp", f"{container_name}:{container_file_path}", host_destination_path],
            check=True
        )
        print(f"Copied {container_file_path} from {container_name} to {host_destination_path}")
    except subprocess.CalledProcessError as e:
        print("Error copying file from container:", e)