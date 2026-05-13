from core.llm import agenerate

SYSTEM = """
You are a planning agent.
Break the user goal into clear executable tasks.
If tasks can be performed in parallel, mark them with "parallel": true.
Return a JSON array of objects: [{"task": "...", "parallel": bool}].
"""

async def create_plan(task):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task}]
    response = await agenerate(messages)
    return response.content
