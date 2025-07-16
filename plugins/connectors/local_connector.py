# plugins/local_connector.py

import os
import json
import shutil
import subprocess
from typing import Dict, List, Any, Optional
from config import settings
from plugins.base_connector import BaseConnector

class Connector(BaseConnector):
    """
    Connector for a locally accessible cluster with a shared filesystem.
    """

    def __init__(self):
        self.job_base_dir = settings.LOCAL_JOB_DIRECTORY

    def _execute_local_command(self, command, working_dir=None):
        """Executes a command on the local machine."""
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, shell=True, cwd=working_dir
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error executing local command: {command}\nStderr: {e.stderr}")
            return None, e.stderr

    def prepare_job_environment(
            self,
            job_id: int,
            params_dict: Dict[str, Any],
            input_file_local_path: Optional[str]
        ) -> Optional[str]:
        """Prepares the job environment on the shared filesystem."""
        try:
            job_dir = os.path.join(self.job_base_dir, str(job_id))
            os.makedirs(job_dir, exist_ok=True)

            # Write params file
            params_file_path = os.path.join(job_dir, "params.json")
            with open(params_file_path, 'w') as f:
                json.dump(params_dict, f, indent=4)

            # Copy input file if it exists
            if input_file_local_path:
                destination_file_path = os.path.join(job_dir, os.path.basename(input_file_local_path))
                shutil.copy(input_file_local_path, destination_file_path)

            return params_file_path
        except (IOError, OSError) as e:
            print(f"Failed to prepare local job environment for job {job_id}: {e}")
            return None

    def submit_job(
            self,
            job_id: int,
            cluster_params_path: str,
            nf_pipeline: str
        ) -> Optional[int]:
        """Submits the job to the local scheduler (e.g., Slurm)."""
        job_path = os.path.dirname(cluster_params_path)
        
        nextflow_pipeline_path = settings.REMOTE_NEXTFLOW_PIPELINE_DIR + f"/{nf_pipeline}/{nf_pipeline}.nf"
        nextflow_command = (
            f"{settings.REMOTE_NEXTFLOW_PATH} -C {settings.REMOTE_NEXTFLOW_CONFIG_PATH} run {nextflow_pipeline_path} "
            f"-params-file {cluster_params_path} -w {job_path}/work"
        )

        sbatch_command = f"echo sbatch --job-name=job_{job_id} --mem=24GB --ntasks=1 --cpus-per-task=1 --partition=efi --output=job_{job_id}.out --wrap='{nextflow_command}'"
        #sbatch_command = f"sbatch --job-name=job_{job_id} --mem=24GB --ntasks=1 --cpus-per-task=1 --partition=efi --output=job_{job_id}.out --wrap='{nextflow_command}'"
        stdout, _ = self._execute_local_command(sbatch_command, working_dir=job_path)
        
        if stdout and "Submitted batch job" in stdout:
            try:
                return int(stdout.split()[-1])
            except (ValueError, IndexError):
                print(f"Could not parse job ID from sbatch output: {stdout}")
        return None

    def get_job_status(self, scheduler_job_id: int) -> str:
        """Checks job status using local sacct."""
        command = f"sacct -j {scheduler_job_id} --format=State --noheader"
        #command = f"sacct -j {scheduler_job_id} --format=State --noheader"
        stdout, _ = self._execute_local_command(command)
        if stdout:
            status = stdout.splitlines()[0].strip()
            if "COMPLETED" in status: return "COMPLETED"
            if "FAILED" in status or "CANCELLED" in status: return "FAILED"
            if "RUNNING" in status or "PENDING" in status: return "RUNNING"
        return "UNKNOWN"

    def retrieve_job_results(self, job_id: int) -> bool:
        """No-op for local connector as results are already in the shared filesystem."""
        print(f"LocalConnector: Results for job {job_id} are already in place.")
        return True
