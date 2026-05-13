SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Выполняет поиск в интернете и возвращает результаты",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос"}
            },
            "required": ["query"]
        }
    }
}

BROWSE_TOOL = {
    "type": "function",
    "function": {
        "name": "browse_web",
        "description": "Открывает веб-страницу и возвращает текстовое содержимое",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL страницы"}
            },
            "required": ["url"]
        }
    }
}

AVAILABLE_TOOLS = [SEARCH_TOOL, BROWSE_TOOL]