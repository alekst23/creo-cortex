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
def tool_set_working_dir(session_id: str, working_dir: str) -> str:
    """
    Sets the working directory for subsequent tool commands.
    `working_dir` must be the absolute path.
    """
    logger.info(">> TOOL: Setting working directory")
    logger.info(f"Working directory: {working_dir}")

    actor: Actor = get_actor(session_id)
    actor.memory.set_working_dir(working_dir)
    return f"Working directory set to {working_dir}"


@tool
def tool_aws_cli(session_id: str, param_string: str) -> str:
    """
    Runs an AWS CLI command and returns the output.
    Will execute `aws {param_string}`.
    """
    logger.info(">> TOOL: Running AWS CLI command")
    logger.info(f"Command: aws {param_string}")

    try:
        actor: Actor = get_actor(session_id)
        if param_string.startswith("aws"):
            command = param_string
        else:
            command = f"aws {param_string}"
        exit_code, stdout, stderr = actor.executor.execute_command(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            command=command,
        )
        if exit_code != 0:
            raise RuntimeError(f"AWS CLI command failed with exit code {exit_code}: {stderr}\n{stdout}")
        
        return str(stdout)
    except Exception as e:
        logger.error(f"Error running AWS CLI command: {str(e)}")
        return f"Error running AWS CLI command: {str(e)}"


@tool
def tool_shell(session_id: str, cmd_string: str) -> str:
    """
    Runs a shell command and returns the output.
    Accepts a string of arguments to pass to the shell.
    """
    logger.info(">> TOOL: Running shell command")
    logger.info(f"Command: {cmd_string}")

    try:    
        actor: Actor = get_actor(session_id)
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
def tool_save_note(session_id: str, note_text: str) -> str:
    """
    Saves a note to State Memory. This allows you to remember pieces of information from tool commands, research, conversations, and other sources.
    Use this command to remember useful facts in the short term.
    """
    logger.info(">> TOOL: Saving note")
    logger.info(f"Note: {note_text}")

    actor: Actor = get_actor(session_id)
    actor.memory.add_note(note_text)
    return f"Note saved to state memory successfully."

@tool
def tool_remove_note(session_id: str, note_id: str) -> str:
    """
    Removes a note from State Memory.
    """
    logger.info(">> TOOL: Removing note")
    logger.info(f"Note ID: {note_id}")

    actor: Actor = get_actor(session_id)
    actor.memory.remove_note(note_id)
    return f"Note removed from state memory successfully."

@tool
def tool_set_goal(session_id: str, goal: str) -> str:
    """
    Sets or updates your goal as designated by the user.
    Use markdown format and make sure to have the following two sections:
    - **User Story**: A brief description of the user story that captures the problem.
    - **Acceptance Criteria**: A list of criteria that must be met for the user story to be considered complete.
    """
    logger.info(">> TOOL: Setting goal")
    logger.info(f"Goal: {goal}")

    actor: Actor = get_actor(session_id)
    actor.memory.set_goal(goal)
    return f"Goal set to {goal}"


@tool
def tool_add_task(session_id: str, task: str, sort_order: float = None) -> str:
    """
    Adds a task to the task list.
    """
    logger.info(">> TOOL: Adding task")
    logger.info(f"Task: {task}")

    actor: Actor = get_actor(session_id)
    actor.memory.add_task(task, sort_order)
    return f"Task added successfully."

@tool
def tool_set_task_status(session_id: str, task_id: str, status: str) -> str:
    """
    Sets the status of a task.
    """
    logger.info(">> TOOL: Setting task status")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Status: {status}")

    actor: Actor = get_actor(session_id)
    actor.memory.set_task_status(task_id, status)
    return f"Task status set to {status} for task {task_id}"

@tool
def tool_close_task(session_id: str, task_id: str, status: str, result: str) -> str:
    """
    Closes a task and updates the status and result.
    The `status` parameter should be one of the following: `new`, `in_progress`, `done`, or `cancelled`.
    The `result` parameter should be in Markdown format and should reflect the outcome of the task.
    """
    logger.info(">> TOOL: Closing task")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Status: {status}")
    logger.info(f"Result: {result}")

    actor: Actor = get_actor(session_id)
    actor.memory.update_task(task_id, status, result)
    return f"Task closed with status {status} and result saved as a note."

@tool
def tool_clear_tasks(session_id: str) -> str:
    """
    Clears all tasks from the task list.
    """
    logger.info(">> TOOL: Clearing tasks")

    actor: Actor = get_actor(session_id)
    actor.memory.clear_tasks()
    return f"Tasks cleared successfully."


@tool
def tool_open_file(session_id: str, file_path: str) -> str:
    """
    Opens a file for reading into memory.
    `file_path` must be a path relative to the working directory.
    """
    logger.info(">> TOOL: Opening file")
    logger.info(f"File path: {file_path}")

    try:
        actor: Actor = get_actor(session_id)
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
    
@tool
def tool_close_file(session_id: str, file_path: str) -> str:
    """
    Closes a file and removes it from memory.
    """
    logger.info(">> TOOL: Closing file")
    logger.info(f"File path: {file_path}")

    actor: Actor = get_actor(session_id)
    actor.memory.remove_open_file(file_path)
    return f"File closed successfully."


@tool
def tool_write_file(session_id: str, file_path: str, file_data: str) -> str:
    """
    Writes data to a file.
    `file_path` must be a path relative to the working directory.
    """
    logger.info(">> TOOL: Writing file")
    logger.info(f"File path: {file_path}")
    import subprocess

    try:
        actor: Actor = get_actor(session_id)
        exit_code, stdout, stderr = actor.executor.write_to_file(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            file_path=file_path,
            content=file_data
        )
        if exit_code != 0:
            logger.error(f"Error writing file: {stderr}\n{stdout}")
            raise RuntimeError(f"Error writing file: {stderr}\n{stdout}")
        
        return f"File written successfully."
    
    except Exception as e:
        logger.error(f"Error writing file: {str(e)}")
        return f"Error writing file: {str(e)}"
