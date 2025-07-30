
# REQUIRED PARAMETERS

	* DATABASE\_URI: python string representation of the SQLAlchemy-accepted database URL. See [docs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls) for creating this string.
	* DRY\_RUN: python boolean. If True, the job manager code will be run as a dry-run where no commands will actually be run and the job database will not be updated. Else, all logged commands will be run and any resulting updates will be committed to the database.
	* LOCAL\_INPUT\_FILE\_SOURCE\_DIR: string path to a directory where _all_ input files will be stored temporarily before they are copied/transported to the compute working directory.
	* LOCAL\_JOB\_DIRECTORY: python string representation of the path where job-specific subdirectories will be made, within which input and result files are stashed for direct access from the website.
	* REMOTE\_JOB\_DIRECTORY: python string representation of the path on the remote/compute resource where job-specific subdirectories will be made, within which input and result files are stashed/written as the job runs. If using LOCAL connector, this should be equivalent to the LOCAL\_JOB\_DIRECTORY path. 
	* LOG\_FILE\_PATH: python string representation of the path where the job manager's logging file will be written. Name it something informative such as `/path/to/dir/job_manager_YYYY_MM_DD.log` to denote when the job manager began running. 
	* MAX\_NUM\_RUNNING\_JOB: Python integer representation to control how many EFI-related jobs can be actively run on the compute resource at one time.

	* EXECUTION\_CONNECTOR: python string, all uppercased. The stem of the `plugins/connectors/{EXECUTION_CONNECTOR.lower()}\_connector.py` file name. E.g. "LOCAL" maps to the `plugins/connectors/local_connector.py`. 
	* REMOTE\_NEXTFLOW\_PIPELINE\_DIR: python string representation of the path to the `pipelines/` subdirectory in the EST repo's home directory.
	* REMOTE\_NEXTFLOW\_CONFIG\_PATH: python string representation of the path to the `conf/` subdirectory in the EST repo's home directory. 
	* REMOTE\_NEXTFLOW\_PATH: python string representation of the executable `nextflow`command. Ideally, the nextflow installation directory is in the $PATH environment variable; if it is, set this parameter to "nextflow". 

	* HPC\_HOSTNAME: python string representation of the hostname to be used to ssh/scp to access a remote compute resource. OPTIONAL. 
	* HPC\_USERNAME: python string representation of the username to be used to ssh/scp to access a remote compute resource. OPTIONAL. 
	* HPC\_SSH\_KEY\_PATH: python string representation of a path to the ssh identity file (if one is needed). OPTIONAL. KEEP THIS SECRET. 
	* PARTITION: python string representation used to specify which compute partition a EFI-related job will be submitted to. OPTIONAL.
	* SOURCE\_ENV\_CMD: python string representation of the command to be run to source a shell environment script. OPTIONAL. 

	* NEXTFLOW\_PARAMS: python dictionary that contains hard-coded parameters that are shared across all EFI jobs. 

	* EMAIL\_HOST (UNUSED)
	* EMAIL\_HOST\_USER (UNUSED)
	* EMAIL\_HOST\_PASSWORD (UNUSED)
	* EMAIL\_PORT (UNUSED)
	* EMAIL\_SENDER (UNUSED)
	* EMAIL\_USE\_TLS (UNUSED)

