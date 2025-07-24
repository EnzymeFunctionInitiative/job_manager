# app/flag_enum_type.py

from typing import Union
from enum import Flag
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

class FlagEnumType(TypeDecorator):
    """
    SQLAlchemy does not know how to handle python Enum/Flag values as DB column
    values. This class is developing the custom handling of a str column
    (stored as a VARCHAR or equivalent) and an associated python Flag object.

    This is general code that works for any python Flag Enum, but is intended
    for the Status object and the status column in the DB.
    """
    impl = String   # DB column is implemented as a SQLAlchemy String
    cache_ok = True

    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def process_bind_param(self, value: Flag, dialect):
        """
        Overwrite TypeDecorator.process_bind_param() method to implement custom
        handling for this object. Documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator.process_bind_param

        This is used to convert an instance of the python Flag class (e.g.
        Status.QUEUED) into a string that can be used in the SQL DB (e.g.
        "queued").
        """
        return value.__str__()

    def process_result_value(self, value: Union[int, str], dialect) -> Flag:
        """
        Overwrite TypeDecorator.process_result_value() method to implement
        custom handling for this object. Documentation:
        https://docs.sqlalchemy.org/en/20/core/custom_types.html#sqlalchemy.types.TypeDecorator.process_result_value

        This is used to convert a row column's value to the returned python
        type, for example a status column value of "queued" in the DB is
        converted to Status.QUEUED.
        """
        return self.enum_class.get_flag(value)

