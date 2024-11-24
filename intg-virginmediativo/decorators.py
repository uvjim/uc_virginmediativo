"""Global decorators."""

from functools import wraps

from const import POLLER_FUNCS, PollerType


def attaches_to(task_type: PollerType):
    """Wrap function."""

    def decorator(func):
        POLLER_FUNCS[task_type] = func

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return async_wrapper

    return decorator
