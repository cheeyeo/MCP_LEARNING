import os
import asyncio
from google import genai
from mem0 import Memory
from mcp_client import MCPClient


system_prompt = "You are a helpful AI. Answer the question based on query and memories.\nUser Memories:\n{memories_str}"

system_prompt_v2 = """
You are a helpful AI. Answer the question based on the query and memories. Use the tools available when you need more information.
User Memories:
{memories_str}

Available tools:
{tools}
"""

async def chat_with_memories(client: genai.Client, mcp_client: MCPClient, memory: Memory, history: list[dict], user_id: str = 'default_user') -> list[dict]:
    query = history[-1]["parts"][0]["text"] 
    print(query)
    
    relevant_memories = memory.search(query=query, user_id=user_id, limit=5)
    print(relevant_memories)

    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])
    print(memories_str)

    tools = await mcp_client.get_tools()

    tool_names = "\n".join([f"- {tool.function_declarations[0].name}" for tool in tools])

    memory_system_prompt = system_prompt_v2.format(memories_str=memories_str, tools=tool_names)
    print(f"MEM SYSTEM PROMPT: {memory_system_prompt}")

    # TODO: since we are providing the list of tools here Gemini is unable to provide list of pools as it doesn't have the tool to provide that information i.e. query of 'where are the nearest swimming pools' fail with `cannot provide information about the nearest swimming pools as my capabilities are limited to providing current temperature information`
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

        #  In a real app, you would call your function here:
        tool_result = await mcp_client.session.call_tool(function_call.name, function_call.args)

        history.append({"role": "model", "parts": [{"text": tool_result.content[0].text}]})
    else:
        history.append({"role": "model", "parts": [{"text": response.text}]})

    # To create new memories from conversation we need to convert history to a list of messages
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": part["parts"][0]["text"]} for i, part in enumerate(history)]

    memory.add(messages, user_id=user_id)

    return history


async def main():
    client = genai.Client()

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

    mcp_client = MCPClient()
    
    try:
        await mcp_client.connect_to_http_server("http://localhost:8123/mcp")
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("Goodbye")
                break
            # print(history)
            history.append({"role": "user", "parts": [{"text": user_input}]})
            response = await chat_with_memories(client, mcp_client, memory, history)
            print(response[-1]["parts"][0]["text"])
    finally:
        await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
