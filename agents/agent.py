from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from dotenv import load_dotenv
import os
from loguru import logger

load_dotenv()

@tool
def execute_code(code: str) -> str:
    """Выполняет Python код."""
    try:
        local = {}
        exec(code, {"__builtins__": {}}, local)
        return str(local.get('result', 'Выполнено успешно'))
    except Exception as e:
        return f"Ошибка: {str(e)}"

@tool
def list_files(directory: str = ".") -> str:
    """Список файлов в папке."""
    try:
        return "\n".join(os.listdir(directory))
    except Exception as e:
        return f"Ошибка: {str(e)}"

@tool
def read_file(filepath: str) -> str:
    """Читает файл."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()[:10000]
    except Exception as e:
        return f"Ошибка чтения: {str(e)}"

@tool
def write_file(filepath: str, content: str) -> str:
    """Записывает файл."""
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Файл {filepath} сохранён."
    except Exception as e:
        return f"Ошибка записи: {str(e)}"

tools = [
    DuckDuckGoSearchResults(num_results=7),
    execute_code,
    list_files,
    read_file,
    write_file,
]

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

agent_executor = create_react_agent(
    model=llm,
    tools=tools,
    state_modifier="Ты — полезный и точный Telegram AI-агент. Используй инструменты при необходимости."
)

async def run_agent(task: str, user_id: str = None) -> str:
    try:
        inputs = {"messages": [("user", task)]}
        final = ""
        async for chunk in agent_executor.astream(inputs, stream_mode="values"):
            if chunk.get("messages"):
                final = chunk["messages"][-1].content
        return final
    except Exception as e:
        logger.error(e)
        return f"Ошибка агента: {str(e)}"