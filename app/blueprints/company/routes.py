from . import bp


@bp.route("/dashboard")
def dashboard():
    return "Company dashboard"  # post job, applicants, shortlist, reports
