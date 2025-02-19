from langchain_core.messages.tool import ToolCall, ToolMessage

from agent.tools import(
    tool_local_ip,
    tool_aws_cli
)


def test_tool_local_ip():
    response = tool_local_ip.invoke(None)
    assert response is not None
    assert type(response) == str
    assert "Host info" in response

def test_tool_aws_cli():
    tool_call = ToolCall(
        name="tool_aws_cli",
        args={"param_string": "--version"},
        id="123",
        type="tool_call"
    )
    result: ToolMessage = tool_aws_cli.invoke(tool_call)
    assert result is not None
    assert type(result) is ToolMessage
    content = result.content
    assert content is not None
    assert type(content) == str
    assert "aws-cli" in content