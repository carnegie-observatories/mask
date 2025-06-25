import subprocess

def docker_copy_file_to(container_name, local_file, container_dest_path):
    try:
        subprocess.run(
            ["docker", "cp", local_file, f"{container_name}:{container_dest_path}"],
            check=True
        )
        print(f"Copied {local_file} to {container_name}:{container_dest_path}")
    except subprocess.CalledProcessError as e:
        print("Error copying file to container:", e)

def docker_run_command(container_name, command):
    """
    Runs a command in a selected docker container
    Args:
        container_name (str): name of the docker container
        command (str): string containing the whole command seperated by spaces. ex: "ls -a mask"
    """
    try:
        subprocess.run(
            ["docker", "exec", container_name] + command.split(" "),
            check=True
        )
        print(f"Command `{command}` executed successfully in {container_name}")
    except subprocess.CalledProcessError as e:
        print("Error running command:", e)

def docker_get_file(container_name, container_file_path, host_destination_path):
    try:
        subprocess.run(
            ["docker", "cp", f"{container_name}:{container_file_path}", host_destination_path],
            check=True
        )
        print(f"Copied {container_file_path} from {container_name} to {host_destination_path}")
    except subprocess.CalledProcessError as e:
        print("Error copying file from container:", e)