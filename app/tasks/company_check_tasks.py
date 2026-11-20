from app.extensions import celery
from app.agents.fake_company_detector.run import run


@celery.task
def check_company(company):
    return run(company)
