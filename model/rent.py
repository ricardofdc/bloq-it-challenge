import uuid
from http import HTTPStatus
from enum import Enum
from jsonschema import validate, ValidationError

from data.database import TableEnum, DatabaseInterface
from .locker import LockerStatus

class RentStatus(Enum):
    """ Represents the status of a rent """
    CREATED = "CREATED"
    WAITING_DROPOFF = "WAITING_DROPOFF"
    WAITING_PICKUP = "WAITING_PICKUP"
    DELIVERED = "DELIVERED"

class RentSize(Enum):
    """ Represents the size of a rent """
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"

class RentModel:
    """
    The RentModel class defines methods managing rents with validation and
    error handling.

    Args:
        database (DatabaseInterface): Instance of a class that implements the
    `DatabaseInterface`. This parameter is used to interact with the database
    for performing operations like reading, creating, updating, and deleting
    data.
    """

    # Schema used for rent validation.
    _schema = {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "format": "uuid"
            },
            "lockerId": {
                "type": ["string", "null"],
                "format": "uuid",
            },
            "weight": {
                "type": "number",
                "minimum": 0
            },
            "size": {
                "enum": ["XS", "S", "M", "L", "XL"]
            },
            "status": {
                "enum": [
                    "CREATED", "WAITING_DROPOFF",
                    "WAITING_PICKUP", "DELIVERED"
                ]
            }
        },
        "required": ["id", "lockerId", "weight", "size", "status"],
        "additionalProperties": False
    }

    def __init__(self, database: DatabaseInterface):
        self.db = database

    def get_all(self) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieve all records from the RENTS database and returns them with an
        HTTP status code of 200 (OK).

        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing a list of
        dictionaries representing all records from the RENTS database, and an
        HTTP status code of 200 (OK).
        """
        return (
            self.db.read(TableEnum.RENTS, lambda rent: True),
            HTTPStatus.OK
        )

    def get_by_id(self, rent_id: str) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieves a record from the RENTS database by its UUID and returns the
        result along with an HTTP status code.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)

        Args:
            rent_id (str): UUID of the rent to look for.
        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing the result of the
        database read operation and the corresponding HTTP status code.
        """
        result = self.db.read(
            TableEnum.RENTS,
            lambda rent: rent["id"] == rent_id
        )

        if len(result) == 0:
            return_code = HTTPStatus.NOT_FOUND
        else:
            return_code = HTTPStatus.OK
        return (result, return_code)

    def get_by_locker_id(self, locker_id: str) -> tuple[list[dict], HTTPStatus]:
        """
        Retrieves all records from the RENTS database by their `lockerId` and
        returns the result along with an HTTP status code.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)

        Args:
            locker_id (str): UUID of the locker to look for.
        Returns:
            tuple[list[dict], HTTPStatus]: A tuple containing the result of the
        database read operation and the corresponding HTTP status code.
        """
        print(locker_id if locker_id != "" else None)
        result = self.db.read(
            TableEnum.RENTS,
            lambda rent: rent["lockerId"] is None if locker_id == ""
                else rent["lockerId"] == locker_id
        )

        if len(result) == 0:
            return_code = HTTPStatus.NOT_FOUND
        else:
            return_code = HTTPStatus.OK
        return (result, return_code)

    def create(self, new_rent: dict) -> tuple[dict | str, HTTPStatus]:
        """
        Generates a unique UUID for a rent object, validates it against a
        schema, and then creates a new entry in the RENTS database.

        The HTTP status code options are:
            - 201 (Created)
            - 400 (Bad Request)
            - 404 (Bloq UUID not found)

        Args:
            bloq (dict): Dictionary containing all the information needed to
        create a rent: "weight" and "size" (all other properties are not
        allowed to be chosen at this point).

        Returns:
            tuple[dict | str, HTTPStatus]: Tuple containing either the created
        rent as a dictionary (in which the generated ID is present) or a
        string in case something went wrong as the first element, and an
        HTTPStatus as the second element.
        """
        if "id" in new_rent:
            return ("You cannot choose an 'id'.", HTTPStatus.BAD_REQUEST)

        if "lockerId" in new_rent:
            return ("You cannot choose a 'lockerId'.", HTTPStatus.BAD_REQUEST)

        if "status" in new_rent:
            return ("You cannot choose a 'status'.", HTTPStatus.BAD_REQUEST)

        new_rent["id"] = str(uuid.uuid1())
        new_rent["lockerId"] = None
        new_rent["status"] = RentStatus.CREATED.value

        try:
            validate(instance=new_rent, schema=self._schema)
            self.db.create(TableEnum.RENTS, new_rent)
            return (new_rent, HTTPStatus.CREATED)

        except ValidationError as msg:
            return (msg.message, HTTPStatus.BAD_REQUEST)

    def delete(self, rent_id: str) -> tuple[str, HTTPStatus]:
        """
        Deletes a rent based on the provided rent UUID.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (UUID not found)

        Args:
            rent_id (str): UUID of the rent to be deleted.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a message string and an
        HTTPStatus value.
        """
        rents = self.db.read(
            TableEnum.RENTS,
            lambda dict: dict["id"] == rent_id
        )

        if len(rents) == 0:
            return (
                f'Rent with "id": "{rent_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

        # delete rent
        self.db.delete(
            TableEnum.RENTS,
            lambda dict: dict["id"] == rent_id
        )

        return (
            f'Rent with "id": "{rent_id}" deleted.',
            HTTPStatus.OK
        )

    def send(self, rent_id: str, locker_id: str) -> tuple[str, HTTPStatus]:
        """
        If the rent `status` is `CREATED` and the locker is not occupied,
        updates the rent status to `WAITING_DROPOFF`, sets the `lockerId`
        where the drop off must happen and sets the `isOccupied` value of that
        locker to `True`. Otherwise a fault message is returned to inform what
        when wrong.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (Rent/Locker UUID not found)
            - 409 (Conflict: cannot send this rent)
            - 500 (Internal Server Error)

        Args:
            rent_id (str): UUID of the rent to be sent.
            locker_id (str): UUID of the locker where the rent will be sent to.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a message string and an
        HTTPStatus value.
        """
        try:
            [rent] = self.db.read(
                TableEnum.RENTS,
                lambda dict: dict["id"] == rent_id
            )
        except ValueError:
            return (
                f'Rent with "id": "{locker_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

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

        if rent["status"] != RentStatus.CREATED.value:
            return (
                'Rent status is not "CREATED". Cannot send it.',
                HTTPStatus.CONFLICT
            )

        if rent["lockerId"] is not None:
            # This one should be impossible to happen knowing that status is
            # "CREATED" from the previous if statement. If nothing out of the
            # ordinary happens to our database, `lockerId` is only `null` while
            # status is "CREATED".
            return (
                'Rent already has a lockerId assigned. Cannot send it.',
                HTTPStatus.INTERNAL_SERVER_ERROR
            )

        if locker["isOccupied"]:
            return (
                'Locker is occupied. Cannot send rent to this locker.',
                HTTPStatus.CONFLICT
            )

        # If all checks pass, we can now update the objects
        locker["isOccupied"] = True
        rent["status"] = RentStatus.WAITING_DROPOFF.value
        rent["lockerId"] = locker_id
        self.db.update(TableEnum.LOCKERS, locker)
        self.db.update(TableEnum.RENTS, rent)
        return ("Rent sent.", HTTPStatus.OK)



    def dropoff(self, rent_id: str, locker_id: str) -> tuple[str, HTTPStatus]:
        """
        If the rent `status` is `WAITING_DROPOFF` and the locker is correct and
        open, changes the rent `status` to `WAITING_PICKUP`. Otherwise, an error
        message is returned to inform what went wrong.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (Rent/Locker UUID not found)
            - 409 (Conflict: cannot send this rent)

        Note:
            It is not the responsibility of this method to `open` or `close`
            the lockers.

        Args:
            rent_id (str): UUID of the rent to be dropped off.
            locker_id (str): UUID of the locker where the rent is being
        dropped off.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a message string and an
        HTTPStatus value.
        """
        try:
            [rent] = self.db.read(
                TableEnum.RENTS,
                lambda dict: dict["id"] == rent_id
            )
        except ValueError:
            return (
                f'Rent with "id": "{rent_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

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

        if rent["status"] != RentStatus.WAITING_DROPOFF.value:
            return (
                'Rent status is not "WAITING_DROPOFF". Cannot drop it off.',
                HTTPStatus.CONFLICT
            )

        if rent["lockerId"] != locker_id:
            return (
                'Rent "lockerId" does not match with the provided locker id. Cannot drop it off.',
                HTTPStatus.CONFLICT
            )

        if locker["status"] != LockerStatus.OPEN.value:
            return (
                'Locker is not open. Cannot drop off on it.',
                HTTPStatus.CONFLICT
            )

        # If all checks pass, we can now update the objects
        rent["status"] = RentStatus.WAITING_PICKUP.value
        self.db.update(TableEnum.RENTS, rent)
        return ("Rent dropped off.", HTTPStatus.OK)


    def pickup(self, rent_id: str, locker_id: str) -> tuple[str, HTTPStatus]:
        """
        If the rent `status` is `WAITING_PICKUP` and the locker is correct,
        open, and occupied, changes the locker `isOccupied` value to `False`
        and the rent `status` to `DELIVERED`. Otherwise, an error message is
        returned to inform what went wrong.

        The HTTP status code options are:
            - 200 (OK)
            - 404 (Rent/Locker UUID not found)
            - 409 (Conflict: cannot send this rent)

        Note:
            It is not the responsibility of this method to `open` or `close`
            the lockers.

        Args:
            rent_id (str): UUID of the rent to be picked up.
            locker_id (str): UUID of the locker where the rent is being
        picked up.

        Returns:
            tuple[str, HTTPStatus]: Tuple containing a message string and an
        HTTPStatus value.
        """
        try:
            [rent] = self.db.read(
                TableEnum.RENTS,
                lambda dict: dict["id"] == rent_id
            )
        except ValueError:
            return (
                f'Rent with "id": "{locker_id}" not found.',
                HTTPStatus.NOT_FOUND
            )

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

        if rent["status"] != RentStatus.WAITING_PICKUP.value:
            return (
                'Rent status is not "WAITING_PICKUP". Cannot pick it up.',
                HTTPStatus.CONFLICT
            )

        if rent["lockerId"] != locker_id:
            return (
                'Rent "lockerId" does not match with the provided locker id. Cannot pick it up.',
                HTTPStatus.CONFLICT
            )

        if locker["status"] != LockerStatus.OPEN.value:
            return (
                'Locker is not open. Cannot pick up from it.',
                HTTPStatus.CONFLICT
            )

        if not locker["isOccupied"]:
            return (
                'Locker is not occupied. Cannot pick up from it.',
                HTTPStatus.CONFLICT
            )

        # If all checks pass, we can now update the objects
        locker["isOccupied"] = False
        rent["status"] = RentStatus.DELIVERED.value
        self.db.update(TableEnum.LOCKERS, locker)
        self.db.update(TableEnum.RENTS, rent)
        return ("Rent picked up.", HTTPStatus.OK)
