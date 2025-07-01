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
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8087
    mcp.run(transport='sse')