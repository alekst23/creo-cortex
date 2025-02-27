import os
import sys
import subprocess
import docker
from typing import List, Optional, Dict

import logging

class DockerCommandExecutor:
    def __init__(self):
        """Initialize the Docker client."""
        self.client = docker.from_env()

    def execute_command(
        self,
        container_name: str,
        command: str,
        working_dir: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None
    ) -> tuple[int, str, str]:
        """
        Execute a command in a running container.
        
        Args:
            container_name: Name or ID of the container
            command: Command to execute
            working_dir: Working directory for command execution
            environment: Environment variables for the command
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            container = self.client.containers.get(container_name)
            
            # Check if container is running
            if container.status != "running":
                raise RuntimeError(f"Container {container_name} is not running")
            
            # Execute the command
            exec_result = container.exec_run(
                cmd=["/bin/sh", "-c", command],
                workdir=working_dir,
                environment=environment,
                demux=True  # Split stdout and stderr
            )
            
            exit_code = exec_result.exit_code
            stdout, stderr = exec_result.output
            
            # Decode bytes to string, handle None cases
            stdout_str = stdout.decode('utf-8') if stdout else ""
            stderr_str = stderr.decode('utf-8') if stderr else ""
            
            return exit_code, stdout_str, stderr_str
            
        except docker.errors.NotFound:
            raise ValueError(f"Container {container_name} not found")
        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error: {str(e)}")

    def write_to_file(
        self,
        container_name: str,
        working_dir: str,
        file_path: str,
        content: str
    ) -> None:
        """
        Write content to a file in a running container.
        
        Args:
            container_name: Name or ID of the container
            file_path: Path to the file in the container
            content: Content to write to the file
        """
        try:
            container = self.client.containers.get(container_name)
            
            # Check if container is running
            if container.status != "running":
                raise RuntimeError(f"Container {container_name} is not running")
            
            docker_path = os.path.join(working_dir, file_path)
            local_path = os.path.join("/tmp", file_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w") as f:
                f.write(content)
            
            result = subprocess.run(
                ["docker", "cp", local_path, f"{container_name}:{docker_path}"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to copy file to container: {result.stderr}")
            else:
                return 0, "File copied succesfully", None

        except docker.errors.NotFound:
            raise ValueError(f"Container {container_name} not found")
        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error: {str(e)}")