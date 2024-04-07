import pytest


@pytest.mark.parametrize(
    "json_body_to_validate, response",
    [
        ("valid_semantic_validation_body", "valid_semantic_validation_response"),
        ("invalid_semantic_validation_body", "invalid_semantic_validation_response"),
    ],
)
def test_semantic_validate_api(client, request, json_body_to_validate, response):
    """
    Test semantic validation API with valid and invalid JSON
    """
    json_body = request.getfixturevalue(json_body_to_validate)
    expected_response = request.getfixturevalue(response)
    res = client.post("/ska-ost-osd/api/v1/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


def test_semantic_validate_api_not_passing_required_keys(
    client, observing_command_input_missing_response, valid_semantic_validation_body
):
    """
    Test semantic validation API response with missing input observing_command_input key
    """
    json_body = valid_semantic_validation_body.copy()
    del json_body["observing_command_input"]
    expected_response = observing_command_input_missing_response
    res = client.post("/ska-ost-osd/api/v1/semantic_validation", json=json_body)
    assert res.get_json() == expected_response


@pytest.mark.parametrize(
    "json_body_to_validate, response, key_to_delete",
    [
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "sources",
        ),
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "interface",
        ),
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "raise_semantic",
        ),
        (
            "valid_semantic_validation_body",
            "valid_semantic_validation_response",
            "osd_data",
        ),
    ],
)
def test_not_passing_optional_keys(
    request, client, json_body_to_validate, response, key_to_delete
):
    """
    Test semantic validation API response by not passing optional keys
    """
    json_body = request.getfixturevalue(json_body_to_validate).copy()
    del json_body[key_to_delete]
    expected_response = request.getfixturevalue(response)
    res = client.post("/ska-ost-osd/api/v1/semantic_validation", json=json_body)
    assert res.get_json() == expected_response
