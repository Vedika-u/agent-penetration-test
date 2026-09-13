from target_agent.tools.web_search import web_search


def test_known_query_returns_fixture_result():
    result = web_search.invoke({"query": "tell me about langgraph"})
    assert "LangGraph" in result


def test_unknown_query_returns_no_results():
    result = web_search.invoke({"query": "asdkfjhaslkdjfhqwerty nonsense query"})
    assert "No results found" in result
