import asyncio
import sys
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
from google import genai


load_dotenv()


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = genai.Client()

    async def connect_to_server(self, server_script_path: str) -> None:
        """Connect to an MCP server

        Args:
          server_script_path: Path to server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script must be .py or .js file")
        
        command = "python" if is_python else "node"

        server_params = StdioServerParameters(command=command, args=[server_script_path], env=None)

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))

        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

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
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path to server script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
