# HPC Job Manager

This application periodically checks a database for new and running jobs, interacts with an HPC
cluster to run them, and updates their status.SetupClone the repository:

# How It Works

The application uses a plugin_loader to dynamically import a "connector" module at runtime based
on the `EXECUTION_CONNECTOR` setting in `config/settings.py`. This means the core application code
does not need to be changed to add support for new cluster environments.

## Setup

1. Clone the repository:

    git clone <your-repo-url>
    cd hpc_job_manager

2. Install dependencies:

    pip install -r requirements.txt

3. Configure the application:

    * Edit app/models.py (if applicable4).
    * Edit config/settings.py:
        * Set `EXECUTION_CONNECTOR` to the name of your target environment (e.g., '`HPC`' or '`LOCAL`'). This name corresponds to the plugin file that will be loaded (e.g., `hpc_connector.py`).
        * Fill in your database URI, file paths, and other settings as needed.
    * Verify your plugin:
        * Ensure the plugin for your chosen connector exists in the `plugins/connectors/` directory (e.g., `plugins/connectors/local_connector.py`).
        * Customize the plugin for your specific cluster scheduler (e.g., Slurm, PBS, SGE).

## Creating a New Plugin

To add support for a new environment (e.g., a different cloud provider or scheduler):

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

## See Also

ORM model explorer: https://g.co/gemini/share/d3655cdfdbe9

