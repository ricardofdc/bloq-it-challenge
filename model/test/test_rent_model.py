from http import HTTPStatus
import shutil
import uuid

import pytest

from data.database import PotatoDatabase
from model.rent import RentModel, RentStatus

@pytest.fixture
def database(tmp_path):
    """
    Creates a PotatoDB instance based on a temporary copy of json files under
    `model/test/data` folder.
    """
    shutil.copyfile("model/test/data/bloqs.json", tmp_path / "bloqs.json")
    shutil.copyfile("model/test/data/lockers.json", tmp_path / "lockers.json")
    shutil.copyfile("model/test/data/rents.json", tmp_path / "rents.json")
    return PotatoDatabase(tmp_path)

@pytest.fixture
def model(database):
    """
    Creates a RentModel instance based on the temporary PotatoDB created before.
    This is used to test the integration between our model and our database.
    """
    return RentModel(database)


def test_get_all(model):
    """
    Test the number of returned rents, their size and the return code.
    """
    all_rents, code = model.get_all()
    assert code == HTTPStatus.OK
    assert len(all_rents) == 4
    for rent in all_rents:
        assert len(rent) == 5

def test_get_by_id(model):
    """
    Test the `get_by_id` model method in 2 scenarios:
        - `rent_id` exists
        - `rent_id` does not exist
    """
    rent_id = "40efc6fd-f10c-4561-88bf-be916613377c"
    expected = {
        "id": rent_id,
        "lockerId": "1b8d1e89-2514-4d91-b813-044bf0ce8d20",
        "weight": 7,
        "size": "L",
        "status": "WAITING_PICKUP"
    }

    ([rent], code) = model.get_by_id(rent_id)
    assert code == HTTPStatus.OK
    assert rent == expected

    locker_id = "wrong_id"
    ([], code) = model.get_by_id(locker_id)
    assert code == HTTPStatus.NOT_FOUND

def test_get_by_locker_id(model):
    """
    Test the `get_by_locker_id` model method in 3 scenarios:
        - id is `None`
        - id is not `None` and exists
        - id is not `None` and does not exist
    """
    locker_id = None
    expected = {
        "id": "50be06a8-1dec-4b18-a23c-e98588207752",
        "lockerId": None,
        "weight": 5,
        "size": "M",
        "status": "CREATED"
    }
    [rent], code = model.get_by_locker_id(locker_id)
    assert code == HTTPStatus.OK
    assert rent == expected

    locker_id = "6b33b2d1-af38-4b60-a3c5-53a69f70a351"
    expected = [
        {
            "id": "84ba232e-ce23-4d8f-ae26-68616600df48",
            "lockerId": "6b33b2d1-af38-4b60-a3c5-53a69f70a351",
            "weight": 10,
            "size": "XL",
            "status": "WAITING_DROPOFF"
        },
        {
            "id": "feb72a9a-258d-49c9-92de-f90b1f11984d",
            "lockerId": "6b33b2d1-af38-4b60-a3c5-53a69f70a351",
            "weight": 30,
            "size": "XL",
            "status": "DELIVERED"
        }
    ]
    rents_list, code = model.get_by_locker_id(locker_id)
    assert code == HTTPStatus.OK
    assert rents_list == expected

    locker_id = "wrong_id"
    ([], code) = model.get_by_locker_id(locker_id)
    assert code == HTTPStatus.NOT_FOUND

def test_create(model):
    """
    Test the `create` model method in 6 scenarios:
        - dict contains `id`
        - dict contains `lockerId`
        - dict contains `status`
        - dict contains extra parameter
        - dict `size` is not allowed ("XXL")
        - dict is correct
    """
    rent_with_id = {
        "id": str(uuid.uuid1()),
        "weight": 7,
        "size": "L"
    }
    rent_with_locker_id = {
        "lockerId": str(uuid.uuid1()),
        "weight": 7,
        "size": "L",
    }
    rent_with_status = {
        "weight": 7,
        "size": "L",
        "status": "CREATED"
    }
    rent_with_wrong_parameter = {
        "weight": 7,
        "size": "L",
        "wrong": "test"
    }

    rent_with_wrong_size = {
        "weight": 7,
        "size": "XXL"
    }

    (_, code) = model.create(rent_with_id)
    assert code == HTTPStatus.BAD_REQUEST

    (_, code) = model.create(rent_with_locker_id)
    assert code == HTTPStatus.BAD_REQUEST

    (_, code) = model.create(rent_with_status)
    assert code == HTTPStatus.BAD_REQUEST

    (_, code) = model.create(rent_with_wrong_parameter)
    assert code == HTTPStatus.BAD_REQUEST

    (_, code) = model.create(rent_with_wrong_size)
    assert code == HTTPStatus.BAD_REQUEST

    rent_correct_info = {
        "weight": 7,
        "size": "L"
    }

    # send copy so that it does not change original dict
    res, code = model.create(rent_correct_info.copy())

    # Add default information to our rent object
    assert code == HTTPStatus.CREATED
    rent_correct_info["id"] = res["id"]
    rent_correct_info["lockerId"] = None
    rent_correct_info["status"] = "CREATED"
    assert res == rent_correct_info

def test_delete(model):
    """
    Test the `delete` model method in 2 scenarios:
        - `rent_id` does not exist
        - `rent_id` exists
    """
    rent_id = "wrong_id"
    (_, code) = model.delete(rent_id)
    assert code == HTTPStatus.NOT_FOUND

    rent_id = "84ba232e-ce23-4d8f-ae26-68616600df48"
    (_, code) = model.delete(rent_id)
    assert code == HTTPStatus.OK
    assert len(model.db.db.tables["rents"]) == 3

def test_send(model):
    """
    Test the `send` model method in 6 scenarios:
        - wrong `rent_id` and wrong `locker_id`
        - wrong `rent_id` and correct `locker_id`
        - correct `rent_id` and wrong `locker_id`
        - `rent_id` of a DELIVERED rent
        - `locker_id` of a occupied
        - correct `rent_id` and correct `locker_id`
    """
    created_rent_id = "50be06a8-1dec-4b18-a23c-e98588207752"
    delivered_rent_id = "feb72a9a-258d-49c9-92de-f90b1f11984d"

    free_locker_id = "ea6db2f6-2da7-42ed-9619-d40d718b7bec"
    occupied_locker_id = "6b33b2d1-af38-4b60-a3c5-53a69f70a351"

    wrong_rent_id = "wrong_rent_id"
    wrong_locker_id = "wrong_locker_id"

    (_, code) = model.send(wrong_rent_id, wrong_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.send(wrong_rent_id, free_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.send(created_rent_id, wrong_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.send(delivered_rent_id, free_locker_id)
    assert code == HTTPStatus.CONFLICT

    (_, code) = model.send(created_rent_id, occupied_locker_id)
    assert code == HTTPStatus.CONFLICT

    (_, code) = model.send(created_rent_id, free_locker_id)
    assert code == HTTPStatus.OK

    # check if the values were correctly updated
    ([rent], _) = model.get_by_id(created_rent_id)
    assert rent["status"] == RentStatus.WAITING_DROPOFF.value
    assert rent["lockerId"] == free_locker_id
    [locker] = model.db.db.query(
        "lockers",
        lambda locker: locker["id"] == free_locker_id
    )
    assert locker["isOccupied"] is True

def test_dropoff(model):
    """
    Test the `dropoff` model method in 7 scenarios:
        - wrong `rent_id` and wrong `locker_id`
        - wrong `rent_id` and correct `locker_id`
        - correct `rent_id` and wrong `locker_id`
        - `rent_id` of a WAITING_PICKUP rent
        - `locker_id` of other rent
        - correct `rent_id` and correct `locker_id`, but locker is CLOSED
        - correct `rent_id` and correct `locker_id`, with locker OPEN
    """
    waiting_dropoff_rent_id = "84ba232e-ce23-4d8f-ae26-68616600df48"
    waiting_dropoff_locker_id = "6b33b2d1-af38-4b60-a3c5-53a69f70a351"

    other_rent_id = "40efc6fd-f10c-4561-88bf-be916613377c"
    other_locker_id = "1b8d1e89-2514-4d91-b813-044bf0ce8d20"

    wrong_rent_id = "wrong_rent_id"
    wrong_locker_id = "wrong_locker_id"

    (_, code) = model.dropoff(wrong_rent_id, wrong_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.dropoff(wrong_rent_id, waiting_dropoff_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.dropoff(waiting_dropoff_rent_id, wrong_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.dropoff(other_rent_id, waiting_dropoff_locker_id)
    assert code == HTTPStatus.CONFLICT

    (_, code) = model.dropoff(waiting_dropoff_rent_id, other_locker_id)
    assert code == HTTPStatus.CONFLICT

    # locker is closed
    (_, code) = model.dropoff(waiting_dropoff_rent_id, waiting_dropoff_locker_id)
    assert code == HTTPStatus.CONFLICT

    # change locker state to OPEN
    model.db.db.update(
        "lockers",
        lambda locker: locker["id"] == waiting_dropoff_locker_id,
        lambda locker: locker.update({"status": "OPEN"})
    )
    (_, code) = model.dropoff(waiting_dropoff_rent_id, waiting_dropoff_locker_id)
    assert code == HTTPStatus.OK

    # check if the values were correctly updated
    ([rent], _) = model.get_by_id(waiting_dropoff_rent_id)
    assert rent["status"] == RentStatus.WAITING_PICKUP.value

def test_pickup(model):
    """
    Test the `pickup` model method in 7 scenarios:
        - wrong `rent_id` and wrong `locker_id`
        - wrong `rent_id` and correct `locker_id`
        - correct `rent_id` and wrong `locker_id`
        - `rent_id` of a DELIVERED rent
        - `locker_id` of other rent
        - correct `rent_id` and correct `locker_id`, but locker is CLOSED
        - correct `rent_id` and correct `locker_id`, with locker OPEN
    """
    waiting_pickup_rent_id = "40efc6fd-f10c-4561-88bf-be916613377c"
    waiting_pickup_locker_id = "1b8d1e89-2514-4d91-b813-044bf0ce8d20"

    other_rent_id = "feb72a9a-258d-49c9-92de-f90b1f11984d"
    other_locker_id = "6b33b2d1-af38-4b60-a3c5-53a69f70a351"


    wrong_rent_id = "wrong_rent_id"
    wrong_locker_id = "wrong_locker_id"

    (_, code) = model.pickup(wrong_rent_id, wrong_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.pickup(wrong_rent_id, waiting_pickup_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.pickup(waiting_pickup_rent_id, wrong_locker_id)
    assert code == HTTPStatus.NOT_FOUND

    (_, code) = model.pickup(other_rent_id, waiting_pickup_locker_id)
    assert code == HTTPStatus.CONFLICT

    (_, code) = model.pickup(waiting_pickup_rent_id, other_locker_id)
    assert code == HTTPStatus.CONFLICT

    # locker is closed
    (_, code) = model.pickup(waiting_pickup_rent_id, waiting_pickup_locker_id)
    assert code == HTTPStatus.CONFLICT

    # change locker state to OPEN
    model.db.db.update(
        "lockers",
        lambda locker: locker["id"] == waiting_pickup_locker_id,
        lambda locker: locker.update({"status": "OPEN"})
    )
    (_, code) = model.pickup(waiting_pickup_rent_id, waiting_pickup_locker_id)
    assert code == HTTPStatus.OK

    # check if the values were correctly updated
    ([rent], _) = model.get_by_id(waiting_pickup_rent_id)
    assert rent["status"] == RentStatus.DELIVERED.value
    [locker] = model.db.db.query(
        "lockers",
        lambda locker: locker["id"] == waiting_pickup_locker_id
    )
    assert locker["isOccupied"] is False
