import json
from core.llm import agenerate_with_tools
from tools.function_schemas import AVAILABLE_TOOLS as STATIC_TOOLS
from tools.web_search import search_web
from tools.browser import browse_async
from mcp.registry import mcp_registry
import asyncio

SYSTEM = """
You are an execution agent.
Complete the given step using your knowledge and available tools.
Use search_web for fresh information, browse_web to read a webpage.
Always output a final answer in plain text.
"""

async def async_search_web(query):
    return await asyncio.to_thread(search_web, query)

TOOL_MAP_ASYNC = {
    "search_web": async_search_web,
    "browse_web": browse_async,
}

async def get_available_tools():
    mcp_tools = await mcp_registry.get_all_tools()
    return STATIC_TOOLS + mcp_tools

async def execute(step):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"TASK:\n{step}"}
    ]
    tools = await get_available_tools()
    max_tool_calls = 5

    for _ in range(max_tool_calls):
        response = await agenerate_with_tools(messages, tools)
        if response.tool_calls:
            messages.append(response)
            for tool_call in response.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                if func_name in TOOL_MAP_ASYNC:
                    tool_result = await TOOL_MAP_ASYNC[func_name](**func_args)
                    result_str = json.dumps(tool_result, ensure_ascii=False)
                elif func_name.startswith("mcp_"):
                    try:
                        tool_result = await mcp_registry.execute_tool(func_name, func_args)
                        result_str = str(tool_result)
                    except Exception as e:
                        result_str = f"Error executing MCP tool: {e}"
                else:
                    result_str = f"Error: unknown function {func_name}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str
                })
        else:
            return response.content
    return "Не удалось выполнить задачу за отведённое число вызовов инструментов."
