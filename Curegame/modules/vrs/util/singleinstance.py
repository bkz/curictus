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
import errno
import logging
import tempfile

_log = logging.getLogger('singleinstance')

##############################################################################
# SingleInstance (file based locking).
##############################################################################

def lock(appid):
    """
    Check if there is an application instance already running which has created
    a file based mutex named ``appid``. If not, this call will create such a
    global identifier for this instance. Returns False if an instance is
    already running or True if we are the first instance. Note: you should call
    this as soon as possible, preferably as the first action in your main().
    """
    lockfile = os.path.normpath(tempfile.gettempdir() + '/' + appid  + '.lock')
    if sys.platform == 'win32':
        try:
            # Lock file already exists (cleanup after previous execution).
            if os.path.exists(lockfile):
                os.unlink(lockfile)
            fd =  os.open(lockfile, os.O_CREAT|os.O_EXCL|os.O_RDWR)
        except OSError, e:
            if e.errno == errno.EACCES:
                return False
            raise
    else:
        import fcntl
        fp = open(lockfile, 'w')
        try:
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            return False
    return True


##############################################################################
# The End.
##############################################################################
