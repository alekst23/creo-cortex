import os

from mcp.server.fastmcp import FastMCP, Context

from agent.actor import get_actor, Actor

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

mcp = FastMCP()

DEFAULT_CONTAINER_NAME = "agent-execution-container"


@mcp.tool()
async def tool_set_working_dir(ctx: Context, session_id: str, working_dir: str) -> str:
    """
    Sets the working directory for shell commands.
    `working_dir` must be the absolute path.
    """
    await ctx.info(">> TOOL: tool_set_working_dir")
    await ctx.info(f"Working directory: {working_dir}")

    actor: Actor = get_actor(session_id)
    actor.memory.set_working_dir(working_dir)
    return f"Working directory set to {working_dir}"


@mcp.tool()
async def tool_aws_cli(ctx: Context, session_id: str, aws_command: str) -> str:
    """
    Runs an AWS CLI command and returns the output.
    """
    await ctx.info(">> TOOL: tool_aws_cli")
    await ctx.info(f"Command: {aws_command}")

    try:
        actor: Actor = get_actor(session_id)
        if aws_command.startswith("aws"):
            command = aws_command
        else:
            command = f"aws {aws_command}"
        exit_code, stdout, stderr = actor.executor.execute_command(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            command=command,
        )
        if exit_code != 0:
            raise RuntimeError(f"AWS CLI command failed with exit code {exit_code}: {stderr}\n{stdout}")
        
        return str(stdout)
    except Exception as e:
        await ctx.error(f"Error running AWS CLI command: {str(e)}")
        return f"Error running AWS CLI command: {str(e)}"


@mcp.tool()
async def tool_shell(ctx: Context, session_id: str, cmd_string: str) -> str:
    """
    Runs a shell command and returns the output.
    Accepts a string of arguments to pass to the shell.
    """
    await ctx.info(">> TOOL: Running shell command")
    await ctx.info(f"Command: {cmd_string}")

    try:    
        actor: Actor = get_actor(session_id)
        exit_code, stdout, stderr = actor.executor.execute_command(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            command=f"{cmd_string}",
        )
        if exit_code != 0:
            raise RuntimeError(f"shell command failed with exit code {exit_code}: {stderr}\n{stdout}")
        
        return str(stdout)
    except Exception as e:
        await ctx.error(f"Error running shell command: {str(e)}")
        await ctx.error(f"working_dir={actor.memory.get_working_dir()}")
        return f"Error running shell command: {str(e)}"


@mcp.tool()
async def tool_save_note(ctx: Context, session_id: str, note_text: str) -> str:
    """
    Saves a note to State Memory. This allows you to remember pieces of information from tool commands, research, conversations, and other sources.
    Use this command to remember useful facts in the short term.
    """
    await ctx.info(">> TOOL: Saving note")
    await ctx.info(f"Note: {note_text}")

    actor: Actor = get_actor(session_id)
    actor.memory.add_note(note_text)
    return f"Note saved to state memory successfully."


@mcp.tool()
async def tool_remove_note(ctx: Context, session_id: str, note_id: str) -> str:
    """
    Removes a note from State Memory.
    """
    await ctx.info(">> TOOL: Removing note")
    await ctx.info(f"Note ID: {note_id}")

    actor: Actor = get_actor(session_id)
    actor.memory.remove_note(note_id)
    return f"Note removed from state memory successfully."


@mcp.tool()
async def tool_set_goal(ctx: Context, session_id: str, goal: str) -> str:
    """
    Sets or updates your goal as designated by the user.
    Use markdown format and make sure to have the following two sections:
    - **User Story**: A brief description of the user story that captures the problem.
    - **Acceptance Criteria**: A list of criteria that must be met for the user story to be considered complete.
    """
    await ctx.info(">> TOOL: Setting goal")
    await ctx.info(f"Goal: {goal}")

    actor: Actor = get_actor(session_id)
    actor.memory.set_goal(goal)
    return f"Goal set to {goal}"


@mcp.tool()
async def tool_add_task(ctx: Context, session_id: str, task: str, sort_order: float = None) -> str:
    """
    Adds a task to the task list.
    """
    await ctx.info(">> TOOL: Adding task")
    await ctx.info(f"Task: {task}")

    actor: Actor = get_actor(session_id)
    actor.memory.add_task(task, sort_order)
    return f"Task added successfully."


@mcp.tool()
async def tool_set_task_status(ctx: Context, session_id: str, task_id: str, status: str) -> str:
    """
    Sets the status of a task.
    """
    await ctx.info(">> TOOL: Setting task status")
    await ctx.info(f"Task ID: {task_id}")
    await ctx.info(f"Status: {status}")

    actor: Actor = get_actor(session_id)
    actor.memory.set_task_status(task_id, status)
    return f"Task status set to {status} for task {task_id}"


@mcp.tool()
async def tool_close_task(ctx: Context, session_id: str, task_id: str, status: str, result: str) -> str:
    """
    Closes a task and updates the status and result.
    The `status` parameter should be one of the following: `done`, or `cancelled`.
    The `result` parameter should be in Markdown format and should reflect the outcome of the task.
    """
    await ctx.info(">> TOOL: Closing task")
    await ctx.info(f"Task ID: {task_id}")
    await ctx.info(f"Status: {status}")
    await ctx.info(f"Result: {result}")

    actor: Actor = get_actor(session_id)
    actor.memory.update_task(task_id, status, result)
    return f"Task closed with status {status} and result saved as a note."


@mcp.tool()
async def tool_clear_tasks(ctx: Context, session_id: str) -> str:
    """
    Clears all tasks from the task list.
    """
    await ctx.info(">> TOOL: Clearing tasks")

    actor: Actor = get_actor(session_id)
    actor.memory.clear_tasks()
    return f"Tasks cleared successfully."


@mcp.tool()
async def tool_open_file(ctx: Context, session_id: str, file_path: str) -> str:
    """
    Opens a file for reading into memory.
    `file_path` must be a path relative to the working directory.
    """
    await ctx.info(">> TOOL: Opening file")
    await ctx.info(f"File path: {file_path}")

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
        actor.memory.set_open_file(file_path)
        return f"{file_path} opened successfully:\n{data}"
    except Exception as e:
        await ctx.error(f"Error opening file: {str(e)}")
        return f"Error opening file: {str(e)}"
    

@mcp.tool()
async def tool_close_file(ctx: Context, session_id: str, file_path: str) -> str:
    """
    Closes a file and removes it from memory.
    """
    await ctx.info(">> TOOL: Closing file")
    await ctx.info(f"File path: {file_path}")

    actor: Actor = get_actor(session_id)
    actor.memory.remove_open_file(file_path)
    return f"File closed successfully."


@mcp.tool()
async def tool_write_file(ctx: Context, session_id: str, file_path: str, file_data: str) -> str:
    """
    Use this tool to write data to a file by providing the file contents as a string input to "file_data" parameter.
    `file_path` must be a path relative to the working directory.
    `file_data` is a string or byte list to write to the file.
    """
    await ctx.info(">> TOOL: Writing file")
    await ctx.info(f"File path: {file_path}")

    try:
        actor: Actor = get_actor(session_id)
        
        exit_code, stdout, stderr = actor.executor.write_to_file(
            container_name=os.getenv("EXECUTION_CONTAINER_NAME", DEFAULT_CONTAINER_NAME),
            working_dir=actor.memory.get_working_dir(),
            file_path=file_path,
            content=file_data
        )
        if exit_code != 0:
            await ctx.error(f"Error writing file: {stderr}\n{stdout}")
            raise RuntimeError(f"Error writing file: {stderr}\n{stdout}")
        
        return f"File written successfully."
    
    except Exception as e:
        await ctx.error(f"Error writing file: {str(e)}")
        return f"Error writing file: {str(e)}"


if __name__ == "__main__":
    print("\n\n>>> Starting FastMCP server...")
    mcp.settings.port = 8080
    mcp.run(transport="sse")