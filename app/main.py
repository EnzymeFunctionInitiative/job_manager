# app/main.py

import time

from config import settings
from app.database import DatabaseHandler
from app.models import Job, Status
from app.job_handler import JobHandler
from app.plugin_loader import load_connector_class
from app.job_logger import logger_names, setup_logger, clean_logger

def main():
    """
    Main application loop to poll the database and process jobs.
    """
    # create the logger that handles logging streams
    main_logger = setup_logger(
        logger_names.MAIN,
        settings.LOG_FILE_PATH,
    )
    main_logger.info("Starting the Job Manager.")

    if settings.DRY_RUN:
        main_logger.info(
            "This is just a dry run of the Job Manager. No commands will be"
            + " executed. Parameter files will logged instead of written to"
            + " file. No updates will be pushed to the Job database."
        )

    # Load the connector class dynamically when the application starts.
    ConnectorClass = load_connector_class()
    # Instantiate the dynamically loaded connector class
    connector = ConnectorClass()
    
    handler = JobHandler(connector)

    # create an instance of the DatabaseHandler object using context management
    with DatabaseHandler() as database_handler:
        # contain the job-handling within try-except blocks
        try:
            # Process running jobs first
            running_jobs = database_handler.fetch_jobs(Status.RUNNING)
            for job in running_jobs:
                main_logger.info("Processing %s.", job)
                results_dict = handler.process_running_job(job)
                database_handler.update_job(job, results_dict)

            # requery the database to get the number of running jobs
            n_running_jobs = len(list(database_handler.fetch_jobs(Status.RUNNING)))
            main_logger.info(
                "There are currently %s EFI jobs running on the"
                + " compute resource (not accounting for nextflow subprocess"
                + " jobs).",
                n_running_jobs
            )
            # see if new jobs can be submitted and do so
            if n_running_jobs < settings.MAX_NUM_RUNNING_JOB:
                # Process new jobs
                new_jobs = database_handler.fetch_jobs(Status.NEW)
                for job in new_jobs:
                    main_logger.info("Processing %s.", job)
                    results_dict = handler.process_new_job(job)
                    database_handler.update_job(job, results_dict)
            
            # Process finished jobs last

        except Exception as e:
            # log the exception
            main_logger.error(
                "An error occurred in the main loop while processing %s.",
                job,
                exc_info = e
            )
            # close the logger's handles
            clean_logger(main_logger)
            # raise the error
            raise
        
    main_logger.info("Shutting down the Job Manager.")
    clean_logger(main_logger)
    

if __name__ == "__main__":
    main()

