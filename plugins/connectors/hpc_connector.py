# plugins/connectors/hpc_connector.py

import os
import json
import subprocess
import tempfile
from typing import Dict, Any, Optional
from config import settings
from plugins.base_connector import BaseConnector

class Connector(BaseConnector):
    """
    Connector for a remote HPC cluster accessed via SSH/SCP.
    """

    def __init__(self):
        self.hostname = settings.HPC_HOSTNAME
        self.username = settings.HPC_USERNAME
        self.ssh_key_path = settings.HPC_SSH_KEY_PATH
        self.remote_base_dir = settings.REMOTE_JOB_DIRECTORY

    def _execute_remote_command(self, command):
        ssh_command = ["ssh", "-i", self.ssh_key_path, f"{self.username}@{self.hostname}", command]
        try:
            result = subprocess.run(ssh_command, capture_output=True, text=True, check=True)
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error executing remote command: {command}\nStderr: {e.stderr}")
            return None, e.stderr

    def _copy_to_remote(self, local_path, remote_path):
        scp_command = ["scp", "-i", self.ssh_key_path, local_path, f"{self.username}@{self.hostname}:{remote_path}"]
        try:
            subprocess.run(scp_command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error copying to remote: {e}")
            return False

    def _copy_from_remote(self, remote_path, local_path):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        scp_command = ["scp", "-r", "-i", self.ssh_key_path, f"{self.username}@{self.hostname}:{remote_path}", local_path]
        try:
            subprocess.run(scp_command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error copying from remote: {e}")
            return False

    def prepare_job_environment(self, job_id: int, params_dict: Dict[str, Any], input_file_local_path: Optional[str]) -> Optional[str]:
        """Prepares the job environment on the remote HPC."""
        remote_job_dir = os.path.join(self.remote_base_dir, str(job_id))
        self._execute_remote_command(f"mkdir -p {remote_job_dir}")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Write params file locally first
                local_params_path = os.path.join(temp_dir, "params.json")
                with open(local_params_path, 'w') as f:
                    json.dump(params_dict, f, indent=4)

                # Copy params file to remote
                remote_params_path = os.path.join(remote_job_dir, "params.json")
                if not self._copy_to_remote(local_params_path, remote_params_path):
                    return None

                # Copy input file if it exists
                if input_file_local_path:
                    remote_input_path = os.path.join(remote_job_dir, os.path.basename(input_file_local_path))
                    if not self._copy_to_remote(input_file_local_path, remote_input_path):
                        return None
                
                return remote_params_path
            except (IOError, OSError) as e:
                print(f"Failed to prepare remote job environment for job {job_id}: {e}")
                return None

    def submit_job(self, job_id: int, cluster_params_path: str) -> Optional[int]:
        """Submits the job to the remote scheduler."""
        remote_job_path = os.path.dirname(cluster_params_path)
        
        nextflow_pipeline = settings.REMOTE_NEXTFLOW_PIPELINE_DIR + f"/{nf_pipeline[0]}/{nf_pipeline[0]}.nf"
        nextflow_command = (
            f"cd {remote_job_path} && "
            f"{settings.REMOTE_NEXTFLOW_PATH} -C {settings.REMOTE_NEXTFLOW_CONFIG_PATH} run {nextflow_pipeline} "
            f"-params-file {cluster_params_path} -w {job_path}/work"
        )
        
        sbatch_command = f"sbatch --job-name=job_{job_id} --output=job_{job_id}.out --wrap='{nextflow_command}'"
        stdout, _ = self._execute_remote_command(sbatch_command)
        
        if stdout and "Submitted batch job" in stdout:
            try:
                return int(stdout.split()[-1])
            except (ValueError, IndexError):
                print(f"Could not parse job ID from sbatch output: {stdout}")
        return None

    def get_job_status(self, scheduler_job_id: int) -> str:
        """Checks job status using remote sacct."""
        command = f"sacct -j {scheduler_job_id} --format=State --noheader"
        stdout, _ = self._execute_remote_command(command)
        if stdout:
            status = stdout.splitlines()[0].strip()
            if "COMPLETED" in status: return "COMPLETED"
            if "FAILED" in status or "CANCELLED" in status: return "FAILED"
            if "RUNNING" in status or "PENDING" in status: return "RUNNING"
        return "UNKNOWN"

    def retrieve_job_results(self, job_id: int) -> bool:
        """Copies results from the remote HPC to the local filesystem."""
        remote_output_dir = os.path.join(self.remote_base_dir, str(job_id), "output")
        local_output_dir = os.path.join(settings.LOCAL_JOB_DIRECTORY, str(job_id))
        print(f"Copying results from {remote_output_dir} to {local_output_dir}")
        return self._copy_from_remote(remote_output_dir, local_output_dir)
