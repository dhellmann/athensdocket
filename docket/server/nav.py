import functools

from flask import g


def set_navbar_active(f):
    "Set the navbar active value to the name of the wrapped function."
    @functools.wraps(f)
    def set_active(*args, **kwds):
        g.navbar_active = f.__name__
        return f(*args, **kwds)
    return set_active
