from typing import List
import os

from langchain_core.language_models import BaseChatModel
from langchain_core.tools.base import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_aws import ChatBedrock

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

import boto3

import logging

from agent.tools import (
    tool_local_ip,
    tool_aws_cli,
    tool_shell,
    tool_save_note,
    tool_remove_note,
    tool_set_working_dir,
    tool_add_task,
    tool_set_task_status,
    tool_clear_tasks,
    tool_set_goal,
    tool_open_file,
    tool_close_file
)

from agent.session_memory import SessionMemory
from agent.actor import get_actor

MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
PROMPT_FILE_DEFAULT = 'MAIN.txt'
#CHATGPT_MODEL = 'gpt-4o'
CHATGPT_MODEL = 'o3-mini'

MODEL_BOOST = {
    False: 'o3-mini',
    True: 'gpt-4o'
}

def get_llm_openai():
    from langchain_openai import ChatOpenAI
    client = ChatOpenAI( model=CHATGPT_MODEL, api_key=os.getenv("OPENAI_API_KEY"))
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
    app: {}

    def __init__(self, session_memory: SessionMemory = None):
        self.session_memory = session_memory

        self.actor = get_actor(session_memory.session_id)

        if not session_memory.get_working_dir():
            session_memory.set_working_dir(DEFAULT_WORKING_DIR)

        self.tools = [
            tool_local_ip,
            tool_set_working_dir,
            tool_aws_cli,
            tool_shell,
            tool_save_note,
            tool_remove_note,
            tool_add_task,
            tool_set_task_status,
            tool_clear_tasks,
            tool_set_goal,
            tool_open_file,
            tool_close_file
        ]
        self.model = get_llm()

        prompt = PromptTemplate.from_template(
            template=self.get_prompt_text()
        ).format(
            session_id=session_memory.session_id,
            working_dir=session_memory.get_working_dir(),
            goal=session_memory.get_goal(),
            tasks=session_memory.get_tasks(),
            notes_memory=session_memory.get_notes(),
            open_files=session_memory.get_open_files()
        )

        #checkpointer = MemorySaver()
        self.app = {}
        for key in MODEL_BOOST:
            logging.info(f">>> Creating agent for ({key}) {MODEL_BOOST[key]}")
            self.app[key] = create_react_agent(MODEL_BOOST[key], self.tools, prompt=str(prompt)) #, checkpointer=checkpointer)


    def get_prompt_text(self, file_name=PROMPT_FILE_DEFAULT):
        config_path = os.path.join(os.path.dirname(__file__), "config", file_name)
        with open(config_path, "r") as file:
            return file.read()
        

    def generate_response(self, message: str | list):
        # Use the agent
        if type(message) == str:
            message = [{"role": "user", "content": message}]

        logging.info(f">>> Generating response using {MODEL_BOOST[self.session_memory.get_boost_state()]}")
        final_state = self.app[self.session_memory.get_boost_state()].invoke(
            {"messages": message},
            config={
                "configurable": {"thread_id": self.session_memory.session_id},
                "recursion_limit": 100
                }
        )
        response = final_state["messages"][-1].content

        return response