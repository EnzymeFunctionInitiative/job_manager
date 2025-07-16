
import sys
from datetime import datetime, timedelta

import app.job_enums
from config import settings
import app.database
import app.models

app.database.init_db() # Ensure database is initialized
db_session_generator = app.database.get_db_session()
db = next(db_session_generator)

row0 = app.models.ESTGenerateFamiliesJob(
    id = 1,
    uuid = "aaa",
    status = app.job_enums.Status.RUNNING,
    isPublic = False,
    efi_db_version = "105",
    job_type = "est_generate_families",
    timeCreated = datetime.now(),
    allByAllBlastEValue = 5,
    families = "pf05544",
    fraction = 1,
    schedulerJobId = 19235978,
)

row1 = app.models.ESTGenerateFamiliesJob(
    id = 2,
    uuid = "bbb",
    status = app.job_enums.Status.NEW,
    isPublic = False,
    efi_db_version = "105",
    job_type = "est_generate_families",
    timeCreated = datetime.now(),
    allByAllBlastEValue = 5,
    families = "pf05544",
    fraction = 1,
)

db.add_all([row0, row1])
db.commit()
db.close()

