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

_actor: Actor = {}
def get_actor(session_id: str) -> Actor:
    global _actor
    if not _actor or session_id not in _actor:
        _actor[session_id] = Actor(get_session_memory(session_id))
    return _actor[session_id]