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
import subprocess
import simplejson
import socket
import os

_log = logging.getLogger('metrics')

###########################################################################
# Utilities.
###########################################################################

def get_local_ip():
    """
    Return (DHCP) IP of local ehternet interface in string form (returns
    empty string if not connected).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.se', 80))
        return s.getsockname()[0]
    except:
        return ""

###########################################################################
# Module public interface.
###########################################################################

# Don't bother tracking event for developer machines.
DEBUG = (os.environ["CUREGAME_OPT_DEBUG"] == "1")

# You need to change the API token if you switch Mixpanel projects.
API_TOKEN = "a8f5ae1a169f870ae99d001ccf73c571"

# Mixpanel use an 'ip' property to uniquely identify clients.
LOCAL_IP = get_local_ip()


def track(event, properties=None):
    """
    A simple function for asynchronously logging to the mixpanel.com API. An
    ``event`` (string) is logged together with an optional set of
    ``properties`` in the form of a dict (key-value pairs).

    Example:
      metrics.track("login", {"type" : "guest"})

    See http://mixpanel.com/api/ for further detail.
    """
    if DEBUG: return None
    try:
        if properties == None:
            properties = {}
        properties["token"] = API_TOKEN
        properties["ip"] = LOCAL_IP
        params = {"event": event, "properties": properties}
        data = base64.b64encode(simplejson.dumps(params))
        request = "http://api.mixpanel.com/track/?data=" + data
        # Launch Curl by forcing the application to hide all of its window,
        # including the console which we don't to popup on the screen.
        curl_exe = os.path.join(os.environ["CUREGAME_ROOT"], "bin\\curl.exe")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen((curl_exe, request), stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, startupinfo=startupinfo)
    except:
        logging.exception("Caught unhandled exception")


def track_error(module, e=None):
    """
    Simple wrapper which tracks errors for ``module`` (string identifier) and
    optionally includes the type of the exception ``e``.

    Example:
      try:
          ...
      except (OSError, IOError) as e:
          metrics.track_error("startup", e)
    """
    if e:
        return track("error", {"module":module, "exception": type(e).__name__})
    else:
        return track("error", {"module":module})


###########################################################################
# The End.
###########################################################################
