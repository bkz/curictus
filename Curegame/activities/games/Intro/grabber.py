##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
#
# This file part of Curictus VRS.
#
# Curictus VRS is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Curictus VRS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Curictus VRS; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
##############################################################################

import hgt
from hgt.nodes import *
from hgt.listeners import ForceListener

class GrabObject:
    def __init__(self, manager, nodes, name, mass):
        self.manager = manager
        self.transform = nodes["Transform_%s" % name]
        self.toggle = hgn.ToggleGroup()
        self.dt = hgn.DynamicTransform()
        self.mass = mass

        self.forceListener = ForceListener(
            callbackObject = None,
            callback = self.press,
            hitForce = 0.2,
        )

        mesh = nodes["Mesh_%s" % name]
        mesh.h3dNode.force.routeNoEvent(self.forceListener)

        self.material = nodes["Material_%s" % name]

        self.transform.reparent_children_to(self.dt)
        self.dt.reparent_children_to(self.toggle)

        self.touchable = True
        self.released = False

        self.manager.register(self)

    def press(self):
        if self.touchable and not self.manager.grabbing:
            # TODO: don't reference your grandparents directly.
            self.manager.ctrl.clear_user_message()

            z = (self.manager.ctrl.tiltMatrix * hgt.haptics.trackerPosition).z
            #print z
            if z < -0.12:
                self.touchable = False
                self.toggle.hapticsOn = False
                #self.material.transparency = 0.3
                self.manager.grab(self)

    def update(self):
        if self.released:
            z = 0.005
            if self.dt.position.z < z:
                self.dt.force = Vec3f(0, 0, 0)
                self.dt.momentum = Vec3f(0, 0, 0)
                self.dt.position.z = z
                self.toggle.hapticsOn = True

class GrabManager:
    def __init__(self, ctrl, matrix):
        self.ctrl = ctrl
        self.matrix = matrix

        self.grabObjects = []
        self.grabbing = False
        self.grabObject = None

        self.grabCount = 0

    def update(self):
        if self.grabbing:
            r = self.matrix
            tp = r * hgt.haptics.proxyPosition
            f = r * (hgt.haptics.deviceVelocity)
            #self.ctrl.forceField.force = 3 * -f + Vec3f(0, 0, -self.grabObject.mass * 2)
            self.ctrl.forceField.force = Vec3f(0, 0, -self.grabObject.mass * 2)
            pos = tp - self.grabObject.transform.translation
            self.grabObject.dt.position = pos

        for o in self.grabObjects:
            o.update()

    def register(self, grabObject):
        self.grabObjects.append(grabObject)

    def grab(self, grabObject):
        self.grabbing = True
        self.grabObject = grabObject

        t = self.ctrl.guideArrowPos.translation
        self.ctrl.guideToggle.graphicsOn = True
        self.ctrl.guideArrowPos.translation = Vec3f(-0.123, -0.0316, t.z)

    def release(self):
        if self.grabbing:
            fx = hgt.haptics.deviceVelocity.x * 3
            self.ctrl.melonDropSound.play(
                location = self.grabObject.dt.position,
                intensity = self.grabObject.mass,
            )
            self.grabObject.released = True
            #self.grabObject.material.transparency = 0.0
            #self.grabObject.dt.momentum = Vec3f(fx, 0, 0)
            self.grabObject.dt.force = Vec3f(0, 0, -1)
            self.grabbing = False
            self.grabObject = None
            self.ctrl.forceField.force = Vec3f(0, 0, 0)
            self.ctrl.guideToggle.graphicsOn = False

            self.grabCount += 1
            #if self.grabCount == 4:
            #    hgt.time.add_timeout(2.0, self.ctrl.quit)
