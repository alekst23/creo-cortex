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
        logger.error(f"working_dir={actor.memory.get_working_dir()}")
        return f"Error running AWS CLI command: {str(e)}"
    

@tool
def tool_save_note(note_text: str) -> str:
    """
    Saves a note to State Memory. This allows you to remember pieces of information from tool commands, research, conversations, and other sources.
    Use this command to remember useful facts in the short term.
    """
    logger.info(">> TOOL: Saving note")
    logger.info(f"Note: {note_text}")

    actor: Actor = get_actor()
    actor.memory.add_note(note_text)
    return f"Note saved to state memory successfully."


@tool
def tool_set_goal(goal: str) -> str:
    """
    Sets or updates your goal as designated by the user.
    """
    logger.info(">> TOOL: Setting goal")
    logger.info(f"Goal: {goal}")

    actor: Actor = get_actor()
    actor.memory.set_goal(goal)
    return f"Goal set to {goal}"


@tool
def tool_add_task(task: str, sort_order: float = None) -> str:
    """
    Adds a task to the task list.
    """
    logger.info(">> TOOL: Adding task")
    logger.info(f"Task: {task}")

    actor: Actor = get_actor()
    actor.memory.add_task(task, sort_order)
    return f"Task added successfully."

@tool
def tool_set_task_status(task_id: str, status: str) -> str:
    """
    Sets the status of a task.
    """
    logger.info(">> TOOL: Setting task status")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Status: {status}")

    actor: Actor = get_actor()
    actor.memory.set_task_status(task_id, status)
    return f"Task status set to {status} for task {task_id}"


@tool
def tool_open_file(file_path: str) -> str:
    """
    Opens a file for reading into memory.
    `file_path` must be a path relative to the working directory.
    """
    logger.info(">> TOOL: Opening file")
    logger.info(f"File path: {file_path}")

    try:
        actor: Actor = get_actor()
        exit_code, stdout, stderr = actor.executor.execute_command(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            command=f"cat {file_path}",
        )
        if exit_code != 0:
            raise RuntimeError(f"Error opening file: {stderr}\n{stdout}")
        
        data = stdout
        actor.memory.set_open_file(file_path, data)
        return f"File opened successfully."
    except Exception as e:
        logger.error(f"Error opening file: {str(e)}")
        return f"Error opening file: {str(e)}"