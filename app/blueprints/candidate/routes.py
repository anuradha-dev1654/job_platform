from . import bp


@bp.route("/dashboard")
def dashboard():
    return "Candidate dashboard"  # profile, resume upload, job search, apply
