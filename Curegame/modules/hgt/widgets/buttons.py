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
Button interactivity. Deprecate.
"""

import hgt
from hgt.utils import *
from hgt.nodes import *
from hgt.gameelements import *
from H3DInterface import *

from hgt.listeners import * 

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

        self.forceListener = ForceListener(None, self.press, hitForce = self.hitForce)
        self.touchListener = MFBoolListener(onTrue = self.touch, onFalse = self.untouch)
        geometry.force.routeNoEvent(self.forceListener)
        geometry.isTouched.routeNoEvent(self.touchListener)
   
        self.armed = False

        self.build_sensors()

    def touch(self):
        if self.enabled:
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
            self.onRelease()

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
            self.onPress() 
    
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

# Todo: Deprecate
class Button(object):
    def __init__(self, 
        onPress = Null(),
        upSound = Null(),
        downSound = Null(),
        size = Vec3f(0.02, 0.02, 0.01),
        texture = None,
        disabledTexture = None,
        textureTransform = None,
        disabledTextureTransform = None,
        text = None,
        onRelease = Null(),
        fontSize = 0.025,
        selfCallback = False,
        callbackOb = None,
        holdTime = 0.0,
    ):
        self.onPress = onPress
        self.onRelease = onRelease
        self.upSound = upSound
        self.downSound = downSound
        self.size = size
        self.texture = texture
        self.disabledTexture = disabledTexture
        self.textureTransform = textureTransform
        self.disabledTextureTransform = disabledTextureTransform
        self.text = text
        self.fontSize = fontSize
        self.selfCallback = selfCallback
        self.callbackOb = callbackOb
        self.holdTime = holdTime

        self.enabled = False
        
        self.build()
        self.build2()
        
        self.set_color(RGB(1, 1, 1))
        self.enable()
    
    def build2(self):
        
        # Black plastic enclosure
        b2 = OpenBoxShape(size = Vec3f(self.size.x * 1.00, self.size.y * 1.00, self.size.z), solid = True)
        b2.material.diffuseColor = RGB(0, 0, 0)
        b2.appearance.surface = hgn.FrictionalSurface()
        t = hgn.Transform(translation = Vec3f(0, 0, -0.005))
        t.add(b2.node)
        self.tr.add(t)
        
        # Hold Pie
        if self.holdTime > 0:
            self.build_pie()
        
        # Label
        self.labelShape = b3 = PlaneShape(w = self.size.x, h = self.size.y)
        self.tr.add(b3.node)
        if self.texture is not None:
            b3.appearance.texture = self.texture

        # Transparent plastic
        #b = Shape(geometry = hgn.Box(size = Vec3f(self.size.x, self.size.y, self.size.z / 2)))
        #b.material.transparency = 0.8
        #self.tr.add(b.node)
        
        # Text Label
        if self.text is not None:
            self.textShape = TextShape(
                string = [self.text], 
                size = self.fontSize, 
                justify = "MIDDLE", 
                family = "Delicious"
            )
            self.textShape.material.emissiveColor = RGB(1, 1, 1)
            y = self.fontSize * -0.27
            t = hgn.Transform(translation = Vec3f(0, y, 0.001))
            t.add(self.textShape.node)
            self.tr.add(t)


    def build_pie(self):
        self.arc = arc = hgn.ArcClose2D(
            radius = self.size.y / 2.5,
            startAngle = 0.0, 
            endAngle = 0.0001 
        )
        b = Shape(geometry = arc)
        b.material.transparency = 0.5
        b.material.diffuseColor = RGB(0, 0, 0)
        t = hgn.Transform(
            translation = Vec3f(0, 0, 0.00097),
            rotation = Rotation(0, 0, 1, math.pi/2)
        )
        t.add(b.node)
        self.tr.add(t)
        
        self.arcTimer = pt = hgn.TimeSensor(
            cycleInterval = self.holdTime,
            loop = False,
            enabled = True
        )
        
        pi = hgn.ScalarInterpolator(
            key = [0, 1],
            keyValue = [2 * math.pi, 0.00001]
        )

        pi2 = hgn.ScalarInterpolator(
            key = [0, 0.1, 1],
            keyValue = [1.0, 0.5, 0.5]
        )

        ci = hgn.ColorInterpolator(
            key = [0, 0.5, 1],
            keyValue = [
                RGB(1, 0, 0),
                RGB(1, 0, 0),
                RGB(1, 0, 0),
            ]
        )

        pt.h3dNode.fraction_changed.routeNoEvent(
            pi.h3dNode.set_fraction
        )

        pt.h3dNode.fraction_changed.routeNoEvent(
            pi2.h3dNode.set_fraction
        )

        pt.h3dNode.fraction_changed.routeNoEvent(
            ci.h3dNode.set_fraction
        )
        
        pi.h3dNode.value_changed.routeNoEvent(
            arc.h3dNode.endAngle
        )
        
        pi2.h3dNode.value_changed.routeNoEvent(
            b.material.h3dNode.transparency
        )
        
        ci.h3dNode.value_changed.routeNoEvent(
            b.material.h3dNode.diffuseColor
        )

        for i in [pi, pt, ci, pi2]:
            self.transform.add(i)

    def build(self):
        self.node = self.transform = hgn.Transform()
        self.isUp = True

        self.tr = hgn.Transform()
        self.transform.add(self.tr)

        self.touchNode = PlaneShape(w = self.size.x, h = self.size.y, solid = True)
        self.touchNode.appearance.surface = hgn.SmoothSurface(
            stiffness = 1.0, 
            damping = 1.0 
        )
        
        tg1 = hgn.ToggleGroup(graphicsOn = False)
        tg1.add(self.touchNode.node)
        self.tr.add(tg1)

        self.build_sensors()

        self.forceListener = ForceListener(self, self.press, hitForce = 2.5)
        self.touchListener = MFBoolListener(onTrue = self.touch, onFalse = self.release)
        self.touchNode.geometry.h3dNode.force.route(self.forceListener)
        self.touchNode.geometry.h3dNode.isTouched.route(self.touchListener)

        self.pushTime = hgt.time.now

    def press(self, pressObject):
        if self.enabled:
            if self.isUp and hgt.time.now > self.pushTime + MOLE_TIME * 2:
                self.move_down()
                self.downSound.play(location = self.transform.translation)
                self.pushTime = hgt.time.now
                hgt.time.add_timeout(MOLE_TIME * 2, self.check_release)

                if self.holdTime > 0:
                    self.arcTimer.enabled = True 
                    self.arcTimer.startTime = hgt.time.now

    def pressHandler(self):
        if self.enabled:
            if self.selfCallback:
                self.onPress(self)
            elif self.callbackOb is not None:
                self.onPress(self.callbackOb)
            else:
                self.onPress()
    
    def releaseHandler(self):
        if self.enabled and (
            self.holdTime == 0 or self.arc.endAngle < 0.0005
        ):
            if self.selfCallback:
                self.onRelease(self)
            elif self.callbackOb is not None:
                self.onRelease(self.callbackOb)
            else:
                self.onRelease()

        if self.holdTime > 0:
            self.arcTimer.enabled = False
            self.arc.endAngle = 0.0001
    
    def touch(self):
        self.upDirectly = False

    def set_color(self, c):
        self.buttonColor = c
        self.labelShape.material.diffuseColor = self.buttonColor 

    def enable(self):
        self.labelShape.material.diffuseColor = self.buttonColor
        self.enabled = True
        if self.texture is not None:
            self.labelShape.appearance.texture = self.texture
            self.labelShape.appearance.textureTransform = self.textureTransform

    def disable(self):
        self.labelShape.material.diffuseColor = RGB(0.5, 0.5, 0.5)
        self.enabled = False
        if self.disabledTexture is not None:
            self.labelShape.appearance.texture = self.disabledTexture
            self.labelShape.appearance.textureTransform = self.disabledTextureTransform

    def release(self):
        if not self.isUp and hgt.time.now > self.pushTime + MOLE_TIME * 2:
            self.release2()
        else:
            self.upDirectly = True

    def check_release(self):
        if self.upDirectly:
            self.release2()

    def release2(self):
            self.pushTime = hgt.time.now
            self.move_up()
            self.upSound.play(location = self.transform.translation)

    def move_up(self):
        if not self.isUp:
            self.isUp = True
            self.upMotion.startTime = hgt.time.soon

    def move_down(self):
        if self.isUp:
            self.isUp = False
            self.downMotion.startTime = hgt.time.soon
    
    def build_sensors(self): 
        self.upMotion = hgn.TimeSensor(
            cycleInterval = MOLE_TIME,
            loop = False,
            enabled = True
        )

        self.downMotion = hgn.TimeSensor(
            cycleInterval = MOLE_TIME / 2.0,
            loop = False,
            enabled = True
        )

        upPi = hgn.PositionInterpolator(
            key = [0, 1],
            keyValue = [
                MOLE_DOWN_POS,
                MOLE_UP_POS,
            ]
        )

        downPi = hgn.PositionInterpolator(
            key = [0, 1],
            keyValue = [
                MOLE_UP_POS,
                MOLE_DOWN_POS,
            ]
        )

        for n in [self.upMotion, self.downMotion, upPi, downPi]:
            self.transform.add(n)

        self.upMotion.h3dNode.fraction_changed.routeNoEvent(
            upPi.h3dNode.set_fraction
        )
        
        upPi.h3dNode.value_changed.routeNoEvent(
            self.tr.h3dNode.translation
        )

        self.downMotion.h3dNode.fraction_changed.routeNoEvent(
            downPi.h3dNode.set_fraction
        )
        
        downPi.h3dNode.value_changed.routeNoEvent(
            self.tr.h3dNode.translation
        )

        self.releaseListener = BoolListener(
            onFalse = self.releaseHandler,
        )
        self.upMotion.h3dNode.isActive.routeNoEvent(
            self.releaseListener
        )

        self.pressListener = BoolListener(
            onFalse = self.pressHandler,
        )
        self.downMotion.h3dNode.isActive.routeNoEvent(
            self.pressListener
        )
