import os
from google import genai
from mem0 import Memory


system_prompt = "You are a helpful AI. Answer the question based on query and memories."


def chat_with_memories(client: genai.Client, memory: Memory, history: list[dict], user_id: str = 'default_user') -> list[dict]:
    print(history[-1]["parts"][0]["text"])
    
    relevant_memories = memory.search(query=history[-1]["parts"][0]["text"], user_id=user_id, limit=5)
    print(relevant_memories)

    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])
    print(memories_str)

    memory_system_prompt = f"{system_prompt}\nUser Memories:\n{memories_str}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
        config={"system_instruction": memory_system_prompt}
    )

    history.append({"role": "model", "parts": [{"text": response.text}]})

    # To create new memories from conversation we need to convert history to a list of messages
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": part["parts"][0]["text"]} for i, part in enumerate(history)]

    memory.add(messages, user_id=user_id)

    return history


if __name__ == "__main__":
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

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("Goodbye")
        break
    # print(history)
    history.append({"role": "user", "parts": [{"text": user_input}]})
    response = chat_with_memories(client, memory, history)
    print(response[-1]["parts"][0]["text"])
