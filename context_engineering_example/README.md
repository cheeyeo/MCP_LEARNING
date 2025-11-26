### Context Engineering

Based on article on LangChain blog about building dynamic contexts for agents rather than using static prompts

Components of context engineering:
* Tool use, function calling
* Short term memory ( current history )
* Long term memory ( mem0 )
* Retrieval ( fetching info dynamically - RAG ? )


Context engineering is:

* A system, not just a text prompt
  its the output of a system that runs before the main LLM call

* Dynamic
  Created on the fly, tailored to the immediate task

* About using the right information and tools at the right time
  Ensure model isn't missing crucial information
  providing both knowledge ( information ) and capabilities ( tools ) only when required and helpful

* Where the format matters
  how information is presented matters
  a concise summary is better than a raw data dump
  a clear tool schema is better than a vague instruction


#### Tool use in Gemini

When defining tools using `tools` parameter in `generate_content` the model scopes all responses to using only the tools passed to it. 





#### On Mem0

mem0 has 2 versions:
* self-hosted ( open source )
* runs on their platform which needs a subscription

For self-hosted, use the `Memory` client and provide a config of LLM, embedding models etc to use

For subscription model, use the `MemoryClient` class and provide an API Key in the constructor. Note that for the free tier you only get 10,000 messages?

By default, memo0 stores history in ~/.mem0/history and creates a temp qdrant database under /tmp/qdrant


Sometimes the short term conversation is not stored in memory as the facts has to be about the user i.e. if the query provided is `I live in XXX` or `I like xxx` that gets stored but other than that its not stored. The query stored has to be about the user himself... ( preferences etc )



### REF

https://www.philschmid.de/context-engineering

https://blog.langchain.com/the-rise-of-context-engineering/

https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md

https://simonwillison.net/2025/Jun/27/context-engineering/

https://rlancemartin.github.io/2025/06/23/context_engineering/

https://docs.mem0.ai/open-source/overview

https://www.philschmid.de/gemini-with-memory

https://github.com/philschmid/gemini-samples/tree/main

https://github.com/philschmid/gemini-samples/blob/main/guides/gemini-with-memory.ipynb

https://medium.com/google-cloud/model-context-protocol-mcp-with-google-gemini-llm-a-deep-dive-full-code-ea16e3fac9a3