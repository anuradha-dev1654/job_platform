from flask import Blueprint

bp = Blueprint("candidate", __name__)

from . import routes  # noqa: E402,F401
