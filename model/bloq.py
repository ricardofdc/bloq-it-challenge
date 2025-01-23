from http import HTTPStatus
import uuid

from jsonschema import validate, ValidationError

from data.database import DatabaseInterface, TableEnum

class BloqModel:
    """
    The BloqModel class defines methods managing bloqs with validation and error
    handling.

    Args:
        database (DatabaseInterface): Instance of a class that implements the
    `DatabaseInterface`. This parameter is used to interact with the database
    for performing operations like reading, creating, updating, and deleting
    data.
    """

    # Schema used for bloq validation.
    _schema = {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "format": "uuid"
            },
            "title": {
                "type": "string"
            },
            "address": {
                "type": "string"
            },
        },
        "required": ["id", "title", "address"],
        "additionalProperties": False
    }

    def __init__(self, database: DatabaseInterface):
        self.db = database

    def get_all(self) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieve all records from the BLOQS database and returns them with an
        HTTP status code of 200 (OK).

        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing a list of
        dictionaries representing all records from the BLOQS database, and an
        HTTP status code of 200 (OK).
        """
        return (self.db.read(TableEnum.BLOQS, lambda bloq: True), HTTPStatus.OK)

    def get_by_id(self, bloq_id: str) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieves a record from the BLOQS database by its UUID and returns the
        result along with an HTTP status code.

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
            TableEnum.BLOQS,
            lambda bloq: bloq["id"] == bloq_id
        )

        if len(result) == 0:
            return_code = HTTPStatus.NOT_FOUND
        else:
            return_code = HTTPStatus.OK
        return (result, return_code)

    def create(self, new_bloq: dict) -> tuple[dict | str, HTTPStatus]:
        """
        Generates a unique UUID for a bloq object, validates it against a
        schema, and then creates a new entry in the BLOQS database.

        The HTTP status code options are:
            - 201 (Created)
            - 400 (Bad Request)

        Args:
            bloq (dict): Dictionary containing all the information needed to
        create a bloq: "title" and "address".

        Returns:
            tuple[dict | str, HTTPStatus]: Tuple containing either the created
        bloq as a dictionary (in which the generated ID is present), or a string
        in case something went wrong as the first element, and an HTTPStatus as
        the second element.
        """
        if "id" in new_bloq:
            return ("You cannot choose an 'id'.", HTTPStatus.BAD_REQUEST)

        new_bloq["id"] = str(uuid.uuid1())
        try:
            validate(instance=new_bloq, schema=self._schema)
            self.db.create(TableEnum.BLOQS, new_bloq)
            return (new_bloq, HTTPStatus.CREATED)
        except ValidationError as msg:
            return (msg.message, HTTPStatus.BAD_REQUEST)

    def update(self, updated_bloq: dict) -> tuple[str, HTTPStatus]:
        """
        Updates a block in the BLOQS database after validating it's parameters
        checking if a block with the same "id" exists.

        The HTTP status code options are:
            - 200 (OK)
            - 400 (Bad Request)
            - 404 (UUID not found)

        Args:
            updated_bloq (dict): Dictionary containing all the data related to
        the updated bloq. It must include both the data that changes and the
        data that does not change.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a string message and an
        HTTP status code.
        """
        try:
            validate(instance=updated_bloq, schema=self._schema)
        except ValidationError as msg:
            return (msg.message, HTTPStatus.BAD_REQUEST)

        # Check if block exists
        find_bloq = self.db.read(
            TableEnum.BLOQS,
            lambda block: block["id"] == updated_bloq["id"]
        )

        if len(find_bloq) == 0:
            return (
                f'Bloq with "id": "{updated_bloq["id"]}" not found.',
                HTTPStatus.NOT_FOUND
            )

        # Perform update
        self.db.update(TableEnum.BLOQS, updated_bloq)
        return ("Updated.", HTTPStatus.OK)

    def delete(self, bloq_id: str) -> tuple[str, HTTPStatus]:
        """
        Deletes a bloq along with its related lockers and rents from the
        database based on the provided bloq UUID.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)

        Args:
            bloq_id (str): UUID of the bloq to be deleted.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a message string and an
        HTTPStatus value.
        """
        bloqs = self.db.read(
            TableEnum.BLOQS,
            lambda bloq: bloq["id"] == bloq_id
        )

        if len(bloqs) == 0:
            return (
                f'Bloq with "id": "{bloq_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

        # delete the bloq
        self.db.delete(TableEnum.BLOQS, lambda bloq: bloq["id"] == bloq_id)

        # delete rents from this bloq
        lockers = self.db.read(
            TableEnum.LOCKERS,
            lambda locker: locker["bloqId"] == bloq_id
        )
        for locker in lockers:
            self.db.delete(
                TableEnum.RENTS,
                lambda rent, locker_id=locker["id"]:
                    rent["lockerId"] == locker_id
            )

        # delete lockers from this bloq
        self.db.delete(
            TableEnum.LOCKERS,
            lambda locker: locker["bloqId"] == bloq_id
        )

        return (
            f'Bloqs, Lockers, and Rents related to "id": "{bloq_id}" deleted.',
            HTTPStatus.OK
        )
