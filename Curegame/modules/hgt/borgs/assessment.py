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
Real-time kinematic assessment.
"""

from H3DInterface import *
import H3DUtils
from hgt.utils import *

from haptics import haptics
from time import time

OSC_ENABLED = False 
OSC_IP = "127.0.0.1"
OSC_PORT = 12346
OSC_TIME_DELTA = 1 / 24.0

class Assessment(Borg):
    def __init__(self):
        self.oscEnabled = OSC_ENABLED
        if self.oscEnabled:
            self.lastOscSendTime = time.now
            curelabs.osc.init()

        self.distance = 0.0
        self.previousPosition = haptics.trackerPosition

    def update(self):
        p = haptics.devicePosition
        o = haptics.deviceOrientation
        f = haptics.deviceForce
        v = haptics.deviceVelocity
       
        tp = haptics.trackerPosition
        d = (tp - self.previousPosition).length()
        self.distance += d
        self.previousPosition = tp 

        if self.oscEnabled and ((time.now - self.lastOscSendTime) > OSC_TIME_DELTA):
            self.lastOscSendTime = time.now
            bundle = curelabs.osc.createBundle()
            curelabs.osc.appendToBundle(bundle, "/devicePosition", [p.x, p.y, p.z])
            curelabs.osc.appendToBundle(bundle, "/deviceOrientation", [o.x, o.y, o.z, o.a])
            curelabs.osc.appendToBundle(bundle, "/deviceForce", [f.x, f.y, f.z])
            curelabs.osc.appendToBundle(bundle, "/deviceVelocity", [v.x, v.y, v.z])
            
            curelabs.osc.sendBundle(bundle, OSC_IP, OSC_PORT)

            curelabs.osc.sendMsg("/inttime", [int(time.now)], OSC_IP, OSC_PORT)
    
    def store(self):
        log_info("Assessment: dummy storing data.")
        
        # Deinitialize osc here
        if self.oscEnabled:
            curelabs.osc.dontListen()
