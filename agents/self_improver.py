import json
import asyncio
from core.llm import agenerate
from memory.vector_memory import get_learning_collection
from core.logging_config import logger

SYSTEM_IMPROVER = """
You are a meta-agent that improves other agents.
Given a set of negative feedback examples and the current system prompt of a target agent,
suggest minimal, concrete changes to the prompt to avoid such mistakes in the future.
Output a JSON: {"new_prompt": "...", "changes_summary": "..."}
"""

async def generate_prompt_improvement(target_agent, current_prompt, sample_errors):
    if not sample_errors:
        return None
    errors_text = "\n".join(sample_errors[:5])
    messages = [
        {"role": "system", "content": SYSTEM_IMPROVER},
        {"role": "user", "content": f"Target agent: {target_agent}\nCurrent prompt:\n{current_prompt}\n\nRecent negative feedback:\n{errors_text}"}
    ]
    response = await agenerate(messages)
    try:
        improvement = json.loads(response.content)
        logger.info(f"Improvement suggested for {target_agent}: {improvement.get('changes_summary')}")
        return improvement
    except json.JSONDecodeError:
        logger.error("Failed to parse improvement suggestion")
        return None

async def maybe_improve_prompts():
    collection = await get_learning_collection()
    if collection.count() < 10:
        return

    results = await asyncio.to_thread(collection.get, where={"rating": "negative"}, limit=20)
    documents = results.get("documents", [])
    if not documents:
        return

    from agents.planner import SYSTEM as PLANNER_PROMPT
    from agents.executor import SYSTEM as EXECUTOR_PROMPT
    from agents.reflector import SYSTEM as REFLECTOR_PROMPT

    prompts = {"planner": PLANNER_PROMPT, "executor": EXECUTOR_PROMPT, "reflector": REFLECTOR_PROMPT}
    suggestions = {}
    for agent, prompt in prompts.items():
        suggestion = await generate_prompt_improvement(agent, prompt, documents)
        if suggestion:
            suggestions[agent] = suggestion

    if suggestions:
        from core.storage import storage
        await storage.save_pending_improvements(suggestions)
        logger.info(f"Stored {len(suggestions)} prompt improvement suggestions")
