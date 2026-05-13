import datetime
import asyncio
from memory.vector_memory import get_learning_collection
from core.logging_config import logger

async def store_feedback(user_id, task, answer, rating, plan=None, comment=None):
    collection = await get_learning_collection()
    doc = f"TASK: {task}\nANSWER: {answer}"
    metadata = {
        "user_id": user_id,
        "rating": rating,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "plan": str(plan) if plan else "",
        "comment": comment or ""
    }
    doc_id = f"feedback_{user_id}_{abs(hash(task))}"
    await asyncio.to_thread(collection.add, documents=[doc], metadatas=[metadata], ids=[doc_id])
    logger.info(f"Feedback stored: {rating} from user {user_id}")

async def get_relevant_lessons(task, n=3, rating="negative"):
    collection = await get_learning_collection()
    if collection.count() == 0:
        return []
    try:
        result = await asyncio.to_thread(collection.query, query_texts=[task], n_results=n, where={"rating": rating})
    except Exception:
        result = await asyncio.to_thread(collection.query, query_texts=[task], n_results=n)
    docs = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    lessons = []
    for doc, meta in zip(docs, metadatas):
        lessons.append(f"Past issue ({meta.get('rating')}): {doc[:200]}")
    return lessons