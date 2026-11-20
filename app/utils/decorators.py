from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(role):
    def wrapper(fn):
        @wraps(fn)
        def inner(*a, **kw):
            if not current_user.is_authenticated or getattr(current_user, "role", None) != role:
                abort(403)
            return fn(*a, **kw)
        return inner
    return wrapper
