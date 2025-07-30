# plugins/base_connector.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.job_enums import Status

class BaseConnector(ABC):
    """
    Abstract Base Class for execution connectors.
    Defines the interface for interacting with a compute environment,
    whether it's a remote HPC or a local cluster.
    """

    @abstractmethod
    def prepare_job_environment(
            self,
            job_id: int,
            params_dict: Dict[str, Any],
            input_file_local_path: Optional[str]
        ) -> Optional[str]:
        """
        Prepares the environment for a job run.
        This includes creating directories, writing parameter files, and staging input data.

        Parameters
        ----------
            job_id
                The unique ID of the job.
            params_dict
                A dictionary of parameters to be written to a JSON file.
            input_file_local_path
                The local path to an input file that needs to be staged.

        Results
        -------
            The path to the parameters file on the cluster, or None if 
            preparation fails.
        """
        pass

    @abstractmethod
    def submit_job(
            self,
            job_id: int,
            cluster_params_path: str
        ) -> Optional[int]:
        """
        Submits the job to the cluster's scheduler.

        Parameters
        ----------
            job_id
                The unique ID of the job.
            cluster_params_path
                The path to the parameters file on the cluster.

        Results
        -------
            The scheduler's job ID, or None if submission fails.
        """
        pass

    @abstractmethod
    def get_job_status(self, scheduler_job_id: int) -> Status:
        """
        Checks the status of a job on the cluster.

        Parameters
        ----------
            scheduler_job_id
                The scheduler's job ID.

        Results
        -------
            A Status enum state representing the job status (e.g.,
            Status.RUNNING, Status.COMPLETED, Status.FAILED).
        """
        pass

    @abstractmethod
    def retrieve_job_results(self, job_id: int) -> bool:
        """
        Retrieves the results of a completed job.
        For remote connectors, this copies data back. For local ones, it might
        be a no-op.

        Parameters
        ----------
            job_id
                The unique ID of the job.

        Results
        -------
            True if successful, False otherwise.
        """
        pass
