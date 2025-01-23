from http import HTTPStatus
import uuid

from flask.testing import FlaskClient
from pytest_mock import MockType
import pytest

from routes import api
from routes.locker import locker_model

@pytest.fixture()
def client(mocker) -> FlaskClient:
    """
    Mocker of a client of our API.
    With this we can simulate requests to different api routes.
    """
    api.testing = True
    return api.test_client()

def test_get_locker(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `locker_model.get_all()`, `locker_model.get_by_id()`, or
    `locker_model.get_by_bloq_id()` methods, they are replicated for the caller
    of GET on `/locker` route, without any parameter, with `id` parameter, and
    with `bloqId` parameter, respectively.
    """
    get_all_mock_return = (b"mock response for get_all", 200)
    get_by_id_mock_return = (b"mock response for get_by_id", 400)
    get_by_bloq_id_mock_return = (b"mock response for get_by_bloq_id", 404)

    mocker.patch.object(
        locker_model,
        "get_all",
        return_value=get_all_mock_return
    )
    mocker.patch.object(
        locker_model,
        "get_by_id",
        return_value=get_by_id_mock_return
    )
    mocker.patch.object(
        locker_model,
        "get_by_bloq_id",
        return_value=get_by_bloq_id_mock_return
    )

    res = client.get("/locker")
    assert res.data == get_all_mock_return[0]
    assert res.status_code == get_all_mock_return[1]

    mock_id = "mock-id"
    res = client.get(f"/locker?id={mock_id}")
    assert res.data == get_by_id_mock_return[0]
    assert res.status_code == get_by_id_mock_return[1]

    res = client.get(f"/locker?bloqId={mock_id}")
    assert res.data == get_by_bloq_id_mock_return[0]
    assert res.status_code == get_by_bloq_id_mock_return[1]

    res = client.get(f"/locker?id={mock_id}&bloqId={mock_id}")
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_create_locker(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `locker_model.create()` method, it is replicated for the caller of POST on
    `/locker` route.
    """
    mock_return = (b"mock response for create", 200)
    mocker.patch.object(locker_model, "create", return_value=mock_return)
    res = client.post("/locker", json={"fake parameter": "fake data"})

    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_open_locker(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `locker_model.open()` method, it is replicated for the caller of PUT on
    `/locker/<locker_id>/open` route.
    """
    mock_return = (b"mock response for open", 200)
    mocker.patch.object(locker_model, "open", return_value=mock_return)
    mock_id = str(uuid.uuid1())

    res = client.put(f"/locker/{mock_id}/open")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_close_locker(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `locker_model.close()` method, it is replicated for the caller of PUT on
    `/locker/<locker_id>/close` route.
    """
    mock_return = (b"mock response for close", 200)
    mocker.patch.object(locker_model, "close", return_value=mock_return)
    mock_id = str(uuid.uuid1())

    res = client.put(f"/locker/{mock_id}/close")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_delete_locker(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that we enforce `id` parameter to be part of
    the request, and whatever response we get from `locker_model.delete()` method,
    it is replicated for the caller of DELETE on `/locker` route.
    """
    mock_return = (b"mock response for delete", 200)
    mocker.patch.object(locker_model, "delete", return_value=mock_return)

    res = client.delete("/locker")
    assert res.status_code == HTTPStatus.BAD_REQUEST

    mock_id = "mock-id"

    res = client.delete(f"/locker?id={mock_id}")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]
