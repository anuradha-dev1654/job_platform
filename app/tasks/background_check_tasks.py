from app.extensions import celery
from app.agents.background_checker.run import run


@celery.task
def background_check(state):
    return run(state)
