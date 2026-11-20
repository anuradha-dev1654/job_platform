from . import bp


@bp.route("/")
def index():
    return "Public job listing"  # search, filter, detail
