##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

import os, sys
import inspect
import functools
import logging
import time

_log = logging.getLogger('util')

###########################################################################
# Custom dictionary type.
###########################################################################

class AttrDict(dict):
    """
    Makes a dictionary behave like an Python objects, i.e. keys are accessable
    as attributes: x['key'] -> x.key.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


###########################################################################
# Retry decorator.
###########################################################################

def retry(count, delay=1, onexception=[Exception], callback=None, exponential_backoff=False):
    """
    Wrap ``f`` to retry calls (on exceptions) for a maximum of ``count`` times
    waiting ``delay`` seconds in-between each calls. Customize ``onexception``
    to narrow down the kind of errors you want to retry on.

    Optionally pass a ``callback`` (taking no arguments) which is invoked
    before each retry attempt (any exceptions raised will be logged and
    swallowed).

    If ``exponential_backoff`` is True, delay will be multiplied by 2^n-1 after
    each failure until we reach ``count`` total failures on succeed.

    Example:
       @retry(count=10, delay=1, exception=[socket.timeout])
       def upload(...):
           ....

    """
    assert count >= 2
    assert delay >= 0
    assert (callback is None) or callable(callback)
    onexception = tuple(onexception)
    def decorator(f):
        assert inspect.isfunction(f) # Did you forgot the parens @retry()?
        def wrapper(*args, **kwargs):
            for i in range(1, count):
                try:
                    return f(*args, **kwargs)
                except onexception:
                    _log.exception("Exception while invoking '%s' (attempt %d/%d)" % (
                            f.__name__, i, count))
                    t = (delay*(2**i-1)) if exponential_backoff else delay
                    time.sleep(t)
                    try:
                        if callback: callback()
                    except Exception:
                        _log.exception("Unhandled exception in retry callback '%s'" % (
                                callback.__name__))
            else:
                return f(*args, **kwargs) # Last attempt, re-raises exception on failure.
        return functools.update_wrapper(wrapper, f)
    return decorator


###########################################################################
# The End.
###########################################################################
