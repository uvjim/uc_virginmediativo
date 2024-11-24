"""Logging."""

import datetime
import inspect
from functools import wraps
from logging import Logger
from typing import Any, Callable


def log_formatter(
    msg, include_datetime: bool = True, func: Callable | None = None
) -> str:
    """Format the logs for display."""
    ret: str = ""
    if include_datetime:
        ret += f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "

    ret += (
        f"{func.__module__}.{func.__qualname__}"
        if func is not None
        else f"{inspect.getmodule(inspect.currentframe().f_back).__name__}.{inspect.currentframe().f_back.f_code.co_qualname}"
    )
    ret += f" {msg}"

    return ret


def log(logger: Logger, include_datetime: bool = True, include_func_name: bool = True):
    """Wrap function for logging."""

    def decorator(func):
        def start_log(*args, **kwargs):
            repr_args: list[Any] = [repr(a) for a in args]
            repr_kwargs = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature: str = ", ".join(repr_args + repr_kwargs)
            logger.debug(
                log_formatter(
                    f"called with args {signature}", include_datetime, func=func
                )
            )

        def end_log(ret: Any):
            logger.debug(
                log_formatter(f"exited {repr(ret)}", include_datetime, func=func)
            )

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_log(*args, **kwargs)
            ret = await func(*args, **kwargs)
            end_log(ret)
            return ret

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_log(*args, **kwargs)
            ret = func(*args, **kwargs)
            end_log(ret)
            return ret

        return async_wrapper if inspect.iscoroutinefunction(func) else wrapper

    return decorator
