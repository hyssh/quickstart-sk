import os
import datetime
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("getDatetime")

@mcp.tool()
def get_local_time() -> str:
    """
    Get the current local time in ISO format.
    """
    return datetime.datetime.now().isoformat()


if __name__ == "__main__":
    print("*"*50)
    print("Starting MCP server")
    print("This server is responsible for getting local time.")
    print("Local time is based on the server's timezone settings.")
    print("*"*50)
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8087
    mcp.run(transport='streamable-http')