from core.llm import agenerate

SYSTEM = """
You are a reflection agent.
Check: reasoning quality, hallucinations, missing information, weak logic.
Improve the answer.
"""

async def reflect(task, answer):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"TASK:\n{task}\nANSWER:\n{answer}"}
    ]
    response = await agenerate(messages)
    return response.content
