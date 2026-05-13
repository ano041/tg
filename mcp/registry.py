from typing import Dict, List
from mcp.client import MCPServerConnection
from core.logging_config import logger
import asyncio

class MCPRegistry:
    def __init__(self):
        self.connections: Dict[str, MCPServerConnection] = {}

    async def load_servers(self, servers_config):
        for cfg in servers_config:
            name = cfg["name"]
            if name in self.connections:
                continue
            conn = MCPServerConnection(name, cfg["command"], cfg["args"])
            try:
                await asyncio.wait_for(conn.start(), timeout=15)
                self.connections[name] = conn
            except Exception as e:
                logger.error(f"Failed to start MCP server {name}: {e}")

    async def shutdown(self):
        for conn in self.connections.values():
            await conn.stop()

    async def get_all_tools(self) -> List[dict]:
        all_tools = []
        for name, conn in self.connections.items():
            try:
                tools = await conn.list_tools()
                for tool in tools.tools:
                    schema = {
                        "type": "function",
                        "function": {
                            "name": f"mcp_{name}__{tool.name}",
                            "description": tool.description or f"MCP tool {tool.name} from {name}",
                            "parameters": tool.inputSchema if tool.inputSchema else {"type": "object", "properties": {}}
                        }
                    }
                    all_tools.append(schema)
            except Exception as e:
                logger.error(f"Error listing tools from {name}: {e}")
        return all_tools

    async def execute_tool(self, full_name, arguments):
        parts = full_name.split("__", 1)
        if len(parts) != 2 or not parts[0].startswith("mcp_"):
            return f"Invalid MCP tool name: {full_name}"
        server_name = parts[0][4:]
        tool_name = parts[1]
        conn = self.connections.get(server_name)
        if not conn:
            return f"MCP server {server_name} not found"
        result = await conn.call_tool(tool_name, arguments)
        if hasattr(result, "content"):
            return "\n".join([c.text for c in result.content if hasattr(c, "text")])
        return str(result)

mcp_registry = MCPRegistry()