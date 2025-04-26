import os, sys
import pytest

lib_path = os.path.abspath(os.path.join('..', 'src'))
if lib_path not in sys.path:
    sys.path.append(lib_path)

from agent.main import MainAgent
from agent.session_memory import get_session_memory

@pytest.fixture
def session_memory():
    return get_session_memory("mock-session")

def test_main_agent(session_memory):
    agent = MainAgent(session_memory)
    assert agent is not None

def test_main_agent_generate_response(session_memory):
    agent = MainAgent(session_memory)
    response = agent.generate_response("Hello")
    assert response is not None

def test_get_open_files(session_memory):
    session_memory.set_working_dir("/container/projects")
    session_memory.set_open_file("README.md")
    agent = MainAgent(session_memory)
    files = agent.get_open_files()
    assert files is not None