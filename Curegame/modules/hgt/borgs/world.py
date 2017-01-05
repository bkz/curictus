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
The mother of all nodes.
"""

import hgt
from hgt.utils import *
from hgt.nodes import hgn, X3DNode, HGTNode, X3DFileNode
from H3DUtils import *
from H3DInterface import *
import os
import math
# fade in/out time in seconds
FADE_TIME = 0.5

ENABLE_FOG = True
FOG_COLOR = RGB(0, 0, 0)

class World(Borg):
    def __init__(self):
        self.topNode = hgn.ToggleGroup(hapticsOn = False, graphicsOn = False)
        self.node = hgn.Transform()
        self.topNode.add(self.node)

        self.fog = None
        if ENABLE_FOG:
            fixme("Using Fog in hgt.world (may clash)")
            self.build_fog()

        # StereoInfo
        self.stereoInfo = si = hgn.StereoInfo(
                interocularDistance = 0.03,
                focalDistance = 0.3
        )
        self.add_topnode(si)

        # Save original stylus
        self._stylusModel = hgt.haptics.hdev.stylus.getValue()
        self.currentStylus = self._stylusModel

        self.add_topnode(hgt.keyboard.keySensor)

        # Global settings
        self.globalSettings = hgn.GlobalSettings()
        #self.graphicsCachingOptions = hgn.GraphicsCachingOptions(cachingDelay = 1)
        self.collisionOptions = hgn.CollisionOptions(avatarCollision = False)
        self.globalSettings.h3dNode.options.setValue([self.collisionOptions.h3dNode])
        self.add_topnode(self.globalSettings)

        self.headlight_off()

    def bind_world(self, node):
        node.children.push_back(self.topNode.h3dNode)

    def clear(self):
        #print "World clearing subnode and resetting rotation..."
        self.node.h3dNode.children.clear()
        self.node.rotation = Rotation(1, 0, 0, 0)

    def add_nodes(self, nodes):
        for n in nodes:
            self.add_node(n)

    def add_node(self, node):
        self.node.add(node)

    def add_topnode(self, node):
        self.topNode.add(node)

    def haptics_on(self):
        self.topNode.hapticsOn = True

    def graphics_on(self):
        self.topNode.graphicsOn = True

    def hide_stylus(self):
        hgt.haptics.hdev.stylus.setValue(None)

    def show_stylus(self):
        hgt.haptics.hdev.stylus.setValue(self.currentStylus)

    def set_stylus(self, h3dNode):
        hgt.haptics.hdev.stylus.setValue(h3dNode)
        self.currentStylus = h3dNode

    def load_stylus(self, stylusId):
        stylusPath = os.path.join(hgt.STYLUS_PATH, stylusId, 'stylus.hgt')
        stylus = X3DFileNode(stylusPath)
        self.set_stylus(stylus.h3dNode)

    def load_stylus_file(self, filename):
        stylus = X3DFileNode(filename)
        self.set_stylus(stylus.h3dNode)

    def reset_stylus(self):
        hgt.haptics.hdev.stylus.setValue(self._stylusModel)

    # Tilt the world n degrees (sic!) about the positive x axis.
    def tilt(self, degrees):
        rads = degrees * (math.pi / 180.0)
        self.node.rotation = Rotation(1, 0, 0, rads)

    def rotate45(self):
        self.node.rotation = Rotation(1, 0, 0, math.pi/4)

    # Introduced after removing rotation from x3d files
    def rotateMinus45(self):
        self.node.rotation = Rotation(1, 0, 0, -math.pi/4)

    def rotateMinus90(self):
        self.node.rotation = Rotation(1, 0, 0, -math.pi/2)

    def build_fog(self):
        vr = 1e-3

        self.fog = hgn.Fog(
            color = FOG_COLOR,
            visibilityRange = vr
        )
        self.add_topnode(self.fog)

        self.fogTimer = hgn.TimeSensor(
            cycleInterval = FADE_TIME,
            loop = False,
            enabled = True,
        )

        self.defogTimer = hgn.TimeSensor(
            cycleInterval = FADE_TIME,
            loop = False,
            enabled = True,
        )

        fogInterpolator = hgn.ScalarInterpolator(
            key = [0, 0.9999, 1],
            keyValue = [vr, 1, 0],
        )

        defogInterpolator = hgn.ScalarInterpolator(
            key = [0, 1],
            keyValue = [1, vr],
        )

        self.add_node(self.fogTimer)
        self.add_node(self.defogTimer)
        self.add_node(fogInterpolator)
        self.add_node(defogInterpolator)

        self.fogTimer.h3dNode.fraction_changed.routeNoEvent(
            fogInterpolator.h3dNode.set_fraction
        )
        self.defogTimer.h3dNode.fraction_changed.routeNoEvent(
            defogInterpolator.h3dNode.set_fraction
        )
        fogInterpolator.h3dNode.value_changed.routeNoEvent(
            self.fog.h3dNode.visibilityRange
        )
        defogInterpolator.h3dNode.value_changed.routeNoEvent(
            self.fog.h3dNode.visibilityRange
        )

    def show_fog(self):
        if self.fog is not None:
            self.defogTimer.startTime = hgt.time.now

    def hide_fog(self):
        if self.fog is not None:
            self.fogTimer.startTime = hgt.time.now

    def headlight_off(self):
        ni = getActiveNavigationInfo()
        if ni is None:
            ni = hgn.NavigationInfo(headlight = False)
            self.add_topnode(ni)
        else:
            ni.headlight.setValue(False)

    def headlight_on(self):
        ni = getActiveNavigationInfo()
        if ni is None:
            ni = hgn.NavigationInfo(headlight = True)
            self.add_topnode(ni)
        else:
            ni.headlight.setValue(True)

    # TODO: Remember why this was put here in the first place. Leaving
    # it for posterity.
    def stylus_to_camera(self):
        vp = getActiveViewpoint()
        print vp.fieldOfView.getValue()

        p = vp.position.getValue()
        p = p + Vec3f(0, 0, -0.45)
        pm = Matrix4f(
            1, 0, 0, p.x,
            0, 1, 0, p.y,
            0, 0, 1, p.z,
            0, 0, 0, 1
        )
        pc = hgt.haptics.positionCalibration
        hgt.haptics.positionCalibration = pc * pm

        #o = vp.orientation.getValue()
        #oc = hgt.haptics.orientationCalibration
        #hgt.haptics.orientationCalibration = -oc * o
        #print o
        #print oc

