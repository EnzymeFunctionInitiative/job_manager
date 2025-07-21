# app/main.py

import time
from app.database import get_db_session, init_db
from app.models import Job, Status
from app.job_handler import JobHandler
from app.plugin_loader import load_connector_class

def main():
    """
    Main application loop to poll the database and process jobs.
    """
    print("Starting HPC Job Manager...")
    init_db() # Ensure database is initialized

    print("Checking for jobs...")
    db_session_generator = get_db_session()
    db = next(db_session_generator)

    # Load the connector class dynamically when the application starts.
    ConnectorClass = load_connector_class()
    # Instantiate the dynamically loaded connector class
    connector = ConnectorClass()
    
    handler = JobHandler(connector)

    try:
        # Process new jobs
        new_jobs = db.query(Job).filter(Job.status == Status.NEW).all()
        for job in new_jobs:
            results_dict = handler.process_new_job(job)
            handler.apply_updates(db, job, results_dict)

        # Process running jobs
        running_jobs = db.query(Job).filter(Job.status == Status.RUNNING).all()
        for job in running_jobs:
            results_dict = handler.process_running_job(job)
            handler.apply_updates(db, job, results_dict)

    except Exception as e:
        print(f"An error occurred in the main loop: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

