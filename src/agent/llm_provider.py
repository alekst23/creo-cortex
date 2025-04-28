from langchain_aws import ChatBedrock
import boto3
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from agent.session_memory import SessionMemory

from logging import getLogger
logger = getLogger(__name__)

MODEL_BOOST_MAP = {
    'bedrock': {
        False: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
        True: 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
    },
    'openai': {
        False: 'o3-mini',
        True: 'gpt-4o'
    }
}

def get_llm_openai(model_name):
    from langchain_openai import ChatOpenAI
    client = ChatOpenAI( model=model_name, api_key=os.getenv("OPENAI_API_KEY"))
    # client.max_tokens = 120000
    return client

def get_llm_bedrock(model_name):
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    bedrock_llm = ChatBedrock(
        model=model_name,
        client=bedrock_client,
        model_kwargs={'temperature': 0}
    )
    return bedrock_llm

def get_llm(provider: str, boost: bool):
    model_name = MODEL_BOOST_MAP[provider][boost]
    if provider == 'bedrock':
        return get_llm_bedrock(model_name)
    else:
        return get_llm_openai(model_name)
    

class LLMProvider:
    def __init__(self, session_memory: SessionMemory, provider: str, prompt: str):
        """
        :param session_memory: SessionMemory
        :param provider: str - 'openai' or 'bedrock'
        """
        self.provider_name = provider
        self.mem = session_memory
        self.prompt = str(prompt)

    async def get_response(self, message: str | list) -> str:
        async with MultiServerMCPClient(
            {
                "test": {
                    "url": "http://localhost:8080/sse",
                    "transport": "sse",
                }
            }
        ) as client:
            model = get_llm(self.provider_name, self.mem.get_boost_state())
            tools = client.get_tools()
            agent = create_react_agent(model, tools, prompt=self.prompt)
            response = await agent.ainvoke(
                {"messages": message},
                config={
                    "configurable": {"thread_id": self.mem.session_id},
                    "recursion_limit": 100
                }
            )
            return response["messages"][-1].content

    def get_model_name(self):
        return MODEL_BOOST_MAP[self.provider_name][self.mem.get_boost_state()]
    
        
