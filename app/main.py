# app/main.py

import time
from app.database import DatabaseHandler
from app.models import Job, Status
from app.job_handler import JobHandler
from app.plugin_loader import load_connector_class

def main():
    """
    Main application loop to poll the database and process jobs.
    """
    print("Starting HPC Job Manager.")

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
                results_dict = handler.process_running_job(job)
                database_handler.update_job(job, results_dict)

            # Process new jobs
            new_jobs = database_handler.fetch_jobs(Status.NEW)
            for job in new_jobs:
                results_dict = handler.process_new_job(job)
                database_handler.update_job(job, results_dict)
            
            # Process finished jobs last

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")


if __name__ == "__main__":
    main()

