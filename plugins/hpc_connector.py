# plugins/hpc_connector.py

import os
import subprocess
from config import settings

class HPCConnector:
    """
    A plugin to handle all interactions with the HPC cluster via SSH and SCP.
    This class should be customized for the specific HPC environment (e.g., Slurm, PBS).
    """

    def __init__(self):
        self.hostname = settings.HPC_HOSTNAME
        self.username = settings.HPC_USERNAME
        self.ssh_key_path = settings.HPC_SSH_KEY_PATH
        self.remote_job_dir = settings.REMOTE_JOB_DIRECTORY

    def _get_ssh_command(self, remote_command):
        """Constructs the full SSH command."""
        return [
            "ssh",
            "-i", self.ssh_key_path,
            f"{self.username}@{self.hostname}",
            remote_command
        ]
    
    def _get_scp_to_remote_command(self, local_path, remote_path):
        """Constructs the full SCP command to copy to the remote."""
        return [
            "scp",
            "-i", self.ssh_key_path,
            local_path,
            f"{self.username}@{self.hostname}:{remote_path}"
        ]

    def _get_scp_from_remote_command(self, remote_path, local_path):
        """Constructs the full SCP command to copy from the remote."""
        return [
            "scp",
            "-i", self.ssh_key_path,
            f"{self.username}@{self.hostname}:{remote_path}",
            local_path
        ]

    def execute_remote_command(self, command):
        """Executes a command on the remote HPC."""
        ssh_command = self._get_ssh_command(command)
        try:
            result = subprocess.run(ssh_command, capture_output=True, text=True, check=True)
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error executing remote command: {e}")
            print(f"Stderr: {e.stderr}")
            return None, e.stderr

    def copy_to_remote(self, local_path, remote_path):
        """Copies a file or directory to the remote HPC."""
        scp_command = self._get_scp_to_remote_command(local_path, remote_path)
        try:
            subprocess.run(scp_command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error copying to remote: {e}")
            return False

    def copy_from_remote(self, remote_path, local_path):
        """Copies a file or directory from the remote HPC."""
        # Ensure the local directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        scp_command = self._get_scp_from_remote_command(remote_path, local_path)
        try:
            subprocess.run(scp_command, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error copying from remote: {e}")
            return False

    def create_remote_directory(self, job_id):
        """Creates a directory for a job on the HPC."""
        remote_path = os.path.join(self.remote_job_dir, str(job_id))
        self.execute_remote_command(f"mkdir -p {remote_path}")
        return remote_path

    def start_nextflow_job(self, job_id, params_file_path):
        """
        Starts a Nextflow job on the HPC.
        This is a placeholder and needs to be adapted for your HPC's scheduler (e.g., Slurm).
        """
        remote_job_path = os.path.join(self.remote_job_dir, str(job_id))
        remote_params_path = os.path.join(remote_job_path, os.path.basename(params_file_path))

        # This command assumes you are using a scheduler like Slurm and `sbatch`.
        # You will need to create a submission script template.
        # For simplicity, we are running nextflow directly here.
        # A more robust solution would use a submission script.
        nextflow_command = (
            f"cd {remote_job_path} && "
            f"{settings.REMOTE_NEXTFLOW_PATH} run {settings.REMOTE_NEXTFLOW_PIPELINE} "
            f"-params-file {remote_params_path}"
        )
        
        # Example for Slurm: wrap the nextflow command in an sbatch script
        # sbatch_script = f"""#!/bin/bash
        # #SBATCH --job-name=job_{job_id}
        # #SBATCH --output=job_{job_id}.out
        # #SBATCH --error=job_{job_id}.err
        # {nextflow_command}
        # """
        # self.execute_remote_command(f"echo '{sbatch_script}' > {remote_job_path}/submit.sh")
        # stdout, stderr = self.execute_remote_command(f"sbatch {remote_job_path}/submit.sh")
        
        # For now, we run it directly and assume it returns a job ID.
        # This part is HIGHLY dependent on your HPC setup.
        stdout, stderr = self.execute_remote_command(nextflow_command)
        
        if stdout and "Submitted batch job" in stdout: # Example for Slurm
            hpc_job_id = int(stdout.split()[-1])
            return hpc_job_id
        return None

    def get_job_status(self, hpc_job_id):
        """
        Checks the status of a job on the HPC.
        This needs to be implemented for your specific scheduler (e.g., `sacct` for Slurm).
        """
        # Example for Slurm:
        command = f"sacct -j {hpc_job_id} --format=State --noheader"
        stdout, stderr = self.execute_remote_command(command)
        if stdout:
            # The output might have multiple lines, get the primary job state
            status = stdout.splitlines()[0].strip()
            if "COMPLETED" in status:
                return "COMPLETED"
            elif "FAILED" in status or "CANCELLED" in status:
                return "FAILED"
            elif "RUNNING" in status or "PENDING" in status:
                return "RUNNING"
        return "UNKNOWN"


