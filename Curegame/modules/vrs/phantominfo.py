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

import ctypes
import metrics

###########################################################################
# Raw imports from DLL
###########################################################################

_getInkwellState = ctypes.CDLL("phantominfo.dll").getInkwellState
_getInkwellState.restype = ctypes.c_int
_getInkwellState.argtypes = []

_getVersionInfo = ctypes.CDLL("phantominfo.dll").getVersionInfo
_getVersionInfo.restype = ctypes.c_char_p
_getVersionInfo.argtypes = []

###########################################################################
# Public interface.
###########################################################################

def isConnected():
    """
    Return 1 if a Phantom Omni connected to the system.
    """
    try:
        return _getInkwellState() != -1
    except Exception as e:
        metrics.track_error("phantominfo", e)
        raise e
        return 1 # Assume device is connected.


def getInkwellState():
    """
    Returns 1 if the haptic pen is inserted into into the inkwell on Phantom
    Omni. This is mainly used to make sure that Phantom Omni has been properly
    intialized and calibrated before launching an application. Note: we return
    0 if no Phantom Omni is connected, if you want to handle this case
    separately use the isConnected() function.
    """
    try:
        ret = _getInkwellState()
        if ret == -1:
            return 0
        else:
            return ret
    except Exception as e:
        metrics.track_error("phantominfo", e)
        raise e
        return 0 # See docstring for details!


def getVersionInfo():
    """
    Retrieve detailed information about the Phantom Omni attached to the
    system. Returns an XML string in the following format:

      <phantom>
        <hdapi>3.00.66</hdapi>
        <vendor>SensAble Technologies, Inc.</vendor>
        <model>PHANTOM Omni</model>
        <driver>4.2.122</driver>
        <firmware>192</firmware>
        <serial>51201300002</serial>
      </phantom>

    """
    try:
        return _getVersionInfo()
    except Exception as e:
        metrics.track_error("phantominfo", e)
        raise e
        return "<phantom></phantom>"


###########################################################################
# The End.
###########################################################################
