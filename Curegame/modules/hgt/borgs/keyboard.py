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
Keyboard input.
"""

import hgt
from hgt.utils import *
from hgt.nodes import hgn, X3DNode
from H3DUtils import *
from H3DInterface import *

import hgt.event

class KeyListener(AutoUpdate(SFString)):
    def __init__(self, bindings, release = False):
        AutoUpdate(SFString).__init__(self)
        self.bindings = bindings
        self.release = release

    def update(self, event):
        key = event.getValue()
        #tp = hgt.haptics.trackerPosition
        #print hgt.world.node.h3dNode.closestPoint(tp)
        #t = hgt.world.node.accumulatedInverse
        #p = t * tp
        #print "Vec3f(%f, %f, %f)," % (p.x, p.y, p.z)
        
        #print "pressed key ", key, " ", ord(key)

        if key in self.bindings:
            f = self.bindings[key]
            evt = hgt.event.Event()
            evt.key = key
            # Don't send event
            if f[2]:
                if self.release:
                    f[1]()
                else:
                    f[0]()
            # Send event
            else:
                if self.release:
                    f[1](evt)
                else:
                    f[0](evt)

        return key


class Keyboard(Borg):
    def __init__(self):
        self.keySensor = hgn.KeySensor()
        self.bindings = {}
        self.km = KeyListener(self.bindings)
        self.krm = KeyListener(self.bindings, release = True)
        self.keySensor.h3dNode.keyPress.routeNoEvent(self.km)
        self.keySensor.h3dNode.keyRelease.routeNoEvent(self.krm)

    def bind_key(self, key, onPress = Null(), onRelease = Null(), noEvent = False):
        #print "Binding key '%s' to %s %s" % (key, onPress, onRelease)
        self.bindings[key] = (onPress, onRelease, noEvent)
