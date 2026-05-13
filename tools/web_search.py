from duckduckgo_search import DDGS

def search_web(query):
    output = []
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
        for r in results:
            output.append({"title": r["title"], "body": r["body"], "url": r["href"]})
    return output
