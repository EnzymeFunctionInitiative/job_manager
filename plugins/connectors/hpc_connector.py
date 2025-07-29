# plugins/connectors/hpc_connector.py

import os
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional
import logging

from config import settings
from plugins.base_connector import BaseConnector
from app.job_enums import Status
from app.job_logger import logger_names

module_logger = logging.getLogger(logger_names.CONNECTOR)

class Connector(BaseConnector):
    """
    Connector for a remote HPC cluster accessed via SSH/SCP.
    """

    def __init__(self):
        self.hostname = settings.HPC_HOSTNAME
        self.username = settings.HPC_USERNAME
        self.ssh_key_path = settings.HPC_SSH_KEY_PATH
        self.remote_base_dir = settings.REMOTE_JOB_DIRECTORY
        self.dry_run = settings.DRY_RUN

    def _execute_remote_command(self, command):
        if self.ssh_key_path:
            ssh_command = ["ssh", "-i", self.ssh_key_path, f"{self.username}@{self.hostname}", command]
        else:
            ssh_command = ["ssh", f"{self.username}@{self.hostname}", command]
        try:
            result = subprocess.run(ssh_command, capture_output=True, text=True, check=True)
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            module_logger.error(
                "Error executing remote command: %s\nStderr: %s",
                command,
                e.stderr
            )
            return None, e.stderr

    def _copy_to_remote(self, local_path, remote_path):
        if self.ssh_key_path:
            scp_command = ["scp", "-i", self.ssh_key_path, local_path, f"{self.username}@{self.hostname}:{remote_path}"]
        else:
            scp_command = ["scp", local_path, f"{self.username}@{self.hostname}:{remote_path}"]
        try:
            subprocess.run(scp_command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            module_logger.error(
                "Error copying to remote.",
                exc_info = e
            )
            return False

    def _copy_from_remote(self, remote_path, local_path):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        if self.ssh_key_path:
            scp_command = ["scp", "-r", "-i", self.ssh_key_path, f"{self.username}@{self.hostname}:{remote_path}", local_path]
        else:
            scp_command = ["scp", "-r", f"{self.username}@{self.hostname}:{remote_path}", local_path]
        try:
            subprocess.run(scp_command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            module_logger.error(
                "Error copying from remote.",
                exc_info = e
            )
            return False

    def prepare_job_environment(self, job_id: int, params_dict: Dict[str, Any], input_file_local_path: Optional[str]) -> Optional[str]:
        """Prepares the job environment on the remote HPC."""
        remote_job_dir = os.path.join(self.remote_base_dir, str(job_id))
        command = f"mkdir -p {remote_job_dir}"
        module_logger.info(
            "The remote working directory for Job %s is being prepared:\n\t%s",
            command
        )
        if self.dry_run:
            module_logger.info(
                "Input files for Job %s are not being prepared due to dry_run.",
                job_id
            )
            return os.path.join(remote_job_dir, "fake_params.json")

        self._execute_remote_command(command)

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Write params file locally first
                local_params_path = os.path.join(temp_dir, "params.json")
                with open(local_params_path, 'w') as f:
                    json.dump(params_dict, f, indent=4)

                # Copy params file to remote
                remote_params_path = os.path.join(remote_job_dir, "params.json")
                module_logger.info("Job %s has files transferred from %s to %s",
                    job_id,
                    local_params_path,
                    remote_params_path
                )
                if not self._copy_to_remote(local_params_path, remote_params_path):
                    return None

                # Copy input file if it exists
                if input_file_local_path:
                    remote_input_path = os.path.join(remote_job_dir, os.path.basename(input_file_local_path))
                    if not self._copy_to_remote(input_file_local_path, remote_input_path):
                        return None
                
                return remote_params_path
            except (IOError, OSError) as e:
                module_logger.error(
                    "Failed to prepare local job environment for job %s.",
                    job_id,
                    exc_info = e
                )
                return None

    def submit_job(self, job_id: int, cluster_params_path: str, nf_pipeline: str) -> Optional[int]:
        """Submits the job to the remote scheduler."""
        remote_job_path = os.path.dirname(cluster_params_path)
        
        nextflow_pipeline_path = settings.REMOTE_NEXTFLOW_PIPELINE_DIR + f"/{nf_pipeline}/{nf_pipeline}.nf"
        config_path = settings.REMOTE_NEXTFLOW_CONFIG_PATH + f"/{nf_pipeline}/slurm.config"
        nextflow_command = (
            f"cd {remote_job_path} && "
            f"{settings.REMOTE_NEXTFLOW_PATH} -C {config_path} run {nextflow_pipeline_path} "
            f"-params-file {cluster_params_path} -w {job_path}/work"
        )
        
        sbatch_command = f"sbatch --job-name=job_{job_id} --mem=24GB --ntasks=1 --cpus-per-task=1 --partition={settings.PARTITION} --output=job_{job_id}.out --wrap='{nextflow_command}'"
        module_logger.info("Job %s is submitted:\n\t%s", job_id, sbatch_command)
        # if dry_run is True, then create a fake stdout string that shows
        # successful submission for demonstration purposes.
        if self.dry_run:
            return 1
        
        stdout, _ = self._execute_remote_command(sbatch_command)
        if stdout and "Submitted batch job" in stdout:
            try:
                return int(stdout.split()[-1])
            except (ValueError, IndexError):
                module_logger.error(
                    "Could not parse job ID from sbatch output: %s.",
                    stdout,
                )
        return None

    def get_job_status(self, scheduler_job_id: int) -> Status:
        """Checks job status using remote sacct."""
        command = f"sacct -j {scheduler_job_id} --format=State --noheader"
        module_logger.info("Check job status:\n\t%s", command)
        # if dry_run is True, then create a fake stdout string that shows
        # successful completion for demonstration purposes.
        if self.dry_run:
            return Status.FINISHED
        
        stdout, _ = self._execute_remote_command(command)
        if stdout:
            status = stdout.splitlines()[0].strip().upper()
            if "COMPLETED" in status: return Status.FINISHED
            if "FAILED" in status or "CANCELLED" in status: return Status.FAILED
            if "RUNNING" in status or "PENDING" in status: return Status.RUNNING
        return Status.UNKNOWN

    def retrieve_job_results(self, job_id: int) -> bool:
        """Copies results from the remote HPC to the local filesystem."""
        remote_output_dir = os.path.join(self.remote_base_dir, str(job_id))
        local_output_dir = os.path.join(settings.LOCAL_JOB_DIRECTORY, str(job_id))
        module_logger.info(
            "Copying results from %s to %s.",
            remote_output_dir,
            local_output_dir
        )
        
        if self.dry_run:
            return True
        
        return self._copy_from_remote(remote_output_dir, local_output_dir)
