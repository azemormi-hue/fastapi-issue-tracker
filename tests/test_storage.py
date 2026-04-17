"""Tests for the JSON file-backed storage in app/storage.py."""
import json

from app import storage


def test_load_returns_empty_list_when_file_missing(isolated_storage):
    assert not isolated_storage.exists()
    assert storage.load_data() == []


def test_load_returns_empty_list_when_file_empty(isolated_storage):
    isolated_storage.parent.mkdir(parents=True, exist_ok=True)
    isolated_storage.write_text("")
    assert storage.load_data() == []


def test_load_returns_empty_list_when_file_whitespace(isolated_storage):
    isolated_storage.parent.mkdir(parents=True, exist_ok=True)
    isolated_storage.write_text("   \n\t  ")
    assert storage.load_data() == []


def test_save_creates_directory_and_file(isolated_storage):
    assert not isolated_storage.parent.exists()
    storage.save_data([{"id": "1"}])
    assert isolated_storage.parent.is_dir()
    assert isolated_storage.is_file()


def test_save_then_load_round_trip(isolated_storage):
    payload = [
        {"id": "a", "title": "t1"},
        {"id": "b", "title": "t2"},
    ]
    storage.save_data(payload)
    assert storage.load_data() == payload


def test_save_overwrites_existing_file(isolated_storage):
    storage.save_data([{"id": "a"}])
    storage.save_data([{"id": "b"}])
    assert storage.load_data() == [{"id": "b"}]


def test_save_writes_indented_json(isolated_storage):
    storage.save_data([{"id": "a"}])
    raw = isolated_storage.read_text()
    # indent=2 means keys are indented with two spaces
    assert "\n  " in raw
    # And it must be valid JSON equal to what we saved
    assert json.loads(raw) == [{"id": "a"}]


def test_save_empty_list(isolated_storage):
    storage.save_data([])
    assert storage.load_data() == []
