# app/database.py

from typing import Dict, Any
import logging

import sqlalchemy
from sqlalchemy import URL, create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from app.job_enums import Status
from app.models import Base, Job
from app.job_logger import logger_names

module_logger = logging.getLogger(logger_names.DATABASE)

class DatabaseHandler:
    def __init__(self):
        self.db_url = settings.DATABASE_URI
        self._Base = Base
        self._Job = Job
        self._engine: Optional[sqlalchemy.engine.Engine] = None
        self._Session: Optional[sqlalchemy.orm.sessionmaker] = None
        self.session: Optional[sqlalchemy.orm.Session] = None
        self.dry_run = settings.DRY_RUN

    # enable context management via __enter__ and __exit__
    def __enter__(self):
        """
        Enables clean opening of the data handler with a `with` statement.
        """
        self.load_data()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Enables clean closing of the data strategy's data stream while in a
        `with` statement.
        """
        self.close()

    ############################################################################
    # interface methods
    def load_data(self):
        """
        Establish a connection to the database
        """
        try:
            self._engine = create_engine(self.db_url)
            
            # Create tables if they don't exist
            self._Base.metadata.create_all(self._engine)
            
            # update the attributes to point to the bound database
            self._Session = sessionmaker(bind=self._engine)
            # create the Session obj instance to use that database conn
            self.session = self._Session()
            module_logger.info("Connected to database: %s", self.db_url)
            
        except Exception as e:
            module_logger.error(
                "Error connecting to database.",
                exc_info = e
            )
            raise

    def close(self):
        """
        Close the connection to the database.  SQLAlchemy handles connection
        pooling, so the connection is not explicitly closed here. Instead,
        dispose of the session.
        """
        # check that any changes get commit to the db before close is executed
        if not self.dry_run:
            self.session.commit()
        
        try:
            if self.session:
                self.session.close()
                self.session = None
                module_logger.info(
                    "Disconnected from database (session closed)."
                )
            if self._engine:
                self._engine.dispose()
                self._engine = None
                module_logger.info(
                    "Disconnected from database (engine disposed)."
                )
            
        except Exception as e:
            module_logger.error(
                "Error disconnecting from database.",
                exc_info = e
            )
            raise

    def fetch_jobs(self,
            status: Status
            ) -> sqlalchemy.engine.ChunkedIteratorResult:
        """
        Return a generator containing Job objects associated with rows in the
        SQL table that pass the status comparison.

        Arguments
        ---------
            status,
                Status flag to denote the status of the jobs to be fetched
                (e.g., 'Status.QUEUED', 'Status.FINISHED', 'Status.INCOMPLETE')

        Returns
        -------
            sqlalchemy.engine.result.ChunkedIteratorResult
                result from the self.session.execute() call. Is an iterator.
        """
        if not self.session:
            module_logger.error("Not connected to the database.")
            raise Exception
        
        # `status` can be a flag with membership. If so, it needs to be
        # separated into a list of its component Status flag strings
        status_strings = [flag.__str__() for flag in Status if flag in status]
        try:
            # query string using the status_strings list
            statement = select(self._Job).where(self._Job.status.in_(status_strings)).order_by(self._Job.id.asc())
            # execute the query
            for job in self.session.execute(statement):
                yield job[0]
        except Exception as e:
            module_logger.error("Error fetching job rows from the database"
                + " with given status strings: %s",
                status_strings,
                exc_info = e
            )
            raise

    def update_job(self, job_obj: Job, update_dict: Dict[str, Any]) -> None:
        """
        Update the Job object's attributes with information contained in the
        update_dict.
        
        Arguments
        ---------
            job_obj
                Job, the ORM class to denote a row in table Job.
            update_dict
                dict, keys map to Job attributes (column names) and associated
                values are the new values to be updated to.
        """
        if not self.session:
            module_logger.error("Not connected to the database.")
            raise Exception

        if self.dry_run:
            module_logger.info(
                "Job %s would be updated with the given dictionary:\n%s",
                job_obj.id,
                update_dict
            )
            return

        if not update_dict:
            module_logger.info(
                "No updates applied to the (%s).",
                job_obj.__repr__()
            )
            return

        # add an air-gap btwn updating the database by checking whether keys in
        # the results_dict are labeled as updatable in the jOb table.
        updatable_columns = job_obj.get_updatable_attrs()
        # loop over the items in results_dict
        for key, value in update_dict.items():
            if key not in updatable_columns:
                continue
            setattr(job_obj, key, value)
        
        self.session.commit()
        module_logger.info(
            "Applied updates to (%s).",
            job_obj.__repr__()
        )
    ############################################################################

