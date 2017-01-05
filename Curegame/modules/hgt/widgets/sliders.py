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
Linear slider.
"""

import hgt
from hgt.utils import *
from hgt.nodes import *
from hgt.gameelements import *
from H3DInterface import *

from hgt.listeners import * 
from hgt.event import Event

import math
import random

class Slider(GameElement):
    def __init__(
        self,
        geometry = None,
        callback = None,
        releaseCallback = None,
        value = 0.5,
        valRange = (-1, 1),
        snapValue = 0.01,
        
    ):
        self.geometry = geometry
        self.callback = callback
        self.releaseCallback = releaseCallback
        self.value = value 
        self.valRange = valRange
        self.snapValue = snapValue

        self.contactPoint = Vec3f(0, 0, 0)
        
        # Setup listeners
        self.forceListener = ForceListener(
            callbackObject = None,
            callback = self.value_changed,
            hitForce = 0.1,
        )
        geometry.force.routeNoEvent(self.forceListener)

        self.touchListener = MFBoolListener(
            onTrue = None,
            onFalse = self.releaseCallback,
        )
        geometry.isTouched.routeNoEvent(self.touchListener)
        
        fixme("Slider should handle multiple devices.")
   
    def value_changed(self):
        p = self.geometry.contactPoint.getValue()
        self.contactPoint = p[0]
        x = self.contactPoint.x
        normalized = 0
        r = abs(self.valRange[1] - self.valRange[0]) / 2.0 # 0.05  
        if r != 0:
            normalized = x / r # -1 - 1
        v = clamp(normalized + 1.0, 0.0, 2.0) / 2.0 
        self.value = v
        
        if v > 1.0 - self.snapValue:
            self.value = 1.0
        elif v < self.snapValue:
            self.value = 0.0
        
        self.value_callback()

    def value_callback(self):
        if self.callback is not None:
            evt = Event(object = self)
            self.callback(evt)
    
    def debug(self):
        print "Slider: %.3f %.3f" % (self.value, self.contactPoint.x)
