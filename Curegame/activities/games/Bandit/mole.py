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
from hgt.utils import *
from hgt.nodes import *
from H3DInterface import *

import random
import math

MOLE_UP_POS = Vec3f(0, 0.01, 0)
MOLE_DOWN_POS = Vec3f(0, -0.05, 0)
MOLE_TIME = 0.25

class Mole(object):
    def __init__(self, pos):
        self.transform = hgn.Transform()
        #self.transform.add_node(modelGroup)
      
        referenceTarget = X3DFileNode("target.x3d")
        modelGroup = referenceTarget.dn["TARGET_GROUP"]
        self.material = referenceTarget.dn["MOLE_MAT"]
        self.decal = referenceTarget.dn["DECAL"]

        holeCyl = X3DNode("""
        <Transform translation="0 -0.018 0" rotation="0 1 0 1.570796">
            <Shape>
                <Appearance>
                    <Material diffuseColor="0 0 0" />
                </Appearance>
                <Cylinder radius="0.045" height="0.01" />
                </Shape>
        </Transform>
            """)

        self.transform.add(holeCyl)
    
        self.isUp = True

        self.pos = pos
        self.transform.translation = pos

        tr = hgn.Transform()
        tr.add_h3d_node(modelGroup)
        self.transform.add(tr)

        #self.ti = hgn.TransformInfo()
        #self.transform.add(self.ti)
       
        cyl1 = X3DNode("""
<ToggleGroup graphicsOn="false" hapticsOn="true">
    <Transform translation="0 0 0" rotation="0 1 0 1.570796">
        <Shape>
            <Appearance>
                <Material transparency="0" diffuseColor="0 1 0" />
                <FrictionalSurface stiffness="1.0" damping="1.0" />
            </Appearance>
            <Cylinder DEF="HIT_SURFACE" side="false" radius="0.070" height="0.17" />
        </Shape>
        <Shape>
            <Appearance>
                <Material transparency="0" diffuseColor="0 1 0" />
                <FrictionalSurface stiffness="1.0" damping="1.0" />
            </Appearance>
            <Cylinder DEF="HIT_SURFACE2" side="false" radius="0.070" height="0.12" />
        </Shape>
        <Shape>
            <Appearance>
                <Material transparency="0" diffuseColor="0 1 0" />
                <FrictionalSurface stiffness="1.0" damping="1.0" />
            </Appearance>
            <Cylinder DEF="HIT_SURFACE3" side="false" radius="0.070" height="0.06" />
        </Shape>
    </Transform>
</ToggleGroup>
        """)

        cylRim = X3DNode("""
<ToggleGroup graphicsOn="false" hapticsOn="true">
    <Transform translation="0 0 0" rotation="0 1 0 1.570796">
        <Shape>
            <Appearance>
                <Material transparency="0" diffuseColor="0 1 0" />
                <FrictionalSurface stiffness="1.0" damping="1.0" />
            </Appearance>
            <Cylinder top="false" radius="0.070" height="0.17" />
            </Shape>
    </Transform>
</ToggleGroup>
        """)
        
        tr.add(cyl1)
        tr.add(cylRim)
        
        self.geometries = [
            cyl1.dn["HIT_SURFACE"],
            cyl1.dn["HIT_SURFACE2"],
            cyl1.dn["HIT_SURFACE3"],
        ]

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

        self.upMotion.h3dNode.fraction_changed.route(
            upPi.h3dNode.set_fraction
        )
        
        upPi.h3dNode.value_changed.routeNoEvent(
            tr.h3dNode.translation
        )

        self.downMotion.h3dNode.fraction_changed.route(
            downPi.h3dNode.set_fraction
        )
        
        downPi.h3dNode.value_changed.routeNoEvent(
            tr.h3dNode.translation
        )
            
        self.decal.url.setValue([random.choice([
            "textures/bandit1.png",
            #"textures/bandit2.tif",
            "textures/bandit3.png",
            #"textures/bandit4.tif",
        ])])

        self.delayUpFlagTimeout = None

    def set_color(self, col):
        self.material.diffuseColor.setValue(col)

    def move_up(self):
        if not self.isUp:
            #self.isUp = True
            self.delayUpFlagTimeout = hgt.time.add_timeout(MOLE_TIME, self.delayed_up_flag) 
            self.upMotion.startTime = hgt.time.soon
            self.set_color(RGB(0, 1, 0))

    def delayed_up_flag(self):
        self.isUp = True
        self.delayUpFlagTimeout = None

    def move_down(self):
        if self.isUp:
            self.isUp = False
            if self.delayUpFlagTimeout is not None:
                hgt.time.clear_timeout(self.delayUpFlagTimeout)
            self.downMotion.startTime = hgt.time.soon
