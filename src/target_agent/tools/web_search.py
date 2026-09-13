import json
from functools import lru_cache

from langchain_core.tools import tool

from target_agent.config import settings

_NO_RESULTS = [
    {
        "title": "No results found",
        "url": "",
        "snippet": "The search returned no matching results.",
    }
]


@lru_cache(maxsize=1)
def _load_fixtures(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def _format_results(results: list[dict]) -> str:
    lines = []
    for r in results:
        lines.append(f"- {r['title']} ({r['url']})\n  {r['snippet']}")
    return "\n".join(lines)


@tool
def web_search(query: str) -> str:
    """Search the web for information on a topic.

    Args:
        query: The search query.
    """
    fixtures = _load_fixtures(settings.search_fixtures_path)
    query_lower = query.lower()
    for entry in fixtures:
        if entry["query_contains"].lower() in query_lower:
            return _format_results(entry["results"])
    return _format_results(_NO_RESULTS)
