from hirewire.integrations.hhru.api.schemas.generics import ItemsResponse
from hirewire.integrations.hhru.api.schemas.resume import Resume


def test_generic_items_response():
    result = ItemsResponse[Resume].model_validate({"items": [{"id": "r1"}]})
    assert result.items == [Resume(id="r1")]
