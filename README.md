HPC Job ManagerThis application periodically checks a database for new and running jobs, interacts with an HPC cluster to run them, and updates their status.SetupClone the repository:git clone <your-repo-url>
cd hpc_job_manager
Install dependencies:pip install -r requirements.txt
Configure the application:Copy the contents of job_efi_web_orm.py.txt into app/models.py. Make sure to include the Status enum and FlagEnumType or import them from a shared location.Edit config/settings.py with your database URI, file paths, HPC connection details, and email settings.Customize plugins/hpc_connector.py for your specific HPC scheduler (e.g., Slurm, PBS, SGE). The current version has placeholders for Slurm commands (sbatch, sacct).Customize plugins/notification.py if you need more advanced email features.Initialize the database:The application will create the database and tables on its first run, based on the models in app/models.py.Running the ApplicationTo start the job manager, run:python -m app.main
The application will then start its main loop, polling the database for jobs to process.Security NoteThe config/ and plugins/ directories are intended to hold sensitive information and system-specific code. You must add them to your .gitignore file to prevent them from being committed to version control.# .gitignore

config/
plugins/
*.pyc
__pycache__/
*.db

