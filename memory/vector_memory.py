import asyncio
import chromadb
from chromadb.config import Settings
from config import MEMORY_RESULTS
import os

CHROMA_DATA_PATH = os.path.join("data", "chroma_db")
os.makedirs(CHROMA_DATA_PATH, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_DATA_PATH, settings=Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(name="long_memory")
_learning_collection = None

async def get_learning_collection():
    global _learning_collection
    if _learning_collection is None:
        _learning_collection = await asyncio.to_thread(client.get_or_create_collection, name="learning_memory")
    return _learning_collection

async def store_memory(user_id, text):
    await asyncio.to_thread(collection.add, documents=[text], metadatas=[{"user_id": user_id}], ids=[f"{user_id}_{abs(hash(text))}"])

async def search_memory(query, n=MEMORY_RESULTS):
    if collection.count() == 0:
        return []
    result = await asyncio.to_thread(collection.query, query_texts=[query], n_results=min(n, collection.count()))
    return result.get("documents", [[]])[0]