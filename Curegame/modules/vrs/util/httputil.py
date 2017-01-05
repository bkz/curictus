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
import logging
import hashlib
import httplib
import mimetypes
import socket
import urllib
import urllib2
import uuid

_log = logging.getLogger('upload')

###########################################################################
# Utilities.
###########################################################################

def calc_sha256(filepath):
    """
    Get SHA1 hash for ``filepath``, returns digest as string in hex format.
    """
    sha256 = hashlib.sha256()
    sha256.update(open(filepath).read())
    return sha256.hexdigest()


def encode_multipart_formdata(args, files):
    """
    Generate multipart/form-data encoded HTTP request body for form with fields
    ``args`` (dict which maps names -> values) and ``files`` which is a list of
    filenames to be uploaded. Returns the request tuple (content type, body).
    """
    BOUNDARY = uuid.uuid4().hex
    CRLF = '\r\n'
    L = []
    for (key, value) in args.iteritems():
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % str(key))
        L.append('')
        L.append(str(value))
    for (n, filename) in enumerate(files):
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % ("file_%d" % n, str(filename)))
        L.append('Content-Type: %s' % (mimetypes.guess_type(filename)[0] or 'application/octet-stream'))
        L.append('')
        L.append(open(filename, "rb").read())
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


###########################################################################
# Upload public interface.
###########################################################################

def get(hostname, path='', args={}, port=80, auth=(None,None)):
    """
    GET a HTTP request to service ``path`` running on ``port`` at server
    ``hostname``. Basic HTTP authentication is supported via ``auth`` which
    should be set to the tuple (user,passwd) if needed. Arguments and request
    data is passed via the ``args`` dict as key:value pairs. Return server
    response on success (200) or None if request failed.

    Example:
      args = { 'foo1':'bar1', 'foo2':'bar2' }
      http_request('sub.domain.com', '/service',
        port=8000, auth=['default','1234'], args=args)

    """
    h = httplib.HTTPConnection("%s:%d" % (hostname, port))
    headers = {
        'User-Agent' : 'Python HTTP Client',
    }
    username, password = auth
    if username and password:
        fragment = base64.b64encode("%s:%s" % (username, password))
        headers["Authorization"] = "Basic %s" % fragment
    try:
        h.request('GET', path + "?" + urllib.urlencode(args), "", headers)
        res = h.getresponse()
    except socket.error, e:
        _log.error("HTTP Error (%s)" % e)
        return None
    if res.status == 200:
        return res.read()
    else:
        _log.warning("HTTP Error (%s) => %s" % (res.status, res.read()))
        return None


def post(hostname, path='', args={}, port=80, auth=(None,None)):
    """
    POST a HTTP request to service ``path`` running on ``port`` at server
    ``hostname``. Basic HTTP authentication is supported via ``auth`` which
    should be set to the tuple (user,passwd) if needed. Arguments and request
    data is passed via the ``args`` dict as key:value pairs. Return server
    response on success (200) or None if request failed.

    Example:
      args = { 'foo1':'bar1', 'foo2':'bar2' }
      http_request('sub.domain.com', '/service',
        port=8000, auth=['default','1234'], args=args)

    """
    h = httplib.HTTPConnection("%s:%d" % (hostname, port))
    headers = {
        'User-Agent'   : 'Python HTTP Client',
        "Content-type" : "application/x-www-form-urlencoded",
    }
    username, password = auth
    if username and password:
        fragment = base64.b64encode("%s:%s" % (username, password))
        headers["Authorization"] = "Basic %s" % fragment
    try:
        body = urllib.urlencode(args)
        h.request('POST', path, body, headers)
        res = h.getresponse()
    except socket.error, e:
        _log.error("HTTP Error (%s)" % e)
        return None
    if res.status == 200:
        return res.read()
    else:
        _log.warning("HTTP Error (%s) => %s" % (res.status, res.read()))
        return None


def postform(hostname, path='', args={}, files=[], port=80, auth=(None,None)):
    """
    POST a HTTP multipart/form-data request to service ``path`` running on
    ``port`` at server ``hostname``. Form fields are passed as ``args`` which
    maps field names -> values, ``files`` is a list of filenames to be uploaded
    to the server as part of the request. Basic HTTP authentication is
    supported via ``auth`` which should be set to the tuple (user,passwd) if
    needed. Returns server response on success (200) or None on failure.

    Example:
      args = { 'foo1':'bar1', 'foo2':'bar2' }
      http_post_multipart('sub.domain.com.', '/service',
        port=8000, args=args, files=['test.jpg'])

    """
    content_type, body = encode_multipart_formdata(args, files)
    h = httplib.HTTPConnection("%s:%d" % (hostname, port))
    headers = {
        'User-Agent'      : 'Python HTTP Client',
        'Content-Type'    : content_type,
        'Content-Length"' : str(len(body)),
    }
    username, password = auth
    if username and password:
        fragment = base64.b64encode("%s:%s" % (username, password))
        headers["Authorization"] = "Basic %s" % fragment
    try:
        h.request('POST', path, body, headers)
        res = h.getresponse()
    except socket.error, e:
        _log.error("HTTP Error (%s)" % e)
        return None
    if res.status == 200:
        return res.read()
    else:
        _log.warning("HTTP Error (%s) => %s" % (res.status, res.read()))
        return None


###########################################################################
# The End.
###########################################################################
