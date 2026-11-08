from unittest.mock import Mock

from hirewire.integrations.google.drive import list_files


def test_list_files_follows_pagination():
    first = {"files": [{"id": "one", "name": "One"}], "nextPageToken": "next"}
    second = {"files": [{"id": "two", "name": "Two"}]}
    execute = Mock(side_effect=[first, second])
    service = Mock()
    service.files.return_value.list.return_value.execute = execute
    result = list_files(folder_id="folder-id", service=service)
    assert [item["id"] for item in result] == ["one", "two"]
    assert service.files.return_value.list.call_count == 2
    assert (
        service.files.return_value.list.call_args_list[1].kwargs["pageToken"]
        == "next"
    )
