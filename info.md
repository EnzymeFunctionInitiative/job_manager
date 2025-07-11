# Project Structure

To keep the application organized and secure, the following directory structure is used. The core logic will
be version-controlled, while the plugins and config will be specific to your environment and should not be
checked into version control.

    hpc_job_manager/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── database.py
    │   ├── job_handler.py
    │   ├── models.py
    │   └── plugin_loader.py
    ├── plugins/
    │   ├── __init__.py
    │   └── connectors/
    │       ├── hpc_connector.py
    │       ├── local_connector.py
    │       └── notification.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    ├── requirements.txt
    └── README.md


* app/: Contains the core application logic.
** main.py: The entry point of the application.
** database.py: Handles database connections and sessions.
** job_handler.py: Contains the logic for processing individual jobs.
** models.py: Will contain the SQLAlchemy models from job_efi_web_orm.py.txt file.
** plugin_loader.py: Helper function for loading plugin connectors.
* plugins/: Contains modules and API for interacting with external systems.
** connectors/: Contains modules for interacting with external systems. This directory should be in .gitignore.
*** hpc_connector.py:  Will contain the logic for SSH/SCP connections and HPC command execution (e.g., sbatch, sacct).
*** local_connector.py: Allows the application to execute commands like sbatch directly and work with a shared file system, removing the need for SSH and SCP.
** notification.py: Will handle sending email notifications.
* config/: For application configuration. This should also be in .gitignore.
** settings.py: Defines configuration variables like database connection strings, file paths, and HPC details.
* requirements.txt: Lists the Python dependencies for this project.
* README.md: Provides instructions on how to set up and run the application.

