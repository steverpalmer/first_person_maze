#!/usr/bin/env python3
"""
utils.py
Copyright 2023 Steve Palmer
"""

from functools import wraps, partial
import logging


# ======================================================================================================================
# Instruments the code with logging functionality to trace execution
# ======================================================================================================================


def modlog(log: str):
    if log == "__main__":
        log = ""
    result = logging.getLogger(log)
    return result


def traced(
    func=None,
    *,
    level=None,
    log=None,
    with_params=None,
    on_entry=None,
    on_exit=None,
    with_result=None
):
    if func is None:
        return partial(
            traced,
            level=level,
            log=log,
            with_params=with_params,
            on_entry=on_entry,
            on_exit=on_exit,
        )
    # return func
    try:
        already_traced = func._traced
    except AttributeError:
        already_traced = False
    if not __debug__ or already_traced:
        return func
    if level is None:
        level = logging.DEBUG
    if log is None:
        log = func.__module__
    if isinstance(log, str):
        log = modlog(log)
    if with_params is None:
        with_params = False
    if on_entry is None:
        on_entry = True
    if on_exit is None:
        on_exit = False
    if with_result is None:
        with_result = False
    elif with_result:
        on_exit = True

    @wraps(func)
    def wrapper(*args, **kwargs):
        logmsg = func.__qualname__
        if with_params:
            fields = [repr(arg) for arg in args] + [
                "{}={}".format(key, repr(val)) for key, val in kwargs.items()
            ]
            logmsg += "({})".format(", ".join(fields))
        if on_entry:
            log.log(level, logmsg)
        result = func(*args, **kwargs)
        if on_exit:
            logmsg += " => "
            if with_result:
                logmsg += repr(result)
            log.log(level, logmsg)
        return result

    wrapper._traced = True
    return wrapper


def do_not_trace(func):
    if __debug__:
        setattr(func, "_traced", True)
    return func


def traced_methods(cls=None, **kwargs):
    if cls is None:
        return partial(traced_methods, **kwargs)
    # return cls
    for name, method in vars(cls).items():
        if callable(method):
            setattr(cls, name, traced(method, **kwargs))
    return cls


# ======================================================================================================================
# Defensive coding by checking a state invariant
# ======================================================================================================================


def _set_check_type(method, type_):
    if __debug__:
        setattr(method, "_check_type", type_)
    return method


def invariant_checker(method):
    return _set_check_type(method, "invariant_checker")


def query(method):
    return _set_check_type(method, "query")


def procedure(method):
    return _set_check_type(method, "procedure")


def constructor(method):
    return _set_check_type(method, "constructor")


def destructor(method):
    return _set_check_type(method, "destructor")


def do_not_check(method):
    return _set_check_type(method, "do_not_check")


def method_checked(method=None, *, checker):
    if method is None:
        return partial(method_checked, checker=checker)
    # return method
    if not __debug__:
        return method

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            check_type = method._check_type
        except AttributeError:
            check_type = ""
        if check_type == "":
            # determine check_type by name
            if method.__name__ in ("__init__", "__new__"):
                check_type = "constructor"
            elif method.__name__ == "__del__":
                check_type = "destructor"
        if check_type in ("query", "procedure", "destructor"):
            checker(self)
        result = method(self, *args, **kwargs)
        if check_type in ("constructor, procedure"):
            checker(self)
        return result

    return wrapper


def checked_methods(cls=None, *, checker=None):
    if cls is None:
        return partial(checked_methods, checker=checker)
    # return cls
    if __debug__:
        if isinstance(checker, str):
            checker = getattr(cls, checker)
        else:
            checker = None
            for method in vars(cls).values():
                try:
                    if method._check_type == "invariant_checker":
                        assert checker is None
                        checker = method
                except Exception:
                    pass
        assert callable(checker)
        for name, val in vars(cls).items():
            if callable(val):
                setattr(cls, name, method_checked(val, checker=checker))
    return cls


# ======================================================================================================================
# Singleton Metaclass
# ======================================================================================================================


class Singleton(type):
    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)
        return self.__instance


__all__ = (
    "modlog",
    "traced",
    "do_not_trace",
    "traced_methods",
    "invariant_checker",
    "query",
    "procedure",
    "constructor",
    "destructor",
    "checked_methods",
    "Singleton",
)
