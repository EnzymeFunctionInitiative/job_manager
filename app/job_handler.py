# app/job_handler.py

import os
from typing import Dict, Any
from datetime import datetime
import json

from app.job_enums import Status, Pipeline, ImportMode
from app.models import Job, FilenameParameters
#from plugins.notification import send_email
from config import settings

STATUS_KEY = "status"
JOBID_KEY = "schedulerJobId"
TIME_STARTED_KEY = "timeStarted"
TIME_COMPLETED_KEY = "timeCompleted"
FILTER_KEY = "filter"
IMPORT_MODE_KEY = "import_mode"
FIN_OUTPUT_DIR_KEY = "final_output_dir"

class JobHandler:
    def __init__(self, connector_instance):
        self.connector = connector_instance

    def process_new_job(self, job: Job):
        """Handles the submission of a new job by delegating to the connector."""
        pipeline = str(job.pipeline)
        print(f"Processing NEW job: {job.id} is a {pipeline} job")
        
        # 1. Get job parameters and input file path
        input_file = None
        if isinstance(job, FilenameParameters) and job.jobFilename:
            file_path = os.path.join(settings.LOCAL_INPUT_FILE_SOURCE_DIR, job.jobFilename)
            if os.path.exists(file_path):
                input_file = file_path
            else:
                print(f"Input file not found for job {job.id}: {file_path}")
                return {STATUS_KEY: Status.FAILED}

        # 2. Prepare the job environment using the connector
        params = self._create_parameter_dict(job)
        cluster_params_path = self.connector.prepare_job_environment(job.id, params, input_file)
        if not cluster_params_path:
            print(f"Failed to prepare job environment for job {job.id}")
            return {STATUS_KEY: Status.FAILED}

        # 3. Submit the job using the connector
        scheduler_job_id = self.connector.submit_job(job.id, cluster_params_path, pipeline)

        updates_dict = {}
        updates = UpdaterNameSpace()
        if scheduler_job_id:
            updates_dict[STATUS_KEY] = Status.RUNNING
            updates_dict[JOBID_KEY] = scheduler_job_id
            updates_dict[TIME_STARTED_KEY] = datetime.utcnow()
            print(f"Job {job.id} started with scheduler ID: {scheduler_job_id}")
            # send_email(user_email, f"Job {job.id} Started", "Your job is now running.")
        else:
            updates_dict[STATUS_KEY] = Status.FAILED
            print(f"Failed to start job {job.id} on cluster.")
            # send_email(user_email, f"Job {job.id} Failed", "Your job failed to start.")
        
        return updates_dict

    def process_running_job(self, job: Job):
        """Checks the status of a running job."""
        print(f"Checking RUNNING job: {job.id} (Scheduler ID: {job.schedulerJobId})")
        
        # connector.get_job_status() returns a status string
        status = self.connector.get_job_status(job.schedulerJobId)
        # convert that status string to a Status flag
        status = Status.get_flag(status)

        updates_dict = {}
        if status == Status.RUNNING:
            print(f"Job {job.id} is still running.")
            
        elif status == Status.FAILED:
            print(f"Job {job.id} failed.")
            updates_dict["status"] = Status.FAILED
            # should timeCompleted be a time reported from the scheduler or
            # just when the job_manager checks for completion?
            updates_dict["timeCompleted"] = datetime.utcnow()
            # send_email(user_email, f"Job {job.id} Failed", "Your job has failed on the cluster.")
            
        if status == Status.FINISHED:
            print(f"Job {job.id} finished successfully.")
            updates_dict[STATUS_KEY] = Status.FINISHED
            # should timeCompleted be a time reported from the scheduler or
            # just when the job_manager checks for completion?
            updates_dict[TIME_COMPLETED_KEY] = datetime.utcnow()
            
            # Retrieve results using the connector
            self.connector.retrieve_job_results(job)
            
            # check for completion by looking for touched files

            # Parse result file(s)
            results_dict = self.process_results(job)
            updates_dict.update(results_dict)

            # send_email(user_email, f"Job {job.id} Finished", "Your job has completed.")

        else: # UNKNOWN or other states
            print(f"Job {job.id} has an unknown status: {status}")
        
        return updates_dict

    def process_results(self, job: Job) -> Dict[str, Any]:
        """ 
        A job has completed but important summary data needs to be pulled from
        results files such as stats.json so the associated columns in
        the Job table can be updated.
        """

        # create a Updates NameSpace object instance, run the Parser method to
        # process result files, then update the NameSpace obj and return that 
        # to main

        local_output_dir = os.path.join(
            settings.LOCAL_JOB_DIRECTORY, 
            str(job.id)
        )
       
        # nearly all nextflow pipelines write a stats.json file that contain
        # the respective result(s); assume the data typing in the json file is
        # deserrialized correctly. 
        with open(os.path.join(local_output_dir, "stats.json")) as stats:
            results_dict = json.load(stats)

        updates_dict= {}
        # get job-specific column names to be updated
        result_mappings = job.get_result_key_mapping()
        # loop over the key:value pairs from the nf-output json file, check 
        # whether the key maps to a column name in the Job table, and apply
        # mapping to add the value to the results_dict
        for key, val in results_dict.items():
            # get the value associated with key from the mapping dict or get key
            new_key = result_mappings.get(key, key)
            updates_dict[new_key] = val

        return updates_dict

    #def apply_updates(self, db_conn, job: Job, results_dict: Dict[str,Any]):
    #    """
    #    Contents in results_dict get pushed to the Job object, followed by a 
    #    commit() call on the database connection.
    #    """
    #    if not results_dict:
    #        print("No updates applied to the Job ({job.__repr__})")
    #        return
    #    
    #    # add an air-gap btwn updating the database by checking whether keys in
    #    # the results_dict are labeled as updatable in the jOb table.
    #    updatable_columns = job.get_updatable_attrs()
    #    # loop over the items in results_dict
    #    for key, val in results_dict.items():
    #        if key not in updatable_columns:
    #            continue
    #        setattr(job, key, val)

    #    db_conn.commit()

    def _create_parameter_dict(self, job: Job) -> Dict[str, Any]:
        """
        Create the parameter dictionary containing all relevant key:value pairs
        to run the nextflow pipeline.
        """
        # gather the initial dictionary of parameters from the Job object
        params = job.get_parameters_dict()
        
        # add the hardcoded parameters defined in the settings.py code
        params.update(settings.NEXTFLOW_PARAMS)
        params.update({FIN_OUTPUT_DIR_KEY: settings.REMOTE_JOB_DIRECTORY + f"/{job.id}"})
        
        # not all Jobs will have an "import_mode" attribute, but add it when 
        # present
        if hasattr(job, IMPORT_MODE_KEY):
            params.update({IMPORT_MODE_KEY: str(job.import_mode)})
        
        # handle parameters associated with filters for ESTGenerate jobs
        if job.pipeline == Pipeline.EST:
            filter_list = job.get_filter_parameters()
            params[FILTER_KEY] = []
            for col_name in filter_list:
                val = params.get(col_name)
                if val:
                    params[FILTER_KEY].append(f"{col_name}={val}")
                    params.pop(col_name)

        return params



