import os
import asyncio
from google import genai
from mem0 import Memory
from mcp_client import MCPClient


system_prompt_v2 = """
You are a helpful AI assistant. Answer the question based on the query and memories.

<MEMORIES>
Here is some information about the user:
{memories_str}
</MEMORIES>
"""

async def chat_with_memories(query: str, client: genai.Client, mcp_client: MCPClient, memory: Memory, history: list[genai.types.Content], user_id: str = 'default_user') -> list[genai.types.Content]:
    print(query)

    history.append(genai.types.Content(role="user", parts=[genai.types.Part(text=query)]))
    
    relevant_memories = memory.search(query=query, user_id=user_id)
    print(relevant_memories)

    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])
    print(memories_str)

    mcp_tools = await mcp_client.get_tools()

    google_maps_tool = genai.types.Tool(google_maps=genai.types.GoogleMaps())

    tools: list[genai.types.Tool] = [google_maps_tool, *mcp_tools]

    memory_system_prompt = system_prompt_v2.format(memories_str=memories_str)
    print(f"MEM SYSTEM PROMPT: {memory_system_prompt}")

    config = genai.types.GenerateContentConfig(
        tools=tools,
        temperature=0.0,
        system_instruction=memory_system_prompt
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
        config=config
    )

    # check if its a function call
    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        print(f"FUNCTION CALL: {function_call}")

        if function_call.name == "google_maps":
            tool_result = response.text
        else:
            tool_result = await mcp_client.session.call_tool(function_call.name, function_call.args)
            tool_result = tool_result.content[0].text

        # Create function response part
        func_resp_part = genai.types.Part.from_function_response(
            name=function_call.name,
            response={"result": tool_result}
        )
        #  add function call to history
        history.append(response.candidates[0].content)
        # add function resp to history
        history.append(genai.types.Content(role="user", parts=[func_resp_part]))

        final_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=history,
            config=config
        )
        history.append(genai.types.Content(role="model", parts=[genai.types.Part(text=final_response.text)]))
    else:
        history.append(genai.types.Content(role="model", parts=[genai.types.Part(text=response.text)]))

    # To create new memories from conversation we need to convert history to a list of messages
    messages: list[dict] = []
    for content in history:
        role = content.role
        if role == "model":
            role = "assistant"
        part = content.parts[0].text
        messages.append({"role": role, "content": part})
    memory.add(messages, user_id=user_id)

    return history


async def main():
    config = {
        "embedder": {
            "provider": "gemini",
            "config": {
                "model": "models/text-embedding-004",
            }
        },
        "llm": {
            "provider": "gemini",
            "config": {
                "model": "gemini-2.5-flash",
                "temperature": 0.0,
                "max_tokens": 2000,
            }
        },
        "vector_store": {
            "config": {
                "embedding_model_dims": 768, # needed to match the embedding output shape from gemini text-embedding-004 model
            }
        }
    }


    memory = Memory.from_config(config)
    # print(memory)

    print("Chatting with Gemini ( type 'exit' to quit )")
    history = []

    client = genai.Client()
    mcp_client = MCPClient()
    
    try:
        await mcp_client.connect_to_http_server("http://localhost:8123/mcp")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye")
                break

            response = await chat_with_memories(user_input, client, mcp_client, memory, history, 'chee')
            print(response[-1].parts[0].text)
    finally:
        await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
