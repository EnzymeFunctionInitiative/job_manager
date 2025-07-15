# app/job_handler.py

import os
from datetime import datetime
from app.job_enums import Status, Pipeline, ImportMode
from app.models import Job, FilenameParameters
#from plugins.notification import send_email
from config import settings

class JobHandler:
    def __init__(self, db_session, connector_instance):
        self.db = db_session
        self.connector = connector_instance

    def process_new_job(self, job: Job):
        """Handles the submission of a new job by delegating to the connector."""
        print(f"Processing NEW job: {job.id} using {job.id, self.connector.__class__.__name__}")
        
        # 1. Get job parameters and input file path
        input_file = None
        if isinstance(job, FilenameParameters) and job.jobFilename:
            file_path = os.path.join(settings.LOCAL_INPUT_FILE_SOURCE_DIR, job.jobFilename)
            if os.path.exists(file_path):
                input_file = file_path
            else:
                print(f"Input file not found for job {job.id}: {file_path}")
                job.status = Status.FAILED
                self.db.commit()
                return

        # 2. Prepare the job environment using the connector
        params = job.get_parameters_dict()
        params.update(settings.NEXTFLOW_PARAMS)
        if hasattr(job, "import_mode"):
            params.update({"import_mode": str(job.import_mode)})
        cluster_params_path = self.connector.prepare_job_environment(job.id, params, input_file)
        if not cluster_params_path:
            print(f"Failed to prepare job environment for job {job.id}")
            job.status = Status.FAILED
            self.db.commit()
            return

        # 3. Submit the job using the connector
        pipeline = str(job.pipeline)
        scheduler_job_id = self.connector.submit_job(job.id, cluster_params_path, pipeline)

        if scheduler_job_id:
            job.status = Status.RUNNING
            job.schedulerJobId = scheduler_job_id
            job.timeStarted = datetime.utcnow()
            print(f"Job {job.id} started with scheduler ID: {scheduler_job_id}")
            # send_email(user_email, f"Job {job.id} Started", "Your job is now running.")
        else:
            job.status = Status.FAILED
            print(f"Failed to start job {job.id} on cluster.")
            # send_email(user_email, f"Job {job.id} Failed", "Your job failed to start.")

        self.db.commit()

    def process_running_job(self, job: Job):
        """Checks the status of a running job."""
        print(f"Checking RUNNING job: {job.id} (Scheduler ID: {job.schedulerJobId})")
        
        status = self.connector.get_job_status(job.schedulerJobId)

        if status == "COMPLETED":
            print(f"Job {job.id} finished successfully.")
            job.status = Status.FINISHED
            job.timeCompleted = datetime.utcnow()
            
            # Retrieve results using the connector
            self.connector.retrieve_job_results(job.id)
            
            # send_email(user_email, f"Job {job.id} Finished", "Your job has completed.")

        elif status == "FAILED":
            print(f"Job {job.id} failed.")
            job.status = Status.FAILED
            job.timeCompleted = datetime.utcnow()
            # send_email(user_email, f"Job {job.id} Failed", "Your job has failed on the cluster.")
            
        elif status == "RUNNING":
            print(f"Job {job.id} is still running.")
            
        else: # UNKNOWN or other states
            print(f"Job {job.id} has an unknown status: {status}")

        self.db.commit()

