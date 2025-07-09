# config/settings.py

# --- Database Configuration ---
# Example for SQLite: "sqlite:///jobs.db"
# Example for PostgreSQL: "postgresql://user:password@host:port/database"
DATABASE_URI = "sqlite:///jobs.db"

# --- Local File System Configuration ---
# The base directory where job files are stored locally
LOCAL_JOB_DIRECTORY = "/data/jobs"
# The directory where input files for jobs are located
LOCAL_INPUT_FILE_SOURCE_DIR = "/data/inputs"

# --- HPC Configuration ---
HPC_HOSTNAME = "your-hpc-hostname"
HPC_USERNAME = "your-username"
# It is recommended to use SSH keys for passwordless authentication.
# If a password is required, you might need to adjust the hpc_connector.py
# to handle it, but key-based auth is more secure.
HPC_SSH_KEY_PATH = "/path/to/your/ssh/private/key"

# The base directory on the HPC where jobs will be created
REMOTE_JOB_DIRECTORY = "/data/jobs"
# The path to the Nextflow executable on the HPC
REMOTE_NEXTFLOW_PATH = "/path/to/nextflow"
# The Nextflow pipeline script to run
REMOTE_NEXTFLOW_PIPELINE = "/path/to/your/pipeline.nf"


# --- Email Configuration ---
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-email@example.com"
EMAIL_HOST_PASSWORD = "your-email-password"
EMAIL_SENDER = "noreply@example.com"

