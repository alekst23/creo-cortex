import docker
from typing import List, Optional, Dict

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
                command,
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

