from http import HTTPStatus
import uuid

from flask.testing import FlaskClient
from pytest_mock import MockType
import pytest

from routes import api
from routes.rent import rent_model

@pytest.fixture()
def client(mocker) -> FlaskClient:
    """
    Mocker of a client of our API.
    With this we can simulate requests to different api routes.
    """
    api.testing = True
    return api.test_client()

def test_get_rent(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `rent_model.get_all()`, `rent_model.get_by_id()`, or
    `rent_model.get_by_locker_id()` methods, they are replicated for the caller
    of GET on `/rent` route, without any parameter, with `id` parameter, and
    with `lockerId` parameter, respectively.
    """
    get_all_mock_return = (b"mock response for get_all", 200)
    get_by_id_mock_return = (b"mock response for get_by_id", 400)
    get_by_locker_id_mock_return = (b"mock response for get_by_locker_id", 404)

    mocker.patch.object(
        rent_model,
        "get_all",
        return_value=get_all_mock_return
    )
    mocker.patch.object(
        rent_model,
        "get_by_id",
        return_value=get_by_id_mock_return
    )
    mocker.patch.object(
        rent_model,
        "get_by_locker_id",
        return_value=get_by_locker_id_mock_return
    )

    res = client.get("/rent")
    assert res.data == get_all_mock_return[0]
    assert res.status_code == get_all_mock_return[1]

    mock_id = "mock-id"
    res = client.get(f"/rent?id={mock_id}")
    assert res.data == get_by_id_mock_return[0]
    assert res.status_code == get_by_id_mock_return[1]

    res = client.get(f"/rent?lockerId={mock_id}")
    assert res.data == get_by_locker_id_mock_return[0]
    assert res.status_code == get_by_locker_id_mock_return[1]

    res = client.get(f"/rent?id={mock_id}&lockerId={mock_id}")
    assert res.status_code == HTTPStatus.BAD_REQUEST

def test_create_rent(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that whatever response we get from
    `rent_model.create()` method, it is replicated for the caller of POST on
    `/rent` route.
    """
    mock_return = (b"mock response for create", 200)
    mocker.patch.object(rent_model, "create", return_value=mock_return)
    res = client.post("/rent", json={"fake parameter": "fake data"})

    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_delete_rent(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that we enforce `id` parameter to be part of
    the request, and whatever response we get from `rent_model.delete()` method,
    it is replicated for the caller of DELETE on `/rent` route.
    """
    mock_return = (b"mock response for delete", 200)
    mocker.patch.object(rent_model, "delete", return_value=mock_return)

    res = client.delete("/rent")
    assert res.status_code == HTTPStatus.BAD_REQUEST

    mock_id = "mock-id"

    res = client.delete(f"/rent?id={mock_id}")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_send_rent(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that we enforce `id` parameter to be part of
    the request, and whatever response we get from `rent_model.send()` method,
    it is replicated for the caller of PUT on `/rent/<uuid:rent_id>/send` route.
    """
    mock_return = (b"mock response for send", 200)
    mocker.patch.object(rent_model, "send", return_value=mock_return)
    mock_id = str(uuid.uuid1())

    res = client.put(f"/rent/{mock_id}/send")
    assert res.status_code == HTTPStatus.BAD_REQUEST


    res = client.put(f"/rent/{mock_id}/send?toLockerId={mock_id}")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_dropoff_rent(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that we enforce `id` parameter to be part of
    the request, and whatever response we get from `rent_model.dropoff()`
    method, it is replicated for the caller of PUT on
    `/rent/<uuid:rent_id>/dropoff` route.
    """
    mock_return = (b"mock response for dropoff", 200)
    mocker.patch.object(rent_model, "dropoff", return_value=mock_return)
    mock_id = str(uuid.uuid1())

    res = client.put(f"/rent/{mock_id}/dropoff")
    assert res.status_code == HTTPStatus.BAD_REQUEST


    res = client.put(f"/rent/{mock_id}/dropoff?toLockerId={mock_id}")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]

def test_pickup_rent(client: FlaskClient, mocker: MockType):
    """
    For this test we want to know that we enforce `id` parameter to be part of
    the request, and whatever response we get from `rent_model.pickup()` method,
    it is replicated for the caller of PUT on `/rent/<uuid:rent_id>/pickup`
    route.
    """
    mock_return = (b"mock response for pickup", 200)
    mocker.patch.object(rent_model, "pickup", return_value=mock_return)
    mock_id = str(uuid.uuid1())

    res = client.put(f"/rent/{mock_id}/pickup")
    assert res.status_code == HTTPStatus.BAD_REQUEST


    res = client.put(f"/rent/{mock_id}/pickup?fromLockerId={mock_id}")
    assert res.data == mock_return[0]
    assert res.status_code == mock_return[1]
