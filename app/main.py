# app/main.py

import time
from app.database import get_db_session, init_db
from app.models import Job, Status
from app.job_handler import JobHandler

def main():
    """
    Main application loop to poll the database and process jobs.
    """
    print("Starting HPC Job Manager...")
    init_db() # Ensure database is initialized

    while True:
        print("Checking for jobs...")
        db_session_generator = get_db_session()
        db = next(db_session_generator)
        
        handler = JobHandler(db)

        try:
            # Process new jobs
            new_jobs = db.query(Job).filter(Job.status == Status.NEW).all()
            for job in new_jobs:
                handler.process_new_job(job)

            # Process running jobs
            running_jobs = db.query(Job).filter(Job.status == Status.RUNNING).all()
            for job in running_jobs:
                handler.process_running_job(job)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
        finally:
            db.close()

        print("Sleeping for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    main()

