from app.extensions import celery
from app.agents.resume_scanner.run import run


@celery.task
def scan_resume(resume_path, job_description):
    return run(resume_path, job_description)
