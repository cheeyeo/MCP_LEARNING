### Context Engineering

Based on article on LangChain blog about building dynamic contexts for agents rather than using static prompts

Components of context engineering:
* Tool use, function calling
* Short term memory ( current history )
* Long term memory ( mem0 )
* Retrieval ( fetching info dynamically - RAG ? )


#### On Mem0

mem0 has 2 versions:
* self-hosted ( open source )
* runs on their platform which needs a subscription

For self-hosted, use the `Memory` client and provide a config of LLM, embedding models etc to use

For subscription model, use the `MemoryClient` class and provide an API Key in the constructor. Note that for the free tier you only get 10,000 messages?

By default, memo0 stores history in ~/.mem0/history and creates a temp qdrant database under /tmp/qdrant


### REF

https://docs.mem0.ai/open-source/overview

https://www.philschmid.de/gemini-with-memory

https://github.com/philschmid/gemini-samples/tree/main