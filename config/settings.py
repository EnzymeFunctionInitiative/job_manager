# config/settings.py

# --- Execution Environment ---
# Choose the connector for your environment.
# Options: 'HPC' (for remote cluster via SSH) or 'LOCAL' (for local/shared filesystem cluster)
EXECUTION_CONNECTOR = 'LOCAL'
DRY_RUN = True


# --- Logging --- 
LOG_FILE_PATH = "/path/to/a/job_manager.log"


# --- Database Configuration ---
# Example for SQLite: "sqlite:///jobs.db"
# Example for PostgreSQL: "postgresql://user:password@host:port/database"
DATABASE_URI = "sqlite:///jobs.db"


# --- File System Configuration ---
# The base directory where job files are stored.
# For 'LOCAL' connector, this is the direct path.
# For 'HPC' connector, this is the local staging path.
LOCAL_JOB_DIRECTORY = "/data/jobs"
# The directory where input files for jobs are located
LOCAL_INPUT_FILE_SOURCE_DIR = "/data/inputs"


# --- HPC Configuration (Used by 'HPC' connector) ---
HPC_HOSTNAME = "your-hpc-hostname"
HPC_USERNAME = "your-username"
# It is recommended to use SSH keys for passwordless authentication.
HPC_SSH_KEY_PATH = "/path/to/your/ssh/private/key"

# The base directory on the remote HPC where jobs will be created
REMOTE_JOB_DIRECTORY = "/data/jobs"
# The partition name jobs will be submitted to.
PARTITION = "queue_name"

# Set a maximum number of running Jobs to be submitted at any one time
MAX_NUM_RUNNING_JOB = 3

# --- Cluster Configuration (Used by both connectors) ---
# The path to the Nextflow executable on the cluster
REMOTE_NEXTFLOW_PATH = "/path/to/nextflow"
# The path to the Nextflow configuration file
REMOTE_NEXTFLOW_CONFIG_PATH = "/path/to/nextflow/config"
# The path to the directory that houses Nextflow pipeline scripts
REMOTE_NEXTFLOW_PIPELINE_DIR = "/path/to/your/EST/pipeline/dir"


# --- Email Configuration ---
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-email@example.com"
EMAIL_HOST_PASSWORD = "your-email-password"
EMAIL_SENDER = "noreply@example.com"


# --- Hard-coded Input Parameters for Nextflow Pipelines -- 
NEXTFLOW_PARAMS = {
    "efi_config": "/path/to/efi.config",   # this is the path to the config file for EFI DB access
    "efi_db": "efi_202503", # name of the database to be used in the EFI tools
    "fasta_db": "/path/to/fasta/database/combined.fasta",   # change this depending on which fasta database is to be used
    # only relevant to EST but no harm in overloading the dict
    "duckdb_memory_limit": "8GB",
    "duckdb_threads": 1,
    "num_fasta_shards": 128,
    "num_accession_shards": 16,
    "blast_num_matches": 250,   # hardcoded for now but should be made a vaue in the job table
    "multiplex": False,
    "filter": None,     # hardcode this value here but implement code that updates if any filter parameters are included in the job table
    "sequence_version": "uniprot",
}


