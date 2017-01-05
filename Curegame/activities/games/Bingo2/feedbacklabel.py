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
from hgt.nodes import hgn
from H3DUtils import Vec3f

class FeedbackLabel:
    def __init__(self, topnode, text, transform, material, toggle):
        self.topnode = topnode
        self.text_node = text
        self.transform_node = transform
        self.material_node = material
        self.toggle_node = toggle

        self.duration = 2.0

        self.build()
        self.reset()

    def reset(self):
        self.toggle_node.graphicsOn = False
        self.playing = False

    def show(self, msg, pos = None):
        if not self.playing:
            self.playing = True
            self.text_node.string = [msg]
            self.material_node.transparency = 1.0
            self.toggle_node.graphicsOn = True

            if pos is not None:
                self.transform_node.translation = pos
            self.time_sensor.startTime = hgt.time.now

            hgt.time.add_timeout(self.duration, self.reset)
        else:
            print "Already playing feedbacklabel"

    def build(self):
        self.time_sensor = hgn.TimeSensor(
            cycleInterval = self.duration,
            loop = False
        )

        si = hgn.ScalarInterpolator(
            key = [0, 0.1, 1],
            keyValue = [1, 0, 1],
        )
        self.topnode.add_child(self.time_sensor)
        self.topnode.add_child(si)

        self.time_sensor.h3dNode.fraction_changed.routeNoEvent(
            si.h3dNode.set_fraction
        )
        si.h3dNode.value_changed.routeNoEvent(
            self.material_node.h3dNode.transparency
        )

        """
        ei = hgn.EaseInEaseOut(
            key = [0, 1],
            easeInEaseOut = [0.1, 0.9, 0.5, 0.5],
        )

        pi = hgn.PositionInterpolator(
            key = [0, 1],
            keyValue = [
                Vec3f(1, 1, 1),
                Vec3f(1, 1, 1) * 1.3,
            ],
        )
        """

        """
        for n in [self.time_sensor, ei, pi, si]:
            self.topnode.add_child(n)

        self.time_sensor.h3dNode.fraction_changed.routeNoEvent(
            ei.h3dNode.set_fraction
        )
        ei.h3dNode.modifiedFraction_changed.routeNoEvent(
            pi.h3dNode.set_fraction
        )
        ei.h3dNode.modifiedFraction_changed.routeNoEvent(
            si.h3dNode.set_fraction
        )
        pi.h3dNode.value_changed.routeNoEvent(
            self.transform_node.h3dNode.scale
        )
        si.h3dNode.value_changed.routeNoEvent(
            self.material_node.h3dNode.transparency
        )
        print "yeah!"
        """
