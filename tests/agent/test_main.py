import os, sys

lib_path = os.path.abspath(os.path.join('..', 'src'))
if lib_path not in sys.path:
    sys.path.append(lib_path)

from agent.main import MainAgent

def test_main_agent():
    agent = MainAgent()
    assert agent is not None

def test_main_agent_generate_response():
    agent = MainAgent()
    response = agent.generate_response("Hello")
    assert response is not None