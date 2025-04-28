from mcp.server.fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool()
def test():
    return "Hello, world!"

@mcp.tool()
def test_name(name: str):
    return f"Hello, {name}!"

@mcp.tool()
def test_get_ip():
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return f"IP address: {ip_address}"

if __name__ == "__main__":
    print("\n\n>>> Starting FastMCP server...")
    mcp.settings.port = 8080
    mcp.run(transport="sse")