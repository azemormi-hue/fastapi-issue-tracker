"""Tests for the JSON file storage layer."""
import json

from app import storage


def test_load_data_returns_empty_list_when_file_missing(isolated_storage):
    assert not isolated_storage.exists()
    assert storage.load_data() == []


def test_load_data_returns_empty_list_for_whitespace_only_file(isolated_storage):
    isolated_storage.parent.mkdir(parents=True, exist_ok=True)
    isolated_storage.write_text("   \n\t  ")
    assert storage.load_data() == []


def test_load_data_returns_empty_list_for_empty_file(isolated_storage):
    isolated_storage.parent.mkdir(parents=True, exist_ok=True)
    isolated_storage.write_text("")
    assert storage.load_data() == []


def test_save_data_creates_directory_and_writes_json(isolated_storage):
    # The directory does not exist yet.
    assert not isolated_storage.parent.exists()
    payload = [{"id": "1", "title": "t", "description": "d"}]
    storage.save_data(payload)
    assert isolated_storage.exists()
    assert json.loads(isolated_storage.read_text()) == payload


def test_save_data_then_load_data_round_trip(isolated_storage):
    payload = [
        {"id": "1", "title": "first", "description": "first issue"},
        {"id": "2", "title": "second", "description": "second issue"},
    ]
    storage.save_data(payload)
    assert storage.load_data() == payload


def test_save_data_overwrites_existing_content(isolated_storage):
    storage.save_data([{"id": "1"}])
    storage.save_data([{"id": "2"}])
    assert storage.load_data() == [{"id": "2"}]
