import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv
from google import genai


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_http_server(self, server_url: str, headers: Optional[dict] = {}):
        self._streams_context = streamablehttp_client(url=server_url, headers=headers)
        
        read_stream, write_stream, _ = await self._streams_context.__aenter__()
        
        self._session_context = ClientSession(read_stream, write_stream)
        self.session: ClientSession = await self._session_context.__aenter__()
        
        await self.session.initialize()

        # list available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(tools)
        print("\nConnected to server with tools: ", [tool.name for tool in tools])
    
    # TODO: Rewrite below to return list of genai.types.Tool one for each MCP tool returned....
    async def get_tools(self) -> list[genai.types.Tool]:
        tools: list[genai.types.Tool] = []

        response = await self.session.list_tools()

        # print(f"TOOL RESPONSE: {response}")
        for tool in response.tools:
            func1 = genai.types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters_json_schema={
                    "type": "object",
                    "properties": tool.inputSchema["properties"],
                    "required": tool.inputSchema["required"]
                }
            )

            tool = genai.types.Tool(function_declarations=[func1])
            tools.append(tool)

        return tools
    
    async def cleanup(self):
        """Cleanup session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)
