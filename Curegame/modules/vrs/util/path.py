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
import stat
import time

###########################################################################
# Robust file-system utilities.
###########################################################################

def rmfile(filename, retry=10):
    """
    Delete ``filename`` handling read-only issues correctly. If errors occur
    we'll retry a maximum of ``retry`` counts.
    """
    try:
        if os.path.isfile(filename):
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        if os.path.exists(filename):
            raise IOError("Failed to delete: %s" % filename)
    except (IOError, WindowsError):
        if retry:
            time.sleep(1)
            rmfile(filename, retry-1)
        else:
            raise


def rmtree(path, retry=10):
    """
    Recursively delete ``path`` handling read-only issues correctly. If errors
    occur we'll retry a maximum of ``retry`` counts.
    """
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(path)
    except (IOError, WindowsError):
        if retry:
            time.sleep(1)
            rmtree(path, retry-1)
        else:
            raise


def mkdir(path, retry=10):
    """
    Create directory to generate ``path`` handling failures gracefully by
    retrying a maximum of ``retry`` times on errors.
    """
    try:
        os.makedirs(path)
    except (IOError, WindowsError):
        if retry:
            time.sleep(1)
            mkdir(path, retry-1)
        else:
            raise


###########################################################################
# The End.
###########################################################################
