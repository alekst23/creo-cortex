import pytest

from langchain_mcp_adapters.client import MultiServerMCPClient


@pytest.mark.asyncio
async def test_get_tools():
    """
    Test the get_tools function
    """
    async with MultiServerMCPClient(
        {
            "test": {
                "url": "http://localhost:8080/sse",
                "transport": "sse",
            }
        }
    ) as client:
        tools = client.get_tools()
        print (f"\n\n>>> Tools: {tools}")
        assert tools is not None
        assert type(tools) == list
        assert len(tools) > 0