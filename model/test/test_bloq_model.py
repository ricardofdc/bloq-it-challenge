from http import HTTPStatus
import shutil
import uuid

import pytest

from data.database import PotatoDatabase
from model.bloq import BloqModel


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
    return BloqModel(database)


def test_get_all(model):
    """
    Test the number of returned bloqs, their size and the return code.
    """
    all_bloqs, code = model.get_all()
    assert code == HTTPStatus.OK
    assert len(all_bloqs) == 3
    for bloq in all_bloqs:
        assert len(bloq) == 3

def test_get_by_id(model):
    """
    Test the `get_by_id` model method in 2 scenarios:
        - `bloq_id` exists
        - `bloq_id` does not exist
    """
    bloq_id = "c3ee858c-f3d8-45a3-803d-e080649bbb6f"
    expected = {
        "id": bloq_id,
        "title": "Luitton Vouis Champs Elysées",
        "address": "101 Av. des Champs-Élysées, 75008 Paris, France",
    }

    ([bloq], code) = model.get_by_id(bloq_id)
    assert code == HTTPStatus.OK
    assert bloq == expected

    bloq_id = "wrong_id"
    ([], code) = model.get_by_id(bloq_id)
    assert code == HTTPStatus.NOT_FOUND

def test_create(model):
    """
    Test the `create` model method in 3 scenarios:
        - dict contains `id`
        - dict contains extra parameter
        - dict is correct
    """
    bloq_with_id = {
        "id": str(uuid.uuid1()),
        "title": "test title",
        "address": "test address"
    }
    (_, code) = model.create(bloq_with_id)
    assert code == HTTPStatus.BAD_REQUEST

    bloq_with_extra_info = {
        "title": "test title",
        "address": "test address",
        "extra_parameter": "test extra parameter"
    }
    (_, code) = model.create(bloq_with_extra_info)
    assert code == HTTPStatus.BAD_REQUEST

    bloq_correct_info = {
        "title": "test title",
        "address": "test address"
    }
    res, code = model.create(bloq_correct_info)
    assert res == {
        "id": res["id"],
        "title": "test title",
        "address": "test address"
    }
    assert code == HTTPStatus.CREATED

def test_update(model):
    """
    Test the `update` model method in 3 scenarios:
        - dict is correct
        - dict contains non existent `id`
        - dict does not contain `id`
    """
    bloq = {
        "id": "c3ee858c-f3d8-45a3-803d-e080649bbb6f",
        "title": "test title",
        "address": "test address"
    }
    (_, code) = model.update(bloq)
    assert code == HTTPStatus.OK

    bloq = {
        "id": "wrong_id",
        "title": "test title",
        "address": "test address"
    }
    (_, code) = model.update(bloq)
    assert code == HTTPStatus.NOT_FOUND

    bloq = {
        "title": "test title",
        "address": "test address"
    }
    (_, code) = model.update(bloq)
    assert code == HTTPStatus.BAD_REQUEST

def test_delete(model):
    """
    Test the `delete` model method in 2 scenarios:
        - `bloq_id` does not exist
        - `bloq_id` exists
    """
    bloq_id = "wrong_id"
    (_, code) = model.delete(bloq_id)
    assert code == HTTPStatus.NOT_FOUND

    bloq_id = "c3ee858c-f3d8-45a3-803d-e080649bbb6f"
    (_, code) = model.delete(bloq_id)
    assert code == HTTPStatus.OK
    assert len(model.db.db.tables["bloqs"]) == 2
    assert len(model.db.db.tables["lockers"]) == 6
    assert len(model.db.db.tables["rents"]) == 3
