import os

from langchain_core.tools import tool

from docker_utils.docker_executor import DockerCommandExecutor
from agent.actor import get_actor, Actor

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

DEFAULT_CONTAINER_NAME = "my_execution_container"


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
def tool_set_working_dir(working_dir: str) -> str:
    """
    Sets the working directory for subsequent tool commands.
    `working_dir` must be the absolute path.
    """
    logger.info(">> TOOL: Setting working directory")
    logger.info(f"Working directory: {working_dir}")

    actor: Actor = get_actor()
    actor.memory.set_working_dir(working_dir)
    return f"Working directory set to {working_dir}"


@tool
def tool_aws_cli(param_string: str) -> str:
    """
    Runs an AWS CLI command and returns the output.
    Will execute `aws {param_string}`.
    """
    logger.info(">> TOOL: Running AWS CLI command")
    logger.info(f"Command: aws {param_string}")

    try:
        actor: Actor = get_actor()
        exit_code, stdout, stderr = actor.executor.execute_command(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            command=f"aws {param_string}",
        )
        if exit_code != 0:
            raise RuntimeError(f"AWS CLI command failed with exit code {exit_code}: {stderr}\n{stdout}")
        
        return str(stdout)
    except Exception as e:
        logger.error(f"Error running AWS CLI command: {str(e)}")
        return f"Error running AWS CLI command: {str(e)}"


@tool
def tool_shell(cmd_string: str) -> str:
    """
    Runs a shell command and returns the output.
    Accepts a string of arguments to pass to the shell.
    """
    logger.info(">> TOOL: Running shell command")
    logger.info(f"Command: {cmd_string}")

    try:    
        actor: Actor = get_actor()
        exit_code, stdout, stderr = actor.executor.execute_command(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            command=f"{cmd_string}",
        )
        if exit_code != 0:
            raise RuntimeError(f"AWS CLI command failed with exit code {exit_code}: {stderr}\n{stdout}")
        
        return str(stdout)
    except Exception as e:
        logger.error(f"Error running AWS CLI command: {str(e)}")
        return f"Error running AWS CLI command: {str(e)}"
    

@tool
def tool_save_note(note_text: str) -> str:
    """
    Saves a note to State Memory. This allows you to remember pieces of information from tool commands, research, conversations, and other sources.
    Use this command to remember useful facts in the short term.
    """
    logger.info(">> TOOL: Saving note")
    logger.info(f"Note: {note_text}")

    from agent.session_memory import SessionMemory, get_session_memory
    memory: SessionMemory = get_session_memory()
    memory.add_note(note_text)
    return f"Note saved to state memory successfully."
