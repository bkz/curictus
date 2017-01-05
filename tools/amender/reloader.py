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
import logging

###########################################################################
# Detect code modification (for automatic restarts).
###########################################################################

import __builtin__

# Save original module import function.
_import  = __builtin__.__import__

# Global list of monitored modules (filename => mtime).
_modules = {}

def _addimport(filename):
    """
    Record module import of ``filename`` excluding it if it's from
    Python standard library (including site-packages).
    """
    if filename.endswith('.pyc') or filename.endswith('.pyo'):
        filename = filename[:-1]
    try:
        is_stdpylib = filename.startswith(sys.exec_prefix)
        if not is_stdpylib and filename not in _modules:
            _modules[filename] = os.stat(filename).st_mtime
    except OSError:
        pass

def _newimport(name, globals={}, locals={}, fromlist=[], level=-1):
    """
    Replace from the builtin import statement, records (filename,
    mtime) for each loaded module so that we later on can track if the
    module has been modified on disk.
    """
    mod = _import(name, globals, locals, fromlist, level)
    if mod and '__file__' in mod.__dict__:
        try:
            _addimport(mod.__file__)
        except AttributeError:
            pass
    return mod

def code_changed():
    """
    Iterrate over the monitored modules and check for file
    modifications. To safeguard ourselves from someone else replacing
    or overriden import callback we'll monitor the system modules list
    just in case. Returns True if one of the loaded modules has
    been modified or False if the code is up to date.
    """
    if hasattr(sys, "frozen"):
        return False
    try:
        modules = _modules.copy()
    except Exception, e:
        modules = {}
    for (filename, prev_mtime) in modules.iteritems():
        try:
            curr_mtime = os.stat(filename).st_mtime
            if curr_mtime != prev_mtime:
                logging.info("Modified: %s" % filename)
                return True
        except OSError:
            continue
    for mod in sys.modules.copy().itervalues():
        try:
            _addimport(mod.__file__)
        except AttributeError:
            pass
    return False


# Overide default import function if we aren't running as frozen using py2exe.
if not hasattr(sys, "frozen"):
    __builtin__.__import__   = _newimport

    
###########################################################################
# The End.
###########################################################################
