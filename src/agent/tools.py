import os

from langchain_core.tools import tool

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

@tool
def tool_local_ip() -> str:
    """
    Provides the IP of the local machine.
    """
    logger.info(">> TOOL: Getting local IP")
    import socket 
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return f"Host info: {hostname}, {ip}"


@tool
def tool_aws_cli(param_string: str) -> str:
    """
    Runs an AWS CLI command and returns the output.
    Accepts a string of arguments to pass to the AWS CLI.
    """
    logger.info(">> TOOL: Running AWS CLI command")
    logger.info(f"Command: aws {param_string}")

    try:

        from docker_utils.docker_executor import DockerCommandExecutor

        executor = DockerCommandExecutor()
            
        exit_code, stdout, stderr = executor.execute_command(container_name=os.getenv("EXECUTION_CONTAINER_NAME", "my_container"),
            command=f"aws {param_string}",
        )
        if exit_code != 0:
            raise RuntimeError(f"AWS CLI command failed with exit code {exit_code}: {stderr}\n{stdout}")
        
        return stdout
    except Exception as e:
        logger.error(f"Error running AWS CLI command: {str(e)}")
        return f"Error running AWS CLI command: {str(e)}"
