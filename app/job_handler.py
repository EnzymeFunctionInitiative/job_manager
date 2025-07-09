# app/job_handler.py

import os
import json
from datetime import datetime
from app.models import Job, Status
from plugins.hpc_connector import HPCConnector
from plugins.notification import send_email
from config import settings

class JobHandler:
    def __init__(self, db_session):
        self.db = db_session
        self.hpc = HPCConnector()

    def process_new_job(self, job: Job):
        """Handles the submission of a new job."""
        print(f"Processing NEW job: {job.id}")
        
        # 1. Create remote directory
        remote_job_dir = self.hpc.create_remote_directory(job.id)
        if not remote_job_dir:
            print(f"Failed to create remote directory for job {job.id}")
            job.status = Status.FAILED
            self.db.commit()
            return

        # 2. Save parameters to a JSON file
        params = job.get_parameters_dict()
        local_params_path = os.path.join(settings.LOCAL_JOB_DIRECTORY, str(job.id), "params.json")
        os.makedirs(os.path.dirname(local_params_path), exist_ok=True)
        with open(local_params_path, 'w') as f:
            json.dump(params, f, indent=4)

        # 3. Copy params file to remote
        remote_params_path = os.path.join(remote_job_dir, "params.json")
        if not self.hpc.copy_to_remote(local_params_path, remote_params_path):
            print(f"Failed to copy params file for job {job.id}")
            job.status = Status.FAILED
            self.db.commit()
            return
            
        # 4. Copy input file if applicable
        if hasattr(job, 'jobFilename') and job.jobFilename:
            local_file_path = os.path.join(settings.LOCAL_INPUT_FILE_SOURCE_DIR, job.jobFilename)
            if os.path.exists(local_file_path):
                remote_file_path = os.path.join(remote_job_dir, job.jobFilename)
                if not self.hpc.copy_to_remote(local_file_path, remote_file_path):
                    print(f"Failed to copy input file for job {job.id}")
                    job.status = Status.FAILED
                    self.db.commit()
                    return
            else:
                print(f"Input file not found for job {job.id}: {local_file_path}")
                job.status = Status.FAILED
                self.db.commit()
                return

        # 5. Start Nextflow job
        hpc_job_id = self.hpc.start_nextflow_job(job.id, remote_params_path)

        if hpc_job_id:
            job.status = Status.RUNNING
            job.schedulerJobId = hpc_job_id
            job.timeStarted = datetime.utcnow()
            print(f"Job {job.id} started with HPC ID: {hpc_job_id}")
            # Assuming you have a way to get the user's email from user_id
            # send_email(user_email, f"Job {job.id} Started", "Your job is now running.")
        else:
            job.status = Status.FAILED
            print(f"Failed to start job {job.id} on HPC.")
            # send_email(user_email, f"Job {job.id} Failed", "Your job failed to start.")

        self.db.commit()

    def process_running_job(self, job: Job):
        """Checks the status of a running job."""
        print(f"Checking RUNNING job: {job.id} (HPC ID: {job.schedulerJobId})")
        
        status = self.hpc.get_job_status(job.schedulerJobId)

        if status == "COMPLETED":
            print(f"Job {job.id} finished successfully.")
            job.status = Status.FINISHED
            job.timeCompleted = datetime.utcnow()
            
            # Copy results back
            remote_output_dir = os.path.join(self.hpc.remote_job_dir, str(job.id), "output")
            local_output_dir = os.path.join(settings.LOCAL_JOB_DIRECTORY, str(job.id), "output")
            self.hpc.copy_from_remote(remote_output_dir, local_output_dir)
            
            # send_email(user_email, f"Job {job.id} Finished", "Your job has completed.")

        elif status == "FAILED":
            print(f"Job {job.id} failed.")
            job.status = Status.FAILED
            job.timeCompleted = datetime.utcnow()
            # send_email(user_email, f"Job {job.id} Failed", "Your job has failed on the HPC.")
            
        elif status == "RUNNING":
            print(f"Job {job.id} is still running.")
            
        else: # UNKNOWN or other states
            print(f"Job {job.id} has an unknown status: {status}")

        self.db.commit()


