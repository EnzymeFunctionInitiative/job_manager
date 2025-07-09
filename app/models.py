# app/models.py
# This file will contain the SQLAlchemy ORM classes from your
# job_efi_web_orm.py.txt file.

from datetime import datetime
from enum import Flag
from typing import Dict, Any, List
import sqlalchemy
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, sessionmaker

# --- Mocked constants for standalone execution ---
class Status(Flag):
    NEW = 1
    RUNNING = 2
    FINISHED = 4
    FAILED = 8
    CANCELLED = 16
    COMPLETED = FINISHED | FAILED | CANCELLED

class FlagEnumType(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.Integer
    cache_ok = True

    def __init__(self, enum_class):
        super().__init__()
        self.enum_class = enum_class

    def process_bind_param(self, value, dialect):
        if isinstance(value, self.enum_class):
            return value.value
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.enum_class(value)
        return value

# --- Your provided ORM classes go here ---
# I've copied the content of job_efi_web_orm.py.txt here.
# For a real application, you might want to organize this differently.

class Base(DeclarativeBase):
    pass

class Job(Base):
    """
    SQLAlchemy model for the EFI-Web 'Job' table.
    """
    __tablename__ = 'Job'
    
    id: Mapped[int] = mapped_column(
        primary_key=True,
        info = {"is_parameter": True, "pipeline_key": "job_id"}
    )
    uuid: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[Status] = mapped_column(
        FlagEnumType(Status),
        nullable=False,
        info = {"is_updatable": True}
    )
    isPublic: Mapped[bool] = mapped_column(nullable=False)
    job_type: Mapped[str] = mapped_column(nullable=False)
    user_id: Mapped[int | None]
    # This is a placeholder for a User table relationship
    # user_email: Mapped[str] = mapped_column(nullable=True) 
    timeCreated: Mapped[datetime | None]
    timeStarted: Mapped[datetime | None] = mapped_column(
        info = {"is_updatable": True}
    )
    timeCompleted: Mapped[datetime | None] = mapped_column(
        info = {"is_updatable": True}
    )
    efi_db_version: Mapped[str | None] = mapped_column(
        info = {"is_parameter": True, "pipeline_key": "job_id"}
    )
    isExample: Mapped[bool | None]
    parentJob_id: Mapped[int | None]
    schedulerJobId: Mapped[int | None] = mapped_column(
        info = {"is_updatable": True}
    )
    jobName: Mapped[str | None] = mapped_column(info = {"is_parameter": True})
    results: Mapped[str | None] = mapped_column(info = {"is_updatable": True})
    
    __mapper_args__ = {
        "polymorphic_on": "job_type",
        "polymorphic_identity": "job",
    }

    def __repr__(self):
        if self.status in Status.COMPLETED:
            completed_string = f"timeStarted='{self.timeStarted}', timeCompleted='{self.timeCompleted}'"
        elif self.status == Status.RUNNING:
            completed_string = f"timeStarted='{self.timeStarted}'"
        else:
            completed_string = ""
        return (f"<self.__class__.__name__(id={self.id},"
                + f" status='{self.status}',"
                + f" job_type='{self.job_type}',"
                + f" timeCreated='{self.timeCreated}'"
                + f" {completed_string})>")

    def get_parameters_dict(self) -> Dict[str, Any]:
        mapper = inspect(self.__class__)
        return {
            column.info.get("pipeline_key",column.name): 
                getattr(self, column.name)
            for column in mapper.columns
            if column.info.get("is_parameter")
        }
    
    def get_updatable_attrs(self) -> List[str]:
        mapper = inspect(self.__class__)
        return [ 
            column.name for column in mapper.columns
            if column.info.get("is_updatable")
        ]

# ... (The rest of your model classes from the file would go here)
# For brevity, I am omitting the rest of the model definitions.
# You should copy all the classes from job_efi_web_orm.py.txt into this file.

class ESTGenerateFastaJob(Job):
     __mapper_args__ = { "polymorphic_identity": "est_generate_fasta" }
     # Add other columns from the original file
     inputFasta: Mapped[str | None] = mapped_column(info={"is_parameter": True})
     jobFilename: Mapped[str | None] = mapped_column(info={"is_parameter": True})
     # ... and so on for all job types

