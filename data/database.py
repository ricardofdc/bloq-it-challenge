
from enum import Enum
from collections.abc import Callable
from abc import ABC, abstractmethod

from potatodb.db import PotatoDB

class TableEnum(Enum):
    """
    The class `TableEnum` defines an enumeration with values representing
    different types of tables.
    """
    BLOQS = "bloqs"
    LOCKERS = "lockers"
    RENTS = "rents"

class DatabaseInterface(ABC):
    """
    The `DatabaseInterface` class defines abstract methods for basic CRUD
    operations on a database.

    """
    @abstractmethod
    def create(self, table: TableEnum, obj: dict) -> None:
        """
        Abstract method for `create` operation.
        This method inserts a new object on the selected table.

        Args:
            table (TableEnum): Table to insert new object
            obj (dict): Object to be inserted
        """

    @abstractmethod
    def read(self, table: TableEnum, query: Callable) -> list[dict]:
        """
        Abstract method for `read` operation.
        This method finds and returns all the objects of a given table that
        satisfy the given query.

        Args:
            table (TableEnum): Table to look for object(s)
            query (Callable): Query to be performed while searching

        Returns:
            list[dict]: list of found objects
        """

    @abstractmethod
    def update(self, table: TableEnum, obj: dict) -> None:
        """
        Abstract method for `update` operation.
        This method looks for the object that matches the given object's "id"
        parameter, and replaces it with the given object.

        Note: "id" parameters are not updatable.

        Args:
            table (TableEnum): Table to look for object
            obj (dict): Object contents after update
        """

    @abstractmethod
    def delete(self, table: TableEnum, query: Callable) -> None:
        """
        Abstract method for `update` operation.
        This method deletes all the objects of a given table that satisfy the
        given query.

        Args:
            table (TableEnum): _description_
            query (Callable): _description_
        """


class PotatoDatabase:
    """
    The `PotatoDatabase` class provides methods for creating, reading, updating,
    and deleting records in a database using a `PotatoDB` instance.

    """
    def __init__(self, foldername: str):
        """_summary_

        Args:
            foldername (str): _description_
        """
        self.db = PotatoDB(foldername)

    def create(self, table: TableEnum, obj: dict) -> None:
        """
        The function creates a new entry in a database table using the provided
        object data.

        Args:
            table (TableEnum): Table where the object should be inserted.
            obj (dict): Dictionary that contains the data to be inserted in the
        table.
        """
        self.db.insert(table.value, obj)

    def read(self, table: TableEnum, query: Callable) -> list[dict]:
        """
        The `read` function takes a table enum and a query function as input,
        and returns a list of dictionaries by querying the database.

        Args:
            table (TableEnum): Table where the object should be read from.
            query (Callable): Callable function that will be used to retrieve
        data from the database.

        Returns:
            list[dict]: list of found objects
        """
        return self.db.query(table.value, query)

    def update(self, table: TableEnum, obj: dict) -> None:
        """
        The `update` function updates a record in a database table based on a
        specified condition.

        Args:
            table (TableEnum): Table where the object should be updated.
            obj (dict): Dictionary containing the data that you want to update
        in the database. The "id" parameter of this dictionary must be the same
        as the one from the object you want to update. ("id" parameters are not
        updatable)
        """
        self.db.update(
            table.value,
            lambda record: record["id"] == obj["id"],
            lambda record: record.update(obj)
        )

    def delete(self, table: TableEnum, query: Callable) -> None:
        """
        The `delete` function deletes records from a database table based on a
        specified query.

        Args:
            table (TableEnum): Table where the object should be deleted.
            query (Callable): Callable function that will be used to delete
        data from the database.
        """
        self.db.delete(table.value, query)
