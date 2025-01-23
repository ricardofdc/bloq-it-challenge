from http import HTTPStatus

from flask.testing import FlaskClient
from pytest_mock import MockType
import pytest

from routes import api
from routes.bloq import bloq_model

@pytest.fixture()
def client(mocker) -> FlaskClient:
    """
    Mocker of a client of our API.
    With this we can simulate requests to different api routes.
    """
    api.testing = True
    return api.test_client()

def test_get_bloq(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `bloq_model.get_all()` or `bloq_model.get_by_id()` methods, they are
    replicated for the caller of GET on `/bloq` route, without and with `id`
    parameter, respectively.
    """
    get_all_mock_return = (b"mock response for get_all", 200)
    get_by_id_mock_return = (b"mock response for get_by_id", 400)

    mocker.patch.object(
        bloq_model,
        "get_all",
        return_value=get_all_mock_return
    )
    mocker.patch.object(
        bloq_model,
        "get_by_id",
        return_value=get_by_id_mock_return
    )

    res = client.get("/bloq")
    assert res.data == get_all_mock_return[0]
    assert res.status_code == get_all_mock_return[1]

    mock_id = "mock-id"
    res = client.get(f"/bloq?id={mock_id}")
    assert res.data == get_by_id_mock_return[0]
    assert res.status_code == get_by_id_mock_return[1]

def test_create_bloq(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `bloq_model.create()` method, it is replicated for the caller of POST on
    `/bloq` route.
    """
    mock_return = (b"mock response for create", 200)
    mocker.patch.object(bloq_model, "create", return_value=mock_return)

    res = client.post("/bloq", json={"fake parameter": "fake data"})
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_update_bloq(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `bloq_model.update()` method, it is replicated for the caller of PUT on
    `/bloq` route.
    """
    mock_return = (b"mock response for update", 200)
    mocker.patch.object(bloq_model, "update", return_value=mock_return)

    res = client.put("/bloq", json={"fake parameter": "fake data"})
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_delete_bloq(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that we enforce `id` parameter to be part of
    the request, and whatever response we get from `bloq_model.delete()` method,
    it is replicated for the caller of DELETE on `/bloq` route.
    """
    mock_return = (b"mock response for delete", 200)
    mocker.patch.object(bloq_model, "delete", return_value=mock_return)

    res = client.delete("/bloq")
    assert res.status_code == HTTPStatus.BAD_REQUEST

    mock_id = "mock-id"

    res = client.delete(f"/bloq?id={mock_id}")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]
