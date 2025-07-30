# EFI Job Manager

This application periodically checks a SQL database for new and running EFI-related jobs and then interacts with an HPC
cluster to run the associated EFI calculations, checks the jobs' statuses, and gathers results. Updates are continually
pushed to the SQL database and results are gathered in a centralized directory structure to enable users to access 
their results. 

# How It Works

The SQLAlchemy module is used to interface with the Job database, enabling many possible SQL engines/formats to be used
to contain the Job table. Additionally, the code uses the `plugin_loader` to dynamically import a `connector` module at
runtime. The Connector module controls all interactions with the HPC cluster. This means the core application code does
not need to be changed to add support for new cluster environments.

# Setup


```
# 1. Clone the repository:
git clone https://github.com/EnzymeFunctionInitiative/job_manager.git
cd job_manager

# 2. Install dependencies:
python3 -m venv job_manager
source job_manager/bin/activate
pip install -r requirements.txt
```

3. Configure the application:
    * Edit app/models.py (if applicable).
    * Edit config/settings.py:
        * Set `EXECUTION_CONNECTOR` to the name of your target environment (e.g., '`HPC`' or '`LOCAL`'). This name 
	  corresponds to the plugin file that will be loaded (e.g., `hpc_connector.py`).
        * Fill in your database URI, file paths, and other settings as needed.
    * Verify your plugin:
        * Ensure the plugin for your chosen connector exists in the `plugins/connectors/` directory (e.g., `plugins/connectors/local_connector.py`).
        * Customize the plugin for your specific cluster scheduler (e.g., Slurm, PBS, SGE).

## Creating a New Plugin

To add support for a new environment:

1. Create a new file in the `plugins/connectors/` directory, named after your environment (e.g., `plugins/connectors/mycloud_connector.py`).

2. In this new file, create a class named `Connector` that inherits from `plugins.base_connector.BaseConnector`.

3. Implement all the abstract methods from the `BaseConnector` interface (`prepare_job_environment`, `submit_job`, `get_job_status`, `retrieve_job_results`).

4. Update `config/settings.py` to point to your new plugin by setting `EXECUTION_CONNECTOR = 'MYCLOUD'`.

The application will now use your new plugin without any changes to the source-controlled code.

## Running the Application

To start the job manager, run:

    python -m app.main

## Security Note

The `config/` and `plugins/connectors/` directories are intended to hold sensitive information and
system-specific code. You must add them to your `.gitignore` file to prevent them from being committed
to version control.


