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
Updated button interactivity.
"""

import hgt
from hgt.utils import *
from hgt.nodes import *
from hgt.gameelements import *
from H3DInterface import *

from hgt.listeners import * 

from hgt.event import Event

import random, math

MOLE_UP_POS = Vec3f(0, 0, 0)
MOLE_DOWN_POS = Vec3f(0, 0, -0.005)
MOLE_TIME = 0.1

class PushButton(GameElement):
    def __init__(
        self,
        transformNode = None,
        geometry = None,
        onPress = Null(),
        onRelease = Null(),
        onTouch = Null(),
        onUntouch = Null(),

        touchSound = Null(),
        untouchSound = Null(),
        pressSound = Null(),
        releaseSound = Null(),

        displacement = Vec3f(0, -0.005, 0),
        upTime = 0.1,
        downTime = 0.05,
        hitForce = 2.5,

        enabled = True,

        event = None,
        touchEvent = None,
    ):
        self.onPress = onPress
        self.onRelease = onRelease
        self.onTouch = onTouch
        self.onUntouch = onUntouch

        self.touchSound = touchSound
        self.untouchSound = untouchSound
        self.pressSound = pressSound
        self.releaseSound = releaseSound

        self.movableTransform = transformNode 
        if self.movableTransform:
            self.upPosition = transformNode.translation.getValue()
            self.downPosition = self.upPosition + displacement 

        self.upTime = upTime
        self.downTime = downTime
        self.hitForce = hitForce

        self.enabled = enabled

        # TODO: Used in Muse, rethink events!?
        if event is None:
            self.event = Event(object = self)
        else:
            self.event = event

        self.touchEvent = touchEvent

        self.forceListener = ForceListener(None, self.press, hitForce = self.hitForce)
        self.touchListener = MFBoolListener(onTrue = self.touch, onFalse = self.untouch)
        geometry.force.routeNoEvent(self.forceListener)
        geometry.isTouched.routeNoEvent(self.touchListener)
   
        self.armed = False

        self.build_sensors()

    def touch(self):
        if self.enabled:
            if self.touchEvent is not None:
                self.onTouch(self.touchEvent)
            else:
                self.onTouch()
            self.touchSound.play()

    def untouch(self):
        self.onUntouch()
        self.untouchSound.play()
        if self.armed:
            self.armed = False
            self.upMotion.startTime = hgt.time.now
            self.releaseSound.play()
    
    def moved_up(self):
            self.onRelease(self.event)

    def external_press(self):
        self.press()

    def external_release(self):
        self.untouch()

    def press(self):
        if not self.armed:
            self.armed = True
            self.downMotion.startTime = hgt.time.now
            self.pressSound.play()
    
    def moved_down(self):
            self.onPress(self.event) 
    
    def build_sensors(self): 
        self.upMotion = hgn.TimeSensor(
            cycleInterval = self.upTime,
            loop = False,
            enabled = True
        )

        self.downMotion = hgn.TimeSensor(
            cycleInterval = self.downTime,
            loop = False,
            enabled = True
        )

        for n in [self.upMotion, self.downMotion]:
            self.add_node(n)

        if self.movableTransform:
            upPi = hgn.PositionInterpolator(
                key = [0, 1],
                keyValue = [
                    self.downPosition,
                    self.upPosition,
                ]
            )

            downPi = hgn.PositionInterpolator(
                key = [0, 1],
                keyValue = [
                    self.upPosition,
                    self.downPosition,
                ]
            )

            self.upMotion.h3dNode.fraction_changed.routeNoEvent(
                upPi.h3dNode.set_fraction
            )
            
            self.downMotion.h3dNode.fraction_changed.routeNoEvent(
                downPi.h3dNode.set_fraction
            )
           
            upPi.h3dNode.value_changed.routeNoEvent(
                self.movableTransform.translation
            )

            downPi.h3dNode.value_changed.routeNoEvent(
                self.movableTransform.translation
            )

            for n in [upPi, downPi]:
                self.add_node(n)

        self.releaseListener = BoolListener(
            onFalse = self.moved_up,
        )
        self.upMotion.h3dNode.isActive.routeNoEvent(
            self.releaseListener
        )

        self.pressListener = BoolListener(
            onFalse = self.moved_down,
        )
        self.downMotion.h3dNode.isActive.routeNoEvent(
            self.pressListener
        )

