from typing import List
import os

from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_aws import ChatBedrock

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

import boto3

from agent.tools import (
    tool_local_ip,
    tool_aws_cli,
    tool_shell,
    tool_save_note,
    tool_set_working_dir
)

from agent.session_memory import SessionMemory
from agent.actor import get_actor

MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
PROMPT_FILE_DEFAULT = 'MAIN.txt'


def get_llm_openai():
    from langchain_openai import ChatOpenAI
    client = ChatOpenAI(temperature=0, model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    # client.max_tokens = 120000
    return client


def get_llm_bedrock():
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )
    bedrock_llm = ChatBedrock(
        model=MODEL_NAME_DEFAULT,
        client=bedrock_client,
        model_kwargs={'temperature': 0}
    )
    return bedrock_llm

def get_llm():
    return get_llm_openai()

DEFAULT_WORKING_DIR = '/container/data'

class MainAgent:
    tools: List[BaseTool]
    model: BaseChatModel
    session_memory: SessionMemory

    def __init__(self, session_memory: SessionMemory = None):
        self.actor = get_actor(session_memory)

        if not session_memory.get_working_dir():
            session_memory.set_working_dir(DEFAULT_WORKING_DIR)

        self.tools = [
            tool_local_ip,
            tool_set_working_dir,
            tool_aws_cli,
            tool_shell,
            tool_save_note
        ]
        self.model = get_llm()

        prompt = PromptTemplate.from_template(
            template=self.get_prompt_text()
        ).format(
            notes_memory=session_memory.get_notes(),
            working_dir=session_memory.get_working_dir()
        )

        self.app = create_react_agent(self.model, self.tools, prompt=str(prompt), checkpointer=MemorySaver())


    def get_prompt_text(self, file_name=PROMPT_FILE_DEFAULT):
        config_path = os.path.join(os.path.dirname(__file__), "config", file_name)
        with open(config_path, "r") as file:
            return file.read()
        

    def generate_response(self, message: str | list):
        # Use the agent
        if type(message) == str:
            message = [{"role": "user", "content": message}]
        final_state = self.app.invoke(
            {"messages": message},
            config={"configurable": {"thread_id": 12}}
        )
        response = final_state["messages"][-1].content

        return response