import argparse
from typing import Any
import httpx
import uvicorn
from mcp.server.fastmcp import FastMCP


mcp = FastMCP(name="weather", json_response=False, stateless_http=False)


# Define the function with type hints and docstring
async def get_current_temperature(location: str) -> dict:
    """Gets the current temperature for a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA

    Returns:
        A dictionary containing the temperature and unit.
    """

    # TODO: Make actual API call
    temperature = 25
    tempUnit = "Celsius"
    return {"temperature": temperature, "units": tempUnit}


@mcp.tool()
async def current_temperature(location: str) -> dict:
    data = await get_current_temperature(location)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MCP streamable HTTP based server")
    parser.add_argument("--port", type=int, default=8123)
    args = parser.parse_args()

    uvicorn.run(mcp.streamable_http_app(), host="localhost", port=args.port)
