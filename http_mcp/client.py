import argparse
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from dotenv import load_dotenv
from google import genai


load_dotenv()


class MCPClient:
    """MCP Client for interacting with MCP streamable HTTP server"""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = genai.Client()

    async def connect_to_streamable_http_server(self, server_url: str, headers: Optional[dict] = {}):
        self._streams_context = streamablehttp_client(
            url=server_url,
            headers=headers
        )

        read_stream, write_stream, _ = await self._streams_context.__aenter__()

        self._session_context = ClientSession(read_stream, write_stream)
        self.session: ClientSession = await self._session_context.__aenter__()

        await self.session.initialize()

        # list available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(tools)
        print("\nConnected to server with tools: ", [tool.name for tool in tools])
    
    async def process_query(self, query: str) -> str:
        """Process query using Gemini and available tools"""

        func_declarations: list[genai.types.FunctionDeclaration] = []

        response = await self.session.list_tools()
        for tool in response.tools:
            # convert each tool format into json function call format for gemini
            # https://ai.google.dev/gemini-api/docs/function-calling

            func1 = genai.types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters_json_schema={
                    "type": "object",
                    "properties": tool.inputSchema["properties"],
                    "required": tool.inputSchema["required"]
                }
            )

            func_declarations.append(func1)

        tools = genai.types.Tool(function_declarations=func_declarations)
        config = genai.types.GenerateContentConfig(
            tools=[tools], 
            temperature=0.0
        )

        contents = [
            genai.types.Content(role="user", parts=[genai.types.Part(text=query)])
        ]

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=config
        )

        final_text = []
        if response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call

            #  In a real app, you would call your function here:
            tool_result = await self.session.call_tool(function_call.name, function_call.args)
            final_text.append(f"Calling tool {function_call.name} with args {function_call.args}")

            # Create function response part
            func_resp_part = genai.types.Part.from_function_response(
                name=function_call.name,
                response={"result": tool_result.content[0].text}
            )

            # append function call and result of function execution to contents
            contents.append(response.candidates[0].content)
            contents.append(genai.types.Content(role="user", parts=[func_resp_part]))

            # Get next response from Gemini
            final_response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config
            )

            final_text.append(final_response.text)
        else:
            print("No function call found in the response.")
            final_text.append(response.text)

        return "\n".join(final_text)


    async def chat_loop(self):
        """Runs an interactive chat loop"""
        print("\nMCP Client started")
        print("Type query or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Cleanup session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


async def main():
    """Main function to run MCP client"""
    parser = argparse.ArgumentParser(description="Run MCP streamable http based client")
    parser.add_argument("--mcp-localhost-port", type=int, default=8123, help="localhost to bind to")
    args = parser.parse_args()

    client = MCPClient()

    try:
        await client.connect_to_streamable_http_server(
            f"http://localhost:{args.mcp_localhost_port}/mcp"
        )
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())