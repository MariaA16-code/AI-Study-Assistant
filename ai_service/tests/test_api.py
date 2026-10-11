from ai_service import api


def test_process_and_delete_roundtrip(fresh_store, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text(
        "Chapter 1 Plants\n\nPlants make food using sunlight, water and carbon "
        "dioxide in their leaves every day.",
        encoding="utf-8",
    )
    result = api.process_document(7, str(f))
    assert result["status"] == "ready"
    assert result["chunks"] >= 1
    api.delete_document(7)
    assert fresh_store.get_all_chunks(7) == []


def test_missing_file_is_reported_not_raised(fresh_store, tmp_path):
    result = api.process_document(8, str(tmp_path / "missing.pdf"))
    assert result["status"] == "failed"
    assert result["warnings"]