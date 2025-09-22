# app/job_handler.py

import os
from typing import Dict, Any
from datetime import datetime
import json
import logging

from config import settings
from app.job_enums import Status, Pipeline, ImportMode
from app.models import Job, FilenameParameters
from app.results_parser import ResultsParser
#from plugins.notification import send_email
from app.job_logger import logger_names

STATUS_KEY = "status"
JOBID_KEY = "schedulerJobId"
TIME_STARTED_KEY = "timeStarted"
TIME_COMPLETED_KEY = "timeCompleted"
FILTER_KEY = "filter"
IMPORT_MODE_KEY = "import_mode"
FIN_OUTPUT_DIR_KEY = "final_output_dir"

module_logger = logging.getLogger(logger_names.JOB_HANDLER)

class JobHandler:
    def __init__(self, connector_instance):
        self.connector = connector_instance
        self.parser = ResultsParser()
        self.dry_run = settings.DRY_RUN

    def process_new_job(self, job: Job) -> Dict[str, Any]:
        """
        Handles the submission of a new job by delegating to the connector.
        1) Check whether uploaded files are present for the job.
        2) Call the `self._create_parameter_dict()` method on the job object
           to create a dictionary of important input parameters. Send this
           dictionary to the `connector.prepare_job_environment()` method to
           be handled appropriately for the site-specific setup.
        3) Having prepared the working space, run the job on the compute
           resource by way of the `connector.submit_job()` method.
        4) Make an update dictionary, filled with any new values to be passed
           to the job object.

        Arguments
        ---------
            job
                Job class instance. Expected to have at least the `id` and
                `pipeline` attributes.
               
        Returns
        -------
            A dictionary of updatable keys and associated new values to be used
            to update the job object. See the job object's
            `get_updatable_attrs()` method and attributes labeled with
            `is_updatable` meta-tags.

                and a set of interface methods:
                    `get_parameters_dict()`,
                    `get_filter_parameters()`,
                    `get_updatable_attrs()`,
                    `get_result_key_mapping()`

        """
        pipeline = str(job.pipeline)
        module_logger.info(
            "Processing NEW job: %s is a %s job",
            job.id,
            pipeline
        )
        
        # 1. Get input file path, if it exists.
        input_file = None
        if isinstance(job, FilenameParameters) and job.jobFilename:
            file_path = os.path.join(
                settings.LOCAL_INPUT_FILE_SOURCE_DIR,
                job.jobFilename
            )
            if os.path.exists(file_path):
                input_file = file_path
            else:
                module_logger.info(
                    "Input file not found for job %s: %s. Marking job as"
                    + " FAILED.",
                    job.id,
                    file_path
                )
                return {STATUS_KEY: Status.FAILED}

        # 2. Prepare the job environment using the connector.
        params = self._create_parameter_dict(job)
        cluster_params_path = self.connector.prepare_job_environment(
            job.id,
            params,
            input_file
        )
        if not cluster_params_path:
            module_logger.info(
                "Failed to prepare job environment for job %s. Marking job as"
                + " FAILED.",
                job.id
            )
            return {STATUS_KEY: Status.FAILED}

        # 3. Submit the job using the connector.
        scheduler_job_id = self.connector.submit_job(
            job.id,
            cluster_params_path,
            pipeline,
        )

        # 4. Gather updates to be pushed to the Job table.
        updates_dict = {}
        if scheduler_job_id:
            updates_dict[STATUS_KEY] = Status.RUNNING
            updates_dict[JOBID_KEY] = scheduler_job_id
            updates_dict[TIME_STARTED_KEY] = datetime.utcnow()
            module_logger.info(
                "Job %s started with scheduler ID: %s",
                job.id,
                scheduler_job_id
            )
            # send_email(user_email, f"Job {job.id} Started", "Your job is now running.")
        else:
            updates_dict[STATUS_KEY] = Status.FAILED
            module_logger.info("Failed to start job %s on cluster.", job.id)
            # send_email(user_email, f"Job {job.id} Failed", "Your job failed to start.")
        
        return updates_dict

    def process_running_job(self, job: Job):
        """
        Checks the status of a running job by delegating to the connector. If
        the `connector.get_job_status()` returns Status.FINISHED, gather the
        result files by delegating that to the connector as well via the
        `connector.retrieve_job_results()` method. Process the result files to
        gather tabular values via the `self._process_results()` method.

        Arguments
        ---------
            job
                Job class instance. Expected to have at least the `id` and
                `pipeline` attributes.
               
        Returns
        -------
            A dictionary of updatable keys and associated new values to be used
            to update the job object. See the job object's
            `get_updatable_attrs()` method and attributes labeled with
            `is_updatable` meta-tags.
        """
        module_logger.info(
            "Checking RUNNING job: %s (Scheduler ID: %s)",
            job.id,
            job.schedulerJobId
        )
        
        # connector.get_job_status() returns a Status Enum Flag not a string
        status = self.connector.get_job_status(job.schedulerJobId)

        updates_dict = {}
        if status == Status.RUNNING:
            module_logger.info("Job %s is still running.", job.id)
            
        elif status == Status.FAILED:
            module_logger.info("Job %s failed.", job.id)
            updates_dict[STATUS_KEY] = status
            # should timeCompleted be a time reported from the scheduler or
            # just when the job_manager checks for completion?
            updates_dict[TIME_COMPLETED_KEY] = datetime.utcnow()
            # send_email(user_email, f"Job {job.id} Failed", "Your job has failed on the cluster.")
            
        elif status == Status.FINISHED:
            module_logger.info("Job %s finished successfully.", job.id)
            updates_dict[STATUS_KEY] = status
            
            # Retrieve results using the connector
            self.connector.retrieve_job_results(job)
            
            # Parse result file(s)
            results_dict = self._process_results(job)
            updates_dict.update(results_dict)
           
            # update the timeCompleted column
            updates_dict[TIME_COMPLETED_KEY] = datetime.utcnow()

            # send_email(user_email, f"Job {job.id} Finished", "Your job has completed.")

        else: # UNKNOWN or other states
            module_logger.info(
                "Job %s has an unknown status: %s",
                job.id,
                status
            )
        
        return updates_dict

    def _process_results(self, job: Job) -> Dict[str, Any]:
        """
        A job has completed but important summary data needs to be pulled from
        results files such as stats.json so the associated columns in
        the Job table can be updated.
        """
        results_dict = {}
        ## 1. check for completion by looking for touched files
        #if not self.parser.check_files(job):
        #    print(f"Job {job.id} is missing result output files.")
        #    results_dict[STATUS_KEY] = Status.FAILED

        # 2. process the stats.json file (and other files if need be)
        #    parser.parse_results() returns a dict, which is immediately used
        #    to update the results_dict.
        results_dict.update(self.parser.parse_results(job))

        return results_dict

    def _create_parameter_dict(self, job: Job) -> Dict[str, Any]:
        """
        Create the parameter dictionary containing all relevant key:value pairs
        to run the nextflow pipeline.
        """
        # gather the initial dictionary of parameters from the Job object
        params = job.get_parameters_dict()
        
        # add the hardcoded parameters defined in the settings.py code
        params.update(settings.NEXTFLOW_PARAMS)
        params.update(
            {FIN_OUTPUT_DIR_KEY: settings.REMOTE_JOB_DIRECTORY + f"/{job.id}"}
        )
        
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


