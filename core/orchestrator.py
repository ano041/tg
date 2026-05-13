import json
import asyncio
import re
from agents.planner import create_plan
from agents.executor import execute
from agents.reflector import reflect
from memory.vector_memory import search_memory, store_memory
from config import MAX_AGENT_STEPS
from core.logging_config import logger
from core.feedback import get_relevant_lessons

def _parse_plan(raw_plan, fallback_task):
    code_block = re.search(r"```json\s*(.*?)\s*```", raw_plan, re.DOTALL)
    if code_block:
        raw_plan = code_block.group(1)
    try:
        plan = json.loads(raw_plan)
        if isinstance(plan, list):
            tasks = []
            for step in plan:
                if isinstance(step, dict):
                    tasks.append(step)
                elif isinstance(step, str):
                    tasks.append({"task": step, "parallel": False})
            return [(s["task"], s.get("parallel", False)) for s in tasks if s.get("task")]
    except json.JSONDecodeError:
        pass
    lines = [line.strip("- ").strip() for line in raw_plan.splitlines() if line.strip()]
    if lines and len(lines) > 1:
        return [(line, False) for line in lines]
    return [(fallback_task, False)]

async def run_agent(user_id, task):
    logger.info(f"Async orchestrator starting for {user_id}: {task[:100]}")
    memories = await search_memory(task)
    memory_context = "\n".join(memories) if memories else "No relevant memories."
    negative_lessons = await get_relevant_lessons(task, rating="negative")
    lesson_context = "\n".join(negative_lessons) if negative_lessons else "No relevant past issues."

    plan_raw = await create_plan(
        f"TASK:\n{task}\n\nPAST MISTAKES TO AVOID:\n{lesson_context}\n\nMEMORY:\n{memory_context}"
    )
    plan = _parse_plan(plan_raw, task)
    logger.info(f"Plan: {plan}")

    outputs = []
    step_index = 0

    async def process_step(step_text):
        nonlocal step_index
        idx = step_index
        step_index += 1
        logger.debug(f"Executing step {idx}: {step_text}")
        result = await execute(step_text)
        improved = await reflect(step_text, result)
        return idx, f"STEP: {step_text}\n\n{improved}"

    i = 0
    while i < len(plan):
        step_text, parallel = plan[i]
        if parallel and i + 1 < len(plan) and plan[i+1][1]:
            group = []
            while i < len(plan) and plan[i][1]:
                group.append(plan[i][0])
                i += 1
            tasks = [process_step(s) for s in group]
            results = await asyncio.gather(*tasks)
            outputs.extend([r[1] for r in sorted(results, key=lambda x: x[0])])
        else:
            _, out = await process_step(step_text)
            outputs.append(out)
            i += 1

    final_output = "\n\n".join(outputs)
    await store_memory(user_id, f"TASK: {task}\nRESULT:\n{final_output}")
    logger.info(f"Async orchestrator finished for {user_id}, output length={len(final_output)}")
    return final_output
