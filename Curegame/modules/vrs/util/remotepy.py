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

import base64
import cPickle
import inspect
import logging
import traceback
import sys
import uuid
import zlib

import tornado.ioloop
import tornado.httpserver
import tornado.web

from vrs.util import httputil
from vrs.util import serializer

_log = logging.getLogger('remotepy')

###########################################################################
# Utilities.
###########################################################################

def make_signature(m):
    """
    Generate unique signature for method ``m`` by combining it's module path,
    class name and method name, ex: 'module.MyType.myFunc'.
    """
    assert inspect.ismethod(m)
    return ".".join([m.im_class.__module__, m.im_class.__name__, m.im_func.__name__])


###########################################################################
# RemotePyError.
###########################################################################

class RemotePyError(Exception):
    """
    Generic RemotePy RPC error.
    """
    def __init__(self, message, stacktrace=None):
        self.message, self.stacktrace = message, stacktrace


class RemotePyConnectError(RemotePyError):
    """
    RemotePy client failed to connecto server error.
    """
    pass


###########################################################################
# RemotePy call dispatcher.
###########################################################################

_rpc_methods = {}

def register(obj, interface=None):
    """
    Register and expose all public method of ``obj`` as RPC endpoints. An
    optional ``interface`` class be passed which will result in all public
    methods of the interface being mapped to the concrete object (i.e. when the
    client calls interface.func() over RPC the server will execute obj.func()).
    """
    if interface is None:
        members = inspect.getmembers(obj)
    else:
        members = inspect.getmembers(interface)
    for (name, value) in members:
        if inspect.ismethod(value):
            signature = make_signature(value)
            assert signature not in _rpc_methods
            _rpc_methods[signature] = getattr(obj, name)


def dispatch(args):
    """
    Dispatch a RPC request using ``args`` which is a pickled/b64 from a
    RemotePy.invoke() call transported from the client over HTTP. Returns a
    dict with detail about the result or any errors which may have occured
    during the RPC call evaluation.
    """
    try:
        args = serializer.loads(args)

        invoke_id      = args["invoke_id"]
        signature      = args["signature"]
        (args, kwargs) = args["params"]

        method = _rpc_methods[signature]
        result = method(*args, **kwargs)

        response = dict(invoke_id=invoke_id, result=result, error=None)
    except:
        _log.exception("Unhandled exception while dispatching RPC call")
        exception_type, exception_value, exception_traceback = sys.exc_info()
        error = dict(exception=exception_type.__name__,
                     message=str(exception_value),
                     stacktrace='\n'.join(traceback.format_tb(exception_traceback)))
        response = dict(invoke_id=invoke_id, result=None, error=error)

    try:
        response = serializer.dumps(response)
    except:
        _log.exception("Unhandled exception while encoding RPC call response")
        exception_type, exception_value, exception_traceback = sys.exc_info()
        error = dict(exception=exception_type.__name__,
                     message=str(exception_value),
                     stacktrace='\n'.join(traceback.format_tb(exception_traceback)))
        response = dict(invoke_id=invoke_id, result=None, error=error)
        response = serializer.dumps(response)

    return response


###########################################################################
# Tornado HTTP handler for exposing RemotePy RPC.
###########################################################################

class RemotePyHandler(tornado.web.RequestHandler):
    def post(self):
        args = self.get_argument("args")
        response = dispatch(args)
        self.write(response)

###########################################################################
# RemotePy HTTP client.
###########################################################################

class RemotePyClient(object):
    def __init__(self, hostname, url, port=80):
        """
        Initialize RPC HTTP client to dispatch calls to``hostname`` using the
        service path ``url``. Override the default HTTP ``port`` if needed.
        """
        self.hostname, self.url, self.port = hostname, url, port


    def invoke(self, method, *args, **kwargs):
        """
        Invoke a RPC call of ``method`` on the remote host using ``args`` and
        ``kwargs``. Return a de-serialized representation of the Python object
        response from the remote host or raises an RemotePyError on errors.
        """
        assert inspect.ismethod(method)

        args = {
            "invoke_id" : str(uuid.uuid4()),
            "signature" : make_signature(method),
            "params"    : (args, kwargs),
            }

        response = httputil.post(self.hostname, self.url, {"args": serializer.dumps(args)}, port=self.port)
        if not response:
            raise RemotePyConnectError("RPC call '%s' failed, server %s not responding" % (
                    method.__name__, self.hostname))

        response = serializer.loads(response)

        assert response["invoke_id"] == args["invoke_id"]

        if response["error"]:
            error = response["error"]
            _log.error("RPC call '%s' to %s:%s%s failed: %s (%s)" % (
                    method.__name__, self.hostname, self.port, self.url, error["message"], error["exception"]))
            _log.debug("RPC error stacktrace:\n%s" % error["stacktrace"])
            raise RemotePyError("RPC call '%s' failed: %s" % (method.__name__, error["message"]), error["stacktrace"])
        else:
            return response["result"]


###########################################################################
# Unit test.
###########################################################################

class TestService(object):
    def test_rpc(self, param1, param2, *args, **kwargs):
        _log.info("test_rpc: %s %s - %s - %s " % (param1, param2, args, kwargs))
        return [1, 2, {"key":"value"}]


    def test_rpc_exception(self, param):
        _log.info("test_rpc_exception: %s" % param)
        raise RuntimeError(param)


def test_rpc_client():
    rpc = RemotePyClient("127.0.0.1", "/remotepy/rpc/", port=8000)

    result = rpc.invoke(TestService.test_rpc, "foo", "bar", 1, 2, 3, a=1, b=2)
    assert type(result) is list
    assert result[0] == 1 and result[1] == 2
    assert type(result[2]) is dict
    assert result[2]["key"] == "value"

    try:
        result = rpc.invoke(TestService.test_rpc_exception, "exception info")
    except RemotePyError, e:
        assert e.message == "RPC call 'test_rpc_exception' failed: exception info"

    rpc = RemotePyClient("127.0.0.0", "/bla/bla/", port=1234)
    try:
        result = rpc.invoke(TestService.test_rpc, "foo", "bar", 1, 2, 3, a=1, b=2)
    except RemotePyError, e:
        assert e.message == "RPC call 'test_rpc' failed, server 127.0.0.0 not responding"


def test_rpc_server():
    register(TestService())
    application = tornado.web.Application([(r"/remotepy/rpc/", RemotePyHandler)])
    server = tornado.httpserver.HTTPServer(application)
    server.listen(8000)
    io_loop = tornado.ioloop.IOLoop.instance().start()

###########################################################################
# Module entry-point.
###########################################################################

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())

    if len(sys.argv) > 1:
        if sys.argv[1] == "client":
            test_rpc_client()
        if sys.argv[1] == "server":
            test_rpc_server()


###########################################################################
# The End.
###########################################################################
