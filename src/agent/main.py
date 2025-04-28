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
logging.basicConfig(level=logging.INFO)

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
    tool_close_file,
    tool_write_file
)

from agent.session_memory import SessionMemory
from agent.actor import get_actor
from agent.llm_provider import LLMProvider


LLM_PROVIDER = 'bedrock'

PROMPT_FILE_DEFAULT = 'MAIN.txt'

# AWS_MODEL_NAME_DEFAULT = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
# #CHATGPT_MODEL = 'gpt-4o'
# CHATGPT_MODEL = 'o3-mini'

# MODEL_BOOST = {
#     False: 'o3-mini',
#     True: AWS_MODEL_NAME_DEFAULT #'gpt-4o'
# }

# def get_llm_openai():
#     from langchain_openai import ChatOpenAI
#     client = ChatOpenAI( model=CHATGPT_MODEL, api_key=os.getenv("OPENAI_API_KEY"))
#     # client.max_tokens = 120000
#     return client


# def get_llm_bedrock():
#     bedrock_client = boto3.client(
#         service_name="bedrock-runtime",
#         region_name="us-east-1",
#     )
#     bedrock_llm = ChatBedrock(
#         model=AWS_MODEL_NAME_DEFAULT,
#         client=bedrock_client,
#         model_kwargs={'temperature': 0}
#     )
#     return bedrock_llm

# def get_llm(provider: str):
#     if provider == 'bedrock':
#         return get_llm_bedrock()
#     else:
#         return get_llm_openai()

DEFAULT_WORKING_DIR = '/container/data'

class MainAgent:
    tools: List[BaseTool]
    model: BaseChatModel
    session_memory: SessionMemory
    app: dict = {}
    llmprovider: LLMProvider

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
            tool_close_file,
            tool_write_file
        ]

        #checkpointer = MemorySaver()
        # self.app = {}
        # for key in MODEL_BOOST:
        #     logging.info(f">>> Creating agent for ({key}) {MODEL_BOOST[key]}")
        #     self.app[key] = create_react_agent(MODEL_BOOST[key], self.tools, prompt=str(prompt)) #, checkpointer=checkpointer)


    def get_prompt_text(self, file_name=PROMPT_FILE_DEFAULT):
        config_path = os.path.join(os.path.dirname(__file__), "config", file_name)
        with open(config_path, "r") as file:
            return file.read()
        
    def get_open_files(self):
        working_dir = self.session_memory.get_working_dir()
        local_data_path = os.getenv('PROJECT_FOLDER')
        
        # Check if working_dir is None or empty
        if not working_dir:
            logging.warning("Working directory is None or empty")
            return []
        
        # Split path and handle the case where it might not have expected elements
        path_parts = working_dir.split("/")
        if len(path_parts) < 4:
            logging.warning(f"Unexpected working directory format: {working_dir}")
            return []
            
        file_path = path_parts[3:]
        if not file_path:
            logging.warning("No file path components after splitting")
            return []
        
        data_path = os.path.join(local_data_path, *file_path)
        logging.info(f">>> Local data path: {local_data_path}")
        logging.info(f">>> File path: {file_path}")
        logging.info(f">>> Full local file path: {data_path}")
        
        files = self.session_memory.get_open_files()
        result = []
        for f in files:
            try:
                with open(os.path.join(data_path, f["file_path"]), "r") as file:
                    result.append({
                        "file_path": f,
                        "data": file.read()
                    })
            except Exception as e:
                logging.error(f"Error reading file {f['file_path']}: {e}")
                self.session_memory.remove_open_file(f["file_path"])
                    
        return result

    async def generate_response(self, message: str | list):
        # Use the agent
        if type(message) == str:
            message = [{"role": "user", "content": message}]

        # logging.info(f">>> Generating response using {MODEL_BOOST[self.session_memory.get_boost_state()]}")
        # final_state = self.app[self.session_memory.get_boost_state()].invoke(
        #     {"messages": message},
        #     config={
        #         "configurable": {"thread_id": self.session_memory.session_id},
        #         "recursion_limit": 100
        #         }
        # )
        # response = final_state["messages"][-1].content


        prompt = PromptTemplate.from_template(
            template=self.get_prompt_text()
        ).format(
            session_id=self.session_memory.session_id,
            working_dir=self.session_memory.get_working_dir(),
            goal=self.session_memory.get_goal(),
            tasks=self.session_memory.get_tasks(),
            notes_memory=self.session_memory.get_notes(),
            open_files=self.get_open_files()
        )

        self.llmprovider = LLMProvider(self.session_memory, LLM_PROVIDER, prompt)

        response = await self.llmprovider.get_response(message)

        return response