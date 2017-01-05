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

from hgt.event import Event
from hgt.locale import translate as _
from hgt.nodes import hgn

import hgt.game
import math
import random
import space

from H3DUtils import *

DEG2RAD = math.pi / 180.0

###########################################################################
# Math2
###########################################################################

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        # Setup hgt world
        hgt.world.stereoInfo.focalDistance = 0.5
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        self.build_world()

    def start(self):
        self.start_time = hgt.time.now
        self.updated = False

    def update(self):

        t = space.nodes["Transform_Target"]

        tx = 0
        cx = 0.17
        tfx = 1
        x = tx + cx * math.sin(hgt.time.now * tfx)

        ty = 0.05
        cy = 0.05
        tfy = 2
        y = ty + cy * math.sin(hgt.time.now * tfy)

        tz = 0.06
        cz = 0.05
        tfz = 3
        z = tz + cz * math.sin(hgt.time.now * tfz)

        t.translation = Vec3f(x, y, z)

        if not self.updated:
            self.updated = True
            space.nodes["Text_xEquation"].string = ["x = %.02f + %.02f sin (%.01ft)" % (tx, cx, tfx)]
            space.nodes["Text_yEquation"].string = ["y = %.02f + %.02f sin( %.01ft )" % (ty, cy, tfy)]
            space.nodes["Text_zEquation"].string = ["z = %.02f + %.02f sin( %.01ft )" % (tz, cz, tfz)]

    def cleanup(self):
        pass

    def build_world(self):
        space.nodes["Transform_Target"]
        s = hgn.SpringEffect(
            startDistance=0.1,
            escapeDistance=1.0,
            springConstant=100,
        )
        space.nodes["Transform_Target"].add_child(s)

