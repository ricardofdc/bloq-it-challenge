from http import HTTPStatus
import shutil
import uuid

import pytest

from data.database import PotatoDatabase
from model.locker import LockerModel, LockerStatus

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
    return LockerModel(database)


def test_get_all(model):
    """
    Test the number of returned lockers, their size and the return code.
    """
    all_lockers, code = model.get_all()
    assert code == HTTPStatus.OK
    assert len(all_lockers) == 9
    for locker in all_lockers:
        assert len(locker) == 4

def test_get_by_id(model):
    """
    Test the `get_by_id` model method in 2 scenarios:
        - `locker_id` exists
        - `locker_id` does not exist
    """
    locker_id = "1b8d1e89-2514-4d91-b813-044bf0ce8d20"
    expected = {
        "id": locker_id,
        "bloqId": "c3ee858c-f3d8-45a3-803d-e080649bbb6f",
        "status": "CLOSED",
        "isOccupied": True
    }

    ([locker], code) = model.get_by_id(locker_id)
    assert code == HTTPStatus.OK
    assert locker == expected

    locker_id = "wrong_id"
    ([], code) = model.get_by_id(locker_id)
    assert code == HTTPStatus.NOT_FOUND

def test_get_by_block_id(model):
    """
    Test the `get_by_bloq_id` model method in 2 scenarios:
        - id exists
        - id does not exist
    """
    bloq_id = "c3ee858c-f3d8-45a3-803d-e080649bbb6f"
    all_lockers, code = model.get_by_bloq_id(bloq_id)
    assert code == HTTPStatus.OK
    assert len(all_lockers) == 3
    for b in all_lockers:
        assert len(b) == 4

    bloq_id = "wrong_id"
    ([], code) = model.get_by_bloq_id(bloq_id)
    assert code == HTTPStatus.NOT_FOUND

def test_create(model):
    """
    Test the `create` model method in 5 scenarios:
        - dict contains `id`
        - dict contains extra parameter
        - dict `status` is not allowed ("IN_BETWEEN")
        - dict `bloqId` does not exist on bloqs table
        - dict is correct
    """
    locker_with_id = {
        "id": str(uuid.uuid1()),
        "bloqId": "c3ee858c-f3d8-45a3-803d-e080649bbb6f",
        "status": "OPEN",
        "isOccupied": False
    }
    (_, code) = model.create(locker_with_id)
    assert code == HTTPStatus.BAD_REQUEST

    locker_with_extra_info = {
        "bloqId": "c3ee858c-f3d8-45a3-803d-e080649bbb6f",
        "status": "OPEN",
        "isOccupied": False,
        "wrongParameter": "value"
    }
    (_, code) = model.create(locker_with_extra_info)
    assert code == HTTPStatus.BAD_REQUEST

    locker_with_wrong_status = {
        "bloqId": "c3ee858c-f3d8-45a3-803d-e080649bbb6f",
        "status": "IN_BETWEEN",
        "isOccupied": False
    }
    (_, code) = model.create(locker_with_wrong_status)
    assert code == HTTPStatus.BAD_REQUEST

    locker_with_wrong_bloq_id = {
        "bloqId": "wrong_id",
        "status": "OPEN",
        "isOccupied": False
    }
    (_, code) = model.create(locker_with_wrong_bloq_id)
    assert code == HTTPStatus.NOT_FOUND

    locker_correct_info = {
        "bloqId": "c3ee858c-f3d8-45a3-803d-e080649bbb6f",
        "status": "OPEN",
        "isOccupied": False
    }

    # send copy so that it does not change original dict
    res, code = model.create(locker_correct_info.copy())

    # Add locker_id from result to sent locker information so that we can test
    locker_correct_info["id"] = res["id"]
    assert res == locker_correct_info
    assert code == HTTPStatus.CREATED

def test_open(model):
    """
    Test the `open` model method in 3 scenarios:
        - correct `locker_id`, with CLOSED locker
        - correct `locker_id`, but locker is OPEN
        - wrong `locker_id`
    """
    locker_id = "1b8d1e89-2514-4d91-b813-044bf0ce8d20"
    res, code = model.open(locker_id)
    assert code == HTTPStatus.OK
    assert res["status"] == LockerStatus.OPEN.value

    locker_id = "8b4b59ae-8de5-4322-a426-79c29315a9f1"
    (_, code) = model.open(locker_id)
    assert code == HTTPStatus.CONFLICT

    locker_id = "wrong_id"
    (_, code) = model.open(locker_id)
    assert code == HTTPStatus.NOT_FOUND

def test_close(model):
    """
    Test the `close` model method in 3 scenarios:
        - correct `locker_id`, with OPEN locker
        - correct `locker_id`, but locker is CLOSED
        - wrong `locker_id`
    """
    locker_id = "8b4b59ae-8de5-4322-a426-79c29315a9f1"
    res, code = model.close(locker_id)
    assert code == HTTPStatus.OK
    assert res["status"] == LockerStatus.CLOSED.value

    locker_id = "1b8d1e89-2514-4d91-b813-044bf0ce8d20"
    (_, code) = model.close(locker_id)
    assert code == HTTPStatus.CONFLICT

    locker_id = "wrong_id"
    (_, code) = model.close(locker_id)
    assert code == HTTPStatus.NOT_FOUND

def test_delete(model):
    """
    Test the `delete` model method in 2 scenarios:
        - `locker_id` does not exist
        - `locker_id` exists
    """
    locker_id = "wrong_id"
    (_, code) = model.delete(locker_id)
    assert code == HTTPStatus.NOT_FOUND

    locker_id = "6b33b2d1-af38-4b60-a3c5-53a69f70a351"
    (_, code) = model.delete(locker_id)
    assert code == HTTPStatus.OK
    assert len(model.db.db.tables["lockers"]) == 8
    assert len(model.db.db.tables["rents"]) == 2
