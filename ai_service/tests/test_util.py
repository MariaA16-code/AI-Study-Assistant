from ai_service.util import extract_json


def test_plain_json_is_read():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_json_inside_a_markdown_fence_is_read():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_line_break_inside_a_long_answer_is_accepted():
    raw = '{"questions": [{"model_answer": "Line one.\nLine two."}]}'
    data = extract_json(raw)
    assert data["questions"][0]["model_answer"] == "Line one.\nLine two."


def test_broken_json_gives_none():
    assert extract_json('{"questions": [{"model_answer": "never ends') is None
    assert extract_json("no json here") is None