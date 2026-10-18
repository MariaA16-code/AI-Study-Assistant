import json
import re


def extract_json(raw: str) -> dict | None:
    """Return the first JSON object found in a model reply, or None."""
    text = re.sub(r"```(?:json)?", "", raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
       data = json.loads(text[start : end + 1], strict=False)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None