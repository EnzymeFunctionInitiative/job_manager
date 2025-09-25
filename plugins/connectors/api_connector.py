# plugins/connectors/api_connector.py

from dataclasses import dataclass
from enum import Enum
from io import BytesIO
import json
import logging
import os
import tempfile
from typing import Tuple, Dict, List, Any, Optional
import zipfile

import requests

from config import settings
from plugins.base_connector import BaseConnector
from app.job_enums import Status
from app.job_logger import logger_names
from app.models import Job

module_logger = logging.getLogger(logger_names.CONNECTOR)

# set string constants for API inputs (params, json, data, headers, etc)
api_file_field_str = "X-Filename"
api_job_str = "job_id"

class RequestMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

@dataclass
class ApiResponse:
    response: Optional[requests.Response] = None
    error: Optional[str] = None

    @property
    def status_code(self) -> int:
        """
        property, enable easy access the response.status_code while also
        handling instances where the requests call failed.
        """
        return self.response.status_code if self.response else 0

    @property
    def content_length(self) -> int:
        """
        property, enable easy access to the header's Content-Length key (if
        present) to determine if content needs to be streamed or can be gathered
        as a whole. Note: `response.headers` is a case-insensitive dictionary.
        """
        return (
            self.response.headers.get("content-length", 0)
            if self.response else 0
        )

    def handle_errors(self) -> str:
        """
        given an error string or fail http status code, determine the reason
        for the failure and handle appropriately. For example, an API rate limit
        may be in place that needs to be caught that causes the job manager to
        end without undue updates to the Job table.
        """
        pass

    #@property
    #def typed_content(self):
    #    """
    #    property, enable easy access to the content-type information in the
    #    response header dict so that the content can be handled appropriately
    #    """
    #    


class Connector(BaseConnector):
    """
    Connector for a remote HPC cluster accessed via a API.
    """

    def __init__(self):
        self.dry_run = settings.DRY_RUN

        # root API url
        self.base_api_url = settings.API_BASE_URL
        # web hook strings to be added to the base_api_url
        self.upload = settings.API_UPLOAD_HOOK
        self.download = settings.API_DOWNLOAD_HOOK
        self.ls = settings.API_LS_HOOK
        self.submit = settings.API_SUBMIT_HOOK
        self.check_status = settings.API_CHECK_STATUS_HOOK
        # settings.API_HEADER can be bare-bones, just containing the necessary
        # details to access the API.
        if settings.API_HEADER:
            self.base_header = (
                settings.API_HEADER |
                {"Content-Type": "application/octet-stream"}
            )  # by default, assume content type is binary
        else:
            self.base_header = {"Content-Type": "application/octet-stream"}


    def _request_api(
            self,
            method: str,
            url: str,
            **kwargs
        )-> Tuple[int, Dict[str,str]]:
        """
        Wrapper function for the requests.request() method that returns an
        data class containing the response.

        Arguments
        ---------
            method
                str, method to be used by the request.Request object to connect
                to the API.
            url
                str, full URL string specifying the API webhook to be used.
            **kwargs
                accepted keyword arguments for the requests.requests() method.
                Some important keywords and values are:
                    params
                        dict, list of tuples, or bytes to send in the query
                        string for the Request.
                    json
                        str, json serializable Python object to send in the body
                        of the Request.
                    data
                        dict, list of tuples, bytes, or file-like object to send
                        in the body of the Request.
                    headers
                        dict of HTTP Headers to send with the Request.
                    stream
                        bool, set to True if response.content will be a large
                        file that should not be stored in memory wholely.

                See the rest of the requests.request() and .post() documentation
                for further details.

        Returns
        -------
            ApiResponse
                dataclass object, containing the response and error message
                as well as various properties to enable ease of use in the
                interface methods.
        """
        try:
            return ApiResponse(
                response = requests.request(method, url, **kwargs)
            )
        except requests.exception.RequestException as e:
            return ApiResponse(error = str(e))


    ###
    # interface methods
    ###
    def prepare_job_environment(
            self,
            job_id: int,
            params_dict: Dict[str, Any],
            input_file_local_paths: Optional[List[str]]
        ) -> Optional[str]:
        """
        Prepares the job environment on the remote HPC via API POST call.
        Steps are as follows:
            1) create params file locally,
            2) gather params and other input file(s) into a local zip file
            3) transfer via API call the zip file to the HPC machine
            4) remove the zip file after successful transfer
            5) return the path to the zip file on the HPC machine

        Arguments
        ---------
            job_id
                int, 'id' attribute associated with the job to be run.
            params_dict
                dict, contains the nextflow parameters to be written to file on
                the remote compute resource.
            input_file_local_path
                list of strings, contains paths to files to be transferred from
                the local storage space to the remote compute resource.

        Returns
        -------
            compute_path,
                str, path to the zip file location on the compute resource.
        """
        # catch dry runs
        if self.dry_run:
            module_logger.info(
                f"Input files for Job {job_id} are not being prepared due to"
                + f" dry_run."
            )
            return "fake/path"

        # make a temp directory within which the params and zip file are written
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write params file locally first
            local_params_path = os.path.join(temp_dir, "params.json")
            with open(local_params_path, 'w') as f:
                json.dump(params_dict, f, indent=4)

            # write the zip file, smartly creating archive names for files so
            # that unzipping creates a clean working directory for the to-be
            # submitted job
            zip_file_path = os.path.join(temp_dir, f"{job_id}_inputs.zip")
            with zipfile.ZipFile(zip_file_path, "w") as zip_file:
                zip_file.write(
                    local_params_path,
                    arcname = f"params.json"
                )
                # copy input files if they exist
                for file_path in input_file_local_paths:
                    if os.path.isfile(file_path):
                        base_name = os.path.basename(file_path)
                        zip_file.write(
                            file_path,
                            f"{base_name}"
                        )

            # send the zip file to the compute resource via the API
            prep_url = self.base_api_url + self.upload
            headers = self.base_header | {
                self.file_field_str: f"{job_id}_inputs.zip",
                "Content-Type": "application/zip"
            }

            # open the zip and send it via a POST request
            with open(zip_file_path, "rb") as data:
                result = self._request_api(
                    RequestMethod.POST.name,
                    prep_url,
                    data = data,
                    headers = headers
                )

            # basic validation that the API call was successful
            if result.error or result.status_code != 200:   # check for http return codes
                module_logger.info(
                    "Transfer of input files for Job %s failed.",
                    job_id
                )
                return None

            ## check that the zip file got moved by listing the directory's
            ## content. NOTE: this code expects specific output from an API 
            ## call
            #result = self._request_api(
            #    RequestMethod.GET.name,
            #    self.base_api_url + self.ls,
            #    headers = self.base_header | {"Content-Type": "application/json"}
            #    data = {"job_id": job_id}
            #)
            #file_into = json.loads(result.response.content.decode("utf-8"))
            #for file in file_info:
            #    if file.get("name") == f"{job_id}_inputs.zip":
            #        assert file.get("size") == os.path.getsize(zip_file_path)
            #        break

        module_logger.info(
            "Transfer of input files for Job %s was successful.",
            job_id
        )
        # NOTE: why did I choose to return a path here?
        return f"{job_id}_inputs.zip"

    def submit_job(
            self,
            job_id: int,
            params_path: str,
            nf_pipeline: str
        ) -> Optional[str | int]:
        """
        Submits the job to the remote HPC via API POST call.

        Arguments
        ---------
            job_id
                int, 'id' attribute associated with the job to be run.
            params_path
                str, path to the nf param file; useable to get the working_dir
            nf_pipeline
                str, specify the type of EFI job is to be started

        Returns
        -------
            scheduler_job_id,
                int or str, the job number given by the HPC scheduler to the
                submitted parent 'nextflow run' call
        """
        
        # catch dry runs
        if self.dry_run:
            module_logger.info(
                f"Job {job_id} is not being submitted via the API due to"
                + " dry_run."
            )
            return 1

        # prep api dictionaries; this is API specific so just providing an
        # example of fields to be used
        
        # NOTE: don't use params use json or data kwarg; requires update to the API code
        params = {"job_id": job_id, "pipeline": nf_pipeline}
        submit_url = self.base_api_url + self.submit
        result = self._request_api(
            RequestMethod.POST.name,
            submit_url, 
            params = params,    # NOTE: ideally this info is not sent via params
            headers = self.base_header | {"Content-Type": "application/json"}
        )
        
        # basic validation that the API call was successful
        if result.error or result.status_code != 200:
            module_logger.info(
                "Submission of Job %s to the compute resource queue failed.",
                job_id
            )
            return None

        # retrieve the scheduler's Job ID for the submitted job
        # NOTE: once again, this is API specific, but assume that a scheduler id
        # is returned from the API call. 
        response_dict= json.loads(result.response.content.decode("utf-8"))
        # NOTE: check whether response_dict can be case-insenstive else need to
        # ensure that the returned json data is correctly case'd
        scheduler_id = response_dict.get("scheduler_id", None)
        if not scheduler_id:
            module_logger.info(
                "Submission of Job %s successfully called the API but failed\n"
                + "return a scheduler job id."
            )
        return scheduler_id

    def get_job_status(
            self,
            scheduler_job_id: int
        ) -> Status:
        """
        Checks the job's status on the remote HPC via API POST call.

        Arguments
        ---------
            scheduler_job_id
                int, 'schedulerJobId' attribute associated with the running job.

        Returns
        -------
            status,
                Status enum, the enum value associated with the returned job
                state.
        """
        # catch dry runs
        if self.dry_run:
            module_logger.info(
                f"The job {job_id} is not being checked for status changes via"
                + " the API due to dry_run."
            )
            return Status.FINISHED
        
        # prep api dictionaries; this is API specific so just providing an
        # example of fields to be used
        check_status_url = self.base_api_url + self.check_status
        data = {"job_id": scheduler_job_id}

        result = self._request_api(
            RequestMethod.POST.name,
            check_status_url, 
            data = json.dumps(data),
            headers = self.base_header | {"Content-Type": "application/json"}
        )

        # basic validation that the API call was successful
        if result.error or result.status_code != 200:
            module_logger.info(
                "Checking the status of Job %s failed.",
                job_id
            )
            return None
        
        # retrieve the scheduler's status (qstat, sacct, etc) results 
        # NOTE: once again, this is API specific, but assume that a dict of 
        # job information is returned from the API call. 
        response_dict= json.loads(result.response.content.decode("utf-8"))
        status_str = response_dict.get("status", "failed")
        # get the Status Flag enum based on that status string
        # NOTE: once again, this is API/scheduler dependent.
        status = self.parse_status_string(status_str)
        return status

    def retrieve_job_results(self, job: Job) -> bool:
        """
        Submits a "retrieve" task via API POST call that gathers all result
        files from the compute resource and stashes them in the local storage
        space.

        Arguments
        ---------
            job
                Job, Job table row object.

        Returns
        -------
            compute_path,
                str, path to the file location on the compute resource.
        """
        # catch dry runs
        if self.dry_run:
            module_logger.info(
                f"Result files for Job {job.id} are not being gathered due via"
                + " the API due to dry_run."
            )
            return True

        # prep api dictionaries; this is API specific so just providing an
        # example of fields to be used
        download_url = self.base_api_url + self.download
        headers = self.base_header | {"Content-Type": "application/zip"}
        params = {"file": f"{job.id}/results.zip"}

        # NOTE: this assumes the to-be-gathered zip file can be contained in the
        # current computer's memory. Need to implement either streaming of the
        # contents in chunks or some other way of handling LARGE files.
        result = self._request_api(
            RequestMethod.GET.name,
            download_url, 
            params = params,
            headers = headers,
            stream = True   # needed if the zip file is to be iterated by chunk
        )

        # basic validation that the API call was successful
        if result.error or result.status_code != 200:
            module_logger.info(
                "Gathering the results zip file of Job %s failed.",
                job_id
            )
            return None
      
        # contents is a bytes object of the full results.zip file gathered via
        # the API call. Handle that zip file appropriately.
        results_zip_path = f"{settings.LOCAL_JOB_DIRECTORY}/{job.id}/results.zip"
        output_dir_path = os.path.dirname(os.path.realpath(results_zip_path))
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # the result.response.content zip file may be large so check the length
        # first and determine whether it needs to be written to a zip file on
        # storage or if it can be streamed from the response straight to
        # extraction of all files.
        # length cutoff is hardset at 1 GB for now. 
        if result.content_length < 10**9:
            z = zipfile.ZipFile(io.BytesIO(result.response.content))
            try:
                z.extractall(output_dir_path)
            
            except zipfile.BadZipFile as e:
                print(f"Unzipping {zip_file_path} failed.\n{e}")
                raise
            except OSError as e:
                print(
                    f"OS differences caused unzipping {zip_file_path} to fail."
                    + f"\n{e}")
                raise
            finally:
                z.cloes()
            ## NOTE: uncomment if the zip file should be written to storage too
            #with open(results_zip_path, "wb") as out_zip:
            #    out_zip.write(result.response.content)

        else:
            with open(results_zip_path, "wb") as out_zip:
                for chunk in result.response.iter_chunk(chunk_size = 8192):
                    if chunk:
                        out_zip.write(chunk)
            with zipfile.ZipFile(results_zip_path) as out_zip:
                z.extractall(output_dir_path)
        
        # done handling the zip file
        module_logger.info(
            "Results for Job %s were gathered via API and saved to %s.",
            job.id,
            output_dir_path
        )
        return True

