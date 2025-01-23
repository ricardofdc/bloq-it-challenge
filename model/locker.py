import uuid
from http import HTTPStatus
from enum import Enum

from jsonschema import validate, ValidationError

from data.database import TableEnum, DatabaseInterface

class LockerStatus(Enum):
    """ Represents the status of a locker """
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class LockerModel:
    """
    The LockerModel class defines methods managing lockers with validation and
    error handling.

    Args:
        database (DatabaseInterface): Instance of a class that implements the
    `DatabaseInterface`. This parameter is used to interact with the database
    for performing operations like reading, creating, updating, and deleting
    data.
    """

    # Schema used for locker validation.
    _schema = {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "format": "uuid"
            },
            "bloqId": {
                "type": "string",
                "format": "uuid"
            },
            "status": {
                "enum": ["OPEN", "CLOSED"]
            },
            "isOccupied": {
                "type": "boolean"
            }
        },
        "required": ["id", "bloqId", "status", "isOccupied"],
        "additionalProperties": False
    }

    def __init__(self, database: DatabaseInterface):
        self.db = database

    def get_all(self) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieve all records from the LOCKERS database and returns them with an
        HTTP status code of 200 (OK).

        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing a list of
        dictionaries representing all records from the LOCKERS database, and an
        HTTP status code of 200 (OK).
        """
        return (
            self.db.read(TableEnum.LOCKERS, lambda locker: True),
            HTTPStatus.OK
        )

    def get_by_id(self, locker_id: str) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieves a record from the LOCKERS database by its UUID and returns the
        result along with an HTTP status code.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)

        Args:
            locker_id (str): UUID of the locker to look for.
        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing the result of the
        database read operation and the corresponding HTTP status code.
        """
        result = self.db.read(
            TableEnum.LOCKERS,
            lambda locker: locker["id"] == locker_id
        )

        if len(result) == 0:
            return_code = HTTPStatus.NOT_FOUND
        else:
            return_code = HTTPStatus.OK
        return (result, return_code)

    def get_by_bloq_id(self, bloq_id: str) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieves all records from the LOCKERS database by their bloqId and
        returns the result along with an HTTP status code.

        The HTTP status code options are:
            - 404 (UUID not found)
            - 200 (OK)

        Args:
            bloq_id (str): UUID of the bloq to look for.
        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing the result of the
        database read operation and the corresponding HTTP status code.
        """
        result = self.db.read(
            TableEnum.LOCKERS,
            lambda locker: locker["bloqId"] == bloq_id
        )

        if len(result) == 0:
            return_code = HTTPStatus.NOT_FOUND
        else:
            return_code = HTTPStatus.OK
        return (result, return_code)

    def create(self, new_locker: dict) -> tuple[dict | str, HTTPStatus]:
        """
        Generates a unique UUID for a locker object, validates it against a
        schema, and then creates a new entry in the LOCKERS database.

        The HTTP status code options are:
            - 201 (Created)
            - 400 (Bad Request)
            - 404 (Bloq UUID not found)

        Args:
            bloq (dict): Dictionary containing all the information needed to
        create a locker: "bloqId", "status", and "isOccupied".

        Returns:
            tuple[dict | str, HTTPStatus]: Tuple containing either the created
        locker as a dictionary (in which the generated ID is present) or a
        string in case something went wrong as the first element, and an
        HTTPStatus as the second element.
        """
        if "id" in new_locker:
            return ("You cannot choose an 'id'.", HTTPStatus.BAD_REQUEST)

        new_locker["id"] = str(uuid.uuid1())

        lockers = self.db.read(
            TableEnum.LOCKERS,
            lambda locker: locker["bloqId"] == new_locker["bloqId"]
        )

        if len(lockers) == 0:
            return (
                f'No bloq with "id": "{new_locker["bloqId"]}" found.',
                HTTPStatus.NOT_FOUND
            )

        try:
            validate(instance=new_locker, schema=self._schema)
            self.db.create(TableEnum.LOCKERS, new_locker)
            return (new_locker, HTTPStatus.CREATED)

        except ValidationError as msg:
            return (msg.message, HTTPStatus.BAD_REQUEST)

    def delete(self, locker_id: str) -> tuple[str, HTTPStatus]:
        """
        Deletes a locker along with its related rents from the database based
        on the provided locker UUID.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)

        Args:
            locker_id (str): UUID of the locker to be deleted,

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a message string and an
        HTTPStatus value.
        """
        lockers = self.db.read(
            TableEnum.LOCKERS,
            lambda locker: locker["id"] == locker_id
        )

        if len(lockers) == 0:
            return (
                f'Locker with "id": "{locker_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

        # delete rents from this locker
        self.db.delete(
            TableEnum.RENTS,
            lambda rent: rent["lockerId"] == locker_id
        )

        # delete locker
        self.db.delete(
            TableEnum.LOCKERS,
            lambda locker: locker["id"] == locker_id
        )

        return (
            f'Lockers, and Rents related to "id": "{locker_id}" deleted.',
            HTTPStatus.OK
        )

    def open(self, locker_id: str) -> tuple[dict | str, HTTPStatus]:
        """
        Updates a locker in the LOCKERS database after validating if it is
        CLOSED. If so, it updates it's "status" to OPEN.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)
            - 409 (Conflict: not CLOSED)

        Args:
            locker_id (str): UUID of the locker to open.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing the opened locker info as
        a dict or a string message in case of error, and the corresponding HTTP
        status code.
        """
        try:
            [locker] = self.db.read(
                TableEnum.LOCKERS,
                lambda dict: dict["id"] == locker_id
            )
        except ValueError:
            return (
                f'Locker with "id": "{locker_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

        if locker["status"] == LockerStatus.OPEN.value:
            return (
                f'Locker with "id": "{locker_id}" already OPEN.',
                HTTPStatus.CONFLICT
            )

        locker["status"] = LockerStatus.OPEN.value
        self.db.update(TableEnum.RENTS, locker)
        return locker, HTTPStatus.OK

    def close(self, locker_id: str) -> tuple[dict | str, HTTPStatus]:
        """
        Updates a locker in the LOCKERS database after validating if it is
        OPEN. If so, it updates it's "status" to CLOSED.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)
            - 409 (Conflict: not CLOSED)

        Args:
            locker_id (str): UUID of the locker to close.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing the closed locker info as
        a dict or a string message in case of error, and the corresponding HTTP
        status code.
        """
        try:
            [locker] = self.db.read(
                TableEnum.LOCKERS,
                lambda dict: dict["id"] == locker_id
            )
        except ValueError:
            return (
                f'Locker with "id": "{locker_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

        if locker["status"] == LockerStatus.CLOSED.value:
            return (
                f'Locker with "id": "{locker_id}" already CLOSED.',
                HTTPStatus.CONFLICT
            )

        locker["status"] = LockerStatus.CLOSED.value
        self.db.update(TableEnum.RENTS, locker)
        return (locker, HTTPStatus.OK)
