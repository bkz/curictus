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

"""
Listeners for H3D routing. See widgets.
"""

from H3DInterface import *
from hgt.utils import *

# NOTE: Manully reference routed fields since H3D 2.1.1+ will not keep references to
# them. You must add all instances of listeners to this global variable!
g_nodeRefs = []
        
class BoolListener(AutoUpdate(SFBool)):
    def __init__(self, 
        callbackObject = None, 
        onTrue = None, 
        onFalse = None
    ):
        self._onTrue = onTrue
        self._callbackObject = callbackObject
        self._onFalse = onFalse
        AutoUpdate(SFBool).__init__(self)
        g_nodeRefs.append(self)

    def update(self, event):
        ts = event.getValue()
        if ts:
            if self._onTrue is not None:
                if self._callbackObject is not None:
                    self._onTrue(self._callbackObject)
                else:
                    self._onTrue()
        else:
            if self._onFalse is not None:
                if self._callbackObject is not None:
                    self._onFalse(self._callbackObject)
                else:
                    self._onFalse()
        return ts

class MFBoolListener(AutoUpdate(MFBool)):
    def __init__(self, 
        callbackObject = None, 
        onTrue = None, 
        onFalse = None
    ):
        self._onTrue = onTrue
        self._callbackObject = callbackObject
        self._onFalse = onFalse
        AutoUpdate(MFBool).__init__(self)
        g_nodeRefs.append(self)

    def update(self, event):
        ts = event.getValue()
        if any(ts):
            if self._onTrue is not None:
                if self._callbackObject is not None:
                    self._onTrue(self._callbackObject)
                else:
                    self._onTrue()
        else:
            if self._onFalse is not None:
                if self._callbackObject is not None:
                    self._onFalse(self._callbackObject)
                else:
                    self._onFalse()
        return ts

HIT_FORCE = 3.5
class ForceListener(AutoUpdate(MFVec3f)):
    def __init__(self, callbackObject, callback, hitForce = HIT_FORCE):
        self._callback = callback
        self._callbackObject = callbackObject
        self.hitForce = hitForce
        AutoUpdate(MFVec3f).__init__(self)
        g_nodeRefs.append(self)

    def update(self, event):
        ts = event.getValue()
        for t in ts:
            #print dir(t)
            #print t.length()
            #print t.lengthSqr()
            if t.length() > self.hitForce:
                if self._callbackObject is not None:
                    self._callback(self._callbackObject)
                else:    
                    self._callback()
                break
        return ts


class TouchListener(AutoUpdate(MFBool)):
    def __init__(self, callbackObject, onTouch = None, onRelease = None):
        self._onTouch = onTouch
        self._callbackObject = callbackObject
        self._onRelease = onRelease
        AutoUpdate(MFBool).__init__(self)
        g_nodeRefs.append(self)

    def update(self, event):
        ts = event.getValue()
        if any(ts):
            if self._onTouch is not None:
                self._onTouch(self._callbackObject)
        else:
            if self._onRelease is not None:
                self._onRelease(self._callbackObject)
        return ts


class ContactListener(AutoUpdate(MFVec3f)):
    def __init__(self, callbackObject, onTouch = None, onRelease = None):
        self._onTouch = onTouch
        self._callbackObject = callbackObject
        self._onRelease = onRelease
        AutoUpdate(MFVec3f).__init__(self)
        g_nodeRefs.append(self)

    def update(self, event):
        ts = event.getValue()
        if any(ts):
            if self._onTouch is not None:
                self._onTouch(self._callbackObject)
        else:
            if self._onRelease is not None:
                self._onRelease(self._callbackObject)
        return ts
