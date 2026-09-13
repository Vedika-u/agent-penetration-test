from target_agent.tools.calculator import calculator


def test_basic_arithmetic():
    assert calculator.invoke({"expression": "12 * 7"}) == "84"


def test_parentheses_and_division():
    assert calculator.invoke({"expression": "(3 + 4) / 2"}) == "3.5"


def test_rejects_unsupported_expression():
    result = calculator.invoke({"expression": "__import__('os').system('echo hi')"})
    assert result.startswith("Error:")
