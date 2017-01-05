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

# Copyright Curictus AB

import hgt
import hgt.game

from hgt.gameelements import *
from hgt.locale import translate as _
from hgt.nodes import *
from hgt.utils import *
from hgt.widgets.pushbutton import PushButton

import random
import math

from H3DInterface import *

import space

GRID_SIZE = 0.17
SPACE_TILT = 0.0

class ColorSquare(GameElement):
    def __init__(self, color, size, colors):
            self.colors = colors
            self.s = PlaneShape(h = size.y, w = size.x)
            t = hgn.Transform(translation = Vec3f(size.x / 2.0, -size.y / 2.0, 0))
            t.add(self.s.node)
            self.add_node(t)
            self.set_color(color)
            self.adjacents = set()
            self.pulsing = False

    def set_color(self, c):
            self.color = c
            self.s.material.emissiveColor = self.colors[c]
            self.s.material.diffuseColor = RGB(0, 0, 0)

    def set_pulser(self, ci):
        if not self.pulsing:
            self.pulsing = True
            ci.h3dNode.value_changed.routeNoEvent(
                self.s.material.h3dNode.emissiveColor
            )

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        # Setup hgt world
        hgt.world.stereoInfo.focalDistance = 0.55
        hgt.world.tilt(-SPACE_TILT)
        hgt.world.load_stylus('ball')

        cfg = self.load_config()
        self.level = cfg.settings["colors_level"]

        # Level determines number of squares in grid:
        self.gridW = [5,10,15][self.level - 1]

        self.colors = []

        # Load Blender scene
        self.add_child(space.world)

        self.build_color_pulser()

        # a growing blob of colored squares
        self.blob = set()

        self.build_sounds()
        self.build_buttons()
        self.build_grid()
        self.set_adjacents()

        # score text
        #t2 = hgn.Transform(translation = Vec3f(0, 0.05, ZFOO))
        t2 = space.nodes["Transform_LabelPosition"]

        t = hgn.Transform(translation = Vec3f(0, 0, 0))
        self.scoreText = TextShape(string = ["00"], size = 0.03, family="Droid Sans", justify = "MIDDLE")
        self.scoreText.material.emissiveColor = RGB(1, 1, 1)
        t.add(self.scoreText.node)

        t2.add(t)

        t = hgn.Transform(translation = Vec3f(0, 0.025, 0))
        st = TextShape(string = [_("Moves")], size = 0.01, family="Droid Sans", justify = "MIDDLE")
        st.material.emissiveColor = RGB(1, 1, 1)
        t.add(st.node)
        t2.add(t)

        self.update_blob()

        self.turns = 0
        self.set_text()

        self.tone_history = []

        self.game_ended = False

    def button_push(self, colorId):
        if not self.game_ended:
            # Easter egg - Japanese national anthem
            self.tone_history.append(colorId)
            anthem = [2, 1, 2, 3, 4, 3, 2, 3, 4, 5, 4, 5]
            if self.tone_history[-len(anthem):] == anthem:
                hgt.time.add_timeout(0.5, self.arigato_sound.play)

            self.buttonSounds[colorId].play()
            self.colorId = colorId
            self.change_color(colorId)
            self.update_blob()

            self.turns += 1

            self.set_text()

            if len(self.blob) >= self.gridW ** 2:

                # Prevent further button pushes
                self.game_ended = True

                hgt.time.add_timeout(2, self.end_game)

    def end_game(self):
        #self.dingSound.play()
        self.cheer_sound.play()

        self.log_score(
            level = self.level,
            moves = self.turns,
            duration = hgt.time.now - self.startTime,
        )

        hgt.time.add_timeout(5.0, self.quit)

    def set_text(self):
        self.scoreText.text.string = ["%02d" % (self.turns)]

    def change_color(self, c):
        for square in self.blob:
            square.set_color(c)

    def update_blob(self):
        for s in self.squares:
            s.visited = False
        self.update_blob2(self.squares[0])

        for b in self.blob:
            b.set_pulser(self.colorPulserInterpolator)

        dc = RGB(1, 1, 1)
        self.colorPulserInterpolator.keyValue = [
            dc,
            self.colors[self.colorId],
            self.colors[self.colorId],
            dc,
        ]

    def update_blob2(self, square):
        square.visited = True
        for s in square.adjacents:
            if not s.visited and s.color == square.color:
                self.blob.add(s)
                self.update_blob2(s)

    def set_adjacents(self):
        for (s,i) in zip(self.squares, range(len(self.squares))):
            u = i - self.gridW
            d = i + self.gridW
            l = i - 1
            r = i + 1
            if u >= 0:
                s.adjacents.add(self.squares[u])
            if d < len(self.squares):
                s.adjacents.add(self.squares[d])
            if l >= 0 and (l + 1) % self.gridW != 0:
                s.adjacents.add(self.squares[l])
            if r < len(self.squares) and r % self.gridW != 0:
                s.adjacents.add(self.squares[r])

    def disable_buttons(self):
        for b in self.buttons:
            b.disable()

    def enable_buttons(self):
        for b in self.buttons:
            b.enable()

    def build_buttons(self):
        self.buttons = []

        for i in range(6):
            d = Doer(self.button_push, i)
            b = PushButton(
                transformNode = space.nodes["Transform_button%d" % i].h3dNode,
                geometry = space.nodes["Mesh_button%d" % i].h3dNode,
                pressSound = self.downSound,
                releaseSound = self.upSound,
                onPress = d.do,
                displacement = Vec3f(0, 0, -0.005),
            )
            b.colorId = i
            self.buttons.append(b)

            material = space.nodes["Material_button%d" % i]

            # Make buttons "springier" haptically
            space.nodes["FrictionalSurface_button%d" % i].stiffness = 1.0
            space.nodes["FrictionalSurface_button%d" % i].damping = 0.1

            self.colors.append(material.diffuseColor)

    def quit_button_release(self):
        self.quit()

    def build_grid(self):

        grid = Grid2D(cols = self.gridW, rows = self.gridW, width = GRID_SIZE, height = GRID_SIZE)

        self.squares = []

        for i in range(self.gridW ** 2):
            cs = ColorSquare(
                color = random.randint(0,5),
                size = Vec2f(
                    GRID_SIZE / self.gridW,
                    GRID_SIZE / self.gridW
                ),
                colors = self.colors
            )
            grid.append(cs.node)
            self.squares.append(cs)

        self.blob.add(self.squares[0]) # first square
        self.colorId = self.squares[0].color

        #self.add_child(grid.node)
        #grid.transform.translation = Vec3f(0, GRIDY, ZFOO)

        t = space.nodes["Transform_BoardPosition"]
        t.add_child(grid.node)

    def start(self):
        self.startTime = hgt.time.now

    def update(self):
        pass

    # Setup color pulser
    def build_color_pulser(self):
        self.colorPulser = ts = hgn.TimeSensor(
            cycleInterval = 4.0,
            loop = True,
            enabled = True
        )

        self.colorPulserInterpolator = pi = hgn.ColorInterpolator(
            key = [0, 0.025, 0.975, 1.0],
            keyValue = [
                RGB(0, 0, 0),
                RGB(0, 0, 0),
                RGB(0, 0, 0),
                RGB(0, 0, 0),
            ]
        )

        hgt.world.add_nodes([ts, pi])

        ts.h3dNode.fraction_changed.route(
            self.colorPulserInterpolator.h3dNode.set_fraction
        )

    def build_sounds(self):
        self.downSound = Sound("../../../media/sounds/click.wav", copies = 3, intensity = 0.3)
        self.upSound = Sound("../../../media/sounds/click.wav", intensity = 0.1)
        self.arigato_sound = Sound("sounds/arigato.wav", intensity = 0.5)
        self.cheer_sound = Sound("sounds/cheer.wav", intensity = 0.5)
        self.buttonSounds = []
        for i in range(6):
            self.buttonSounds.append(
                Sound("sounds/%d.wav" % (i + 1), copies = 3)
            )

# FIXME
class Doer(object):
    def __init__(self, fn, args):
        self.fn = fn
        self.args = args
    def do(self, evt):
        self.fn(self.args)
