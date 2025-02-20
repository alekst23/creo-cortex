import os

from langchain_core.tools import tool

from docker_utils.docker_executor import DockerCommandExecutor
from agent.session_memory import SessionMemory, get_session_memory

from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)

DEFAULT_CONTAINER_NAME = "my_execution_container"

class Actor:
    executor: DockerCommandExecutor
    memory: SessionMemory

    def __init__(self, session_memory: SessionMemory=None):
        self.executor = DockerCommandExecutor()
        self.memory = session_memory or get_session_memory()

_actor: Actor = None
def get_actor(session_memory: SessionMemory = None) -> Actor:
    global _actor
    if _actor is None:
        _actor = Actor(session_memory)
    return _actor