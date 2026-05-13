import os

MODEL = "gpt-4o"
MAX_AGENT_STEPS = 8
MEMORY_RESULTS = 5
MAX_MESSAGE_LENGTH = 4000

MCP_SERVERS = [
    {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    },
    {
        "name": "fetch",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
    },
]
