import asyncio
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.logging_config import logger

class MCPServerConnection:
    def __init__(self, name, command, args):
        self.name = name
        self.command = command
        self.args = args
        self.session = None
        self._process = None

    async def start(self):
        server_params = StdioServerParameters(command=self.command, args=self.args)
        self._process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self._read, self._write = await stdio_client(server_params, self._process)
        self.session = ClientSession(self._read, self._write)
        await self.session.initialize()
        logger.info(f"MCP server '{self.name}' connected")

    async def stop(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._process:
            self._process.terminate()

    async def list_tools(self):
        if not self.session:
            return []
        return await self.session.list_tools()

    async def call_tool(self, tool_name, arguments):
        if not self.session:
            raise RuntimeError("MCP session not initialized")
        return await self.session.call_tool(tool_name, arguments)