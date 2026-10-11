from ai_service.validate import validate_item

PASSAGE = (
    "Photosynthesis is the process by which green plants make their own food. "
    "Chlorophyll in the leaves absorbs sunlight, and the plant uses that energy to turn "
    "water and carbon dioxide into glucose and oxygen."
)


def good_mcq(**changes):
    item = {
        "question": "Which gas do plants take in for photosynthesis?",
        "options": ["Carbon dioxide", "Nitrogen", "Helium", "Methane"],
        "correct_index": 0,
        "explanation": "Plants turn water and carbon dioxide into glucose and oxygen.",
    }
    item.update(changes)
    return item


def test_good_mcq_passes():
    assert validate_item("mcq", good_mcq(), PASSAGE) is None


def test_mcq_needs_four_options():
    assert validate_item("mcq", good_mcq(options=["a", "b", "c"]), PASSAGE)


def test_mcq_duplicate_options():
    item = good_mcq(options=["Carbon dioxide", "carbon dioxide", "Helium", "Methane"])
    assert validate_item("mcq", item, PASSAGE) == "duplicate options"


def test_mcq_all_of_the_above():
    item = good_mcq(options=["Carbon dioxide", "Nitrogen", "Helium", "All of the above"])
    assert validate_item("mcq", item, PASSAGE) == "all/none of the above"


def test_mcq_bad_correct_index():
    for bad in (4, -1, True, "x", None):
        assert validate_item("mcq", good_mcq(correct_index=bad), PASSAGE) == "bad correct_index"


def test_question_must_not_mention_the_passage():
    item = good_mcq(question="According to the passage, which gas do plants take in?")
    assert validate_item("mcq", item, PASSAGE) == "mentions the passage"


def test_unsupported_answer_is_rejected():
    item = good_mcq(
        options=["Quantum entanglement of tachyons", "Nitrogen", "Helium", "Methane"],
        explanation="It is a famous physics result about tachyons.",
    )
    assert validate_item("mcq", item, PASSAGE) == "answer not supported by the passage"


def test_short_answer_ok_and_too_short():
    ok = {
        "question": "What do green plants make during photosynthesis?",
        "model_answer": "They make their own food in the form of glucose, using sunlight, water and carbon dioxide.",
    }
    assert validate_item("short", ok, PASSAGE) is None
    assert validate_item("short", {**ok, "model_answer": "Food."}, PASSAGE) == "answer length"


def test_long_answer_needs_real_length():
    item = {
        "question": "Explain how green plants make their own food.",
        "model_answer": "Plants make food using sunlight.",
    }
    assert validate_item("long", item, PASSAGE) == "answer length"


def test_unknown_type():
    assert validate_item("essay", {"question": "What is photosynthesis here?"}, PASSAGE) == "unknown type"