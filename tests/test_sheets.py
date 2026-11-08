from unittest.mock import Mock

import pytest

from hirewire.integrations.google.sheets import (append_values, read_values,
                                                 update_values)


def test_read_values_returns_empty_list_when_range_is_empty():
    execute = Mock(return_value={})
    service = Mock()
    service.spreadsheets.return_value.values.return_value.get.return_value.execute = (
        execute
    )
    result = read_values("spreadsheet-id", "Sheet1!A1:B2", service=service)
    assert result == []
    service.spreadsheets.return_value.values.return_value.get.assert_called_once()


def test_update_values_passes_rows_as_api_body():
    service = Mock()
    update_values(
        "spreadsheet-id",
        "Sheet1!A1:B1",
        [["Company", "Role"]],
        service=service,
    )
    kwargs = (
        service.spreadsheets.return_value.values.return_value.update.call_args.kwargs
    )
    assert kwargs["body"] == {"values": [["Company", "Role"]]}
    assert kwargs["valueInputOption"] == "USER_ENTERED"


def test_append_rejects_empty_values():
    with pytest.raises(ValueError, match="at least one row"):
        append_values("spreadsheet-id", "Sheet1", [], service=Mock())


def test_read_rejects_empty_spreadsheet_id():
    with pytest.raises(ValueError, match="spreadsheet_id"):
        read_values("", "Sheet1!A1", service=Mock())
