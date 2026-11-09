from unittest.mock import Mock

import pytest

from hirewire.integrations.google.drive import get_file, list_files


def test_list_files_follows_pagination():
    first = {"files": [{"id": "one", "name": "One"}], "nextPageToken": "next"}
    second = {"files": [{"id": "two", "name": "Two"}]}
    execute = Mock(side_effect=[first, second])
    service = Mock()
    service.files.return_value.list.return_value.execute = execute
    result = list_files(folder_id="folder-id", service=service)
    assert [item["id"] for item in result] == ["one", "two"]
    assert service.files.return_value.list.call_count == 2
    first_call, second_call = service.files.return_value.list.call_args_list
    assert (
        first_call.kwargs["q"] == "'folder-id' in parents and trashed = false"
    )
    assert first_call.kwargs["pageSize"] == 100
    assert second_call.kwargs["pageToken"] == "next"


def test_list_files_escapes_folder_id_for_drive_query():
    service = Mock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": []
    }
    list_files(folder_id="folder'\\id", service=service)
    query = service.files.return_value.list.call_args.kwargs["q"]
    assert query == "'folder\\'\\\\id' in parents and trashed = false"


def test_list_files_can_include_trashed_files():
    service = Mock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": []
    }
    list_files(include_trashed=True, service=service)
    assert service.files.return_value.list.call_args.kwargs["q"] is None


def test_list_files_rejects_invalid_page_size():
    with pytest.raises(ValueError, match="page_size"):
        list_files(page_size=0, service=Mock())


def test_get_file_rejects_empty_id():
    with pytest.raises(ValueError, match="file_id"):
        get_file("  ", service=Mock())
