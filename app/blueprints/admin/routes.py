from . import bp


@bp.route("/")
def dashboard():
    return "Admin: company approval, platform stats"
