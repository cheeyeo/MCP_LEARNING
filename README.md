### MCP example

Building MCP clients and servers

Adopting the official MCP weather example to use Gemini model instead...

Explores 2 different MCP transport modes:

* STDIO / local
* HTTP / SSE 


#### Build

Uses `uv` to manage venvs and dependencies:
```
uv init --python 3.13.3 # creates .python-version and pyproject.toml

uv venv # creates .venv

source .venv/bin/activate

uv add "mcp[cli]" httpx google-genai uvicorn
```

To use MCP inspector via uv for stdio example:
```
uv run mcp dev stdio_mcp/weather.py

or 

npx @modelcontextprotocol/inspector uv --directory ./stdio_mcp "run" "weather.py"
```


Run stdio client:
```
uv run stdio_mcp/client.py stdio_mcp/weather.py
```

Run HTTP MCP in separate terminals:
```
uv run http_mcp/server.py --port 8123
```

```
uv run http_mcp/client.py
```

NOTE: Both examples require a .env file with the gemini api key:
```
GEMINI_API_KEY=XXXXX
```

### TODO

* Learn about OAuth in MCP
* Learn about writing tests for MCP servers


### References

https://builder.aws.com/content/301AFBdz2tMxoTTpsRCZj4QyY6u/how-to-setup-mcp-with-uv-in-python-the-right-way

https://realpython.com/python-mcp/


( example using HTTP with SSE )
https://github.com/invariantlabs-ai/mcp-streamable-http/tree/main/python-example

( example using sse )
https://github.com/sidharthrajaram/mcp-sse?tab=readme-ov-file