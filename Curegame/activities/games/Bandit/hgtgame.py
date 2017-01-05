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

# Whack-A-Bandit
# Copyright Curictus AB

import hgt
from hgt.utils import *
from hgt.nodes import *
from hgt.gameelements import *
from H3DInterface import *
from hgt.locale import translate as _

import hgt.game
import random
import math

from hgt.listeners import ForceListener, TouchListener

from mole import Mole

MUSIC_VOLUME = 0.4
SFX_VOLUME = 0.5

DEG2RAD = math.pi / 180

BASE_SCORE = 50
MAX_GANGSIZE = 3

PLAY_DURATION = 55

class Game(hgt.game.Game):
    def build(self):
        random.seed(hgt.time.now)
        hgt.world.stereoInfo.focalDistance = 0.55

        cfg = self.load_config()
        self.level = cfg.settings["bandit_level"]

        self.cameraPos1 = Vec3f(0, 0.02, -0.25)
        self.cameraPos2 = Vec3f(0, 0.02, -0.13)
        #self.cameraPos1 = self.cameraPos2
        self.cameraRot = Rotation(1, 0, 0, 25 * DEG2RAD)

        # Disable normal stylus rendering
        hgt.world.hide_stylus()
        hgt.world.headlight_on()

        # Top container
        self.worldGroup = hgn.Transform()
        self.add_node(self.worldGroup)

        # Create saloon
        self.build_room()

        # Create Club
        self.clubGroup = hgn.Transform()
        self.worldGroup.add(self.clubGroup)
        self.clubGroup.add(X3DFileNode("clubhead.x3d"))
        self.clubGroup.add(X3DFileNode("clubshaft.x3d"))

        self.scoreBoardGroup = hgn.Transform()
        self.roomGroup.add(self.scoreBoardGroup)
        self.scoreBoardGroup.add(X3DFileNode("scoreboard.x3d"))

        # Create bandits
        # NB: node insertion order is important for alpha calculations!
        self.build_bandits()

        # Other setup
        self.build_camera_motion()
        self.build_audio()

        self.score = 0
        self.bonus_time = 3.0
        self.max_bonus = 50
        self.displayScore = 0
        self.gameStarted = False
        self.timeToExit = False

        # Experiments
        if False:
            self.worldGroup.add(hgn.ViscosityEffect(
                viscosity = 2.0,
                deviceIndex = 0,
                enabled = True,
                dampingFactor = 0.5,
                radius = 0.15
            ))

            """
            print "Fog!"
            self.worldGroup.add_node(hgn.Fog(
                visibilityRange = 5,
                color = RGB(0, 0, 0),
                fogType = "LINEAR"
            ))
            """

    def start(self):
        self.cameraMotion.startTime = hgt.time.now + 3
        self.upClip.startTime = hgt.time.now
        self.reset()

    def reset(self):
        self.set_score("")

        # Game variables
        self.gameStarted = False
        self.score = 0
        self.displayScore = 0
        self.hits = 0
        self.banditsShown = 0
        self.hitRoll = 0
        self.perfect = True

        """
        for (b, c) in zip(self.bandits[:3], [RGB(0, 1, 0), RGB(1, 0.5, 0), RGB(1, 0, 0)]):
            b.move_up()
            b.set_color(c)
        """

        self.gameStarted = True
        self.startTime = hgt.time.now
        self.musicClip.startTime = hgt.time.now
        hgt.time.add_timeout(3, self.begin)

    def begin(self):
        hgt.time.add_timeout(PLAY_DURATION, self.flag_exit)
        hgt.time.add_timeout(3.0, self.show_bandits)

    def flag_exit(self):
        self.timeToExit = True

    def end_game(self):
        self.log_score(
            level = self.level,
            score = self.score,
            perfect = self.perfect,
            duration = hgt.time.now - self.startTime,
        )

        hgt.time.add_timeout(0.5, self.quit)

    def set_times(self):
        if self.level == 1:
            self.gangSize = random.randint(1, MAX_GANGSIZE)
            self.downTime = 1 + random.random() * 2
            self.upTime = 3
            if self.gangSize > 1:
                self.upTime = 1 + 1.5 * self.gangSize # 1 + random.random()
        elif self.level == 2:
            self.gangSize = random.randint(1, MAX_GANGSIZE)
            self.downTime = 1 + random.random() * 2
            self.upTime = 1.5
            if self.gangSize > 1:
                self.upTime = 1 + 0.75 * self.gangSize # 1 + random.random()
        elif self.level == 3:
            self.gangSize = random.randint(1, MAX_GANGSIZE)
            self.downTime = 1 + random.random() * 2
            #self.upTime = 0.7
            self.upTime = 1.0
            if self.gangSize > 1:
                self.upTime = 1.0 + 0.3 * self.gangSize # 1 + random.random()
                #self.upTime = 0.7 + 0.3 * self.gangSize # 1 + random.random()
        else:
            pass

    def touch(self, bandit):
        self.lastBanditTouched = bandit

    def hit(self, bandit):
        if self.gameStarted:
            if bandit.isUp:
                #self.hitSound.play()
                #bonus = int(clamp(20 - (hgt.time.now - self.showTime) * 10, 0, 20))
                bonus = 0
                time_delta = hgt.time.now - self.showTime
                if time_delta < self.bonus_time:
                    bonus_factor = 1.0 - (time_delta / self.bonus_time)
                    bonus = int(bonus_factor * self.max_bonus)

                self.hitClip.startTime = hgt.time.now
                self.downClip.startTime = hgt.time.now
                bandit.move_down()
                bandit.set_color(RGB(1, 1, 0))

                self.hits += 1
                self.hitRoll += 1
                self.score += BASE_SCORE * self.hitRoll + bonus
                if self.hitRoll == 3:
                    #self.cashClip.startTime = hgt.time.now
                    yell = random.choice(self.yells)
                    yell.startTime = hgt.time.now

                self.currentBandits.remove(bandit)

            else:
                #self.missClip.startTime = hgt.time.now
                pass

        # Before game started
        else:
            """
            if bandit.isUp:
                self.hitClip.startTime = hgt.time.now
                self.downClip.startTime = hgt.time.now
                for b in self.bandits:
                    b.move_down()
                    b.set_color(RGB(0, 1, 0))
                self.gameStarted = True
                self.difficulty = bandit.difficulty
                self.musicClip.startTime = hgt.time.now
                hgt.time.add_timeout(3, self.begin)
            else:
                self.missClip.startTime = hgt.time.now
            """
            pass
            #self.missClip.startTime = hgt.time.now

    def show_bandits(self):
        self.set_times()
        self.showTime = hgt.time.now

        self.upClip.startTime = hgt.time.now
        self.hitRoll = 0

        # Select bandits to pop up, do not use last touched bandit
        bandits = self.bandits[:]
        bandits.remove(self.lastBanditTouched)
        self.currentBandits = random.sample(bandits, self.gangSize)

        for b in self.bandits:
            b.set_color(RGB(0, 1, 0))
        for b in self.currentBandits:
            b.move_up()
        hgt.time.add_timeout(self.upTime, self.hide_bandits)
        self.upClip.startTime = hgt.time.now

        self.banditsShown += self.gangSize


    def hide_bandits(self):
        if len(self.currentBandits) > 0:
            self.perfect = False
            self.downClip.startTime = hgt.time.now
            for b in self.currentBandits:
                b.set_color(RGB(1, 0, 0))
                b.move_down()

        if self.timeToExit:
            if self.perfect:
                self.cashClip.startTime = hgt.time.now
                self.gameStarted = False
                #self.set_score("Perfect!")
            hgt.time.add_timeout(4, self.end_game)
        else:
            hgt.time.add_timeout(self.downTime, self.show_bandits)

    def update(self):
        self.clubGroup.translation = hgt.haptics.trackerPosition
        self.clubGroup.rotation = hgt.haptics.trackerOrientation

        if self.gameStarted:
            if self.displayScore < self.score:
                self.set_score("%04d" % self.displayScore)
                self.displayScore += random.randint(1, 10)
            else:
                self.set_score("%04d" % self.score)

    # Create saloon environment
    def create_file_group(
        self,
        parent,
        child,
        t = Vec3f(0, 0, 0),
        s = Vec3f(1, 1, 1),
        r = Rotation(1, 0, 0, 0)
    ):
        g = hgn.Transform()
        g.translation = t
        g.scale = s
        g.rotation = r
        g.add(child)
        parent.add(g)
        return g

    def build_room(self):
        self.roomGroup = self.create_file_group(
            parent = self.worldGroup,
            child = X3DFileNode("room.x3d"),
            t = self.cameraPos1,
            r = self.cameraRot
        )

        self.barrelGroup = self.create_file_group(
            parent = self.roomGroup,
            child = X3DFileNode("barrel2.x3d"),
            t = Vec3f(-0.22, -0.2, 0.07),
            s = Vec3f(1.3, 1.3, 1.3)
        )

        self.bottleGroup = self.create_file_group(
            parent = self.roomGroup,
            child = X3DFileNode("bottle.x3d"),
            t = Vec3f(-0.20, -0.13, 0.07),
            s = Vec3f(0.8, 0.7, 0.8),
            r = (
                Rotation(1, 0, 0, math.pi / 2) *
                Rotation(0, 0, 1, math.pi / 6)
            )
        )

        self.sideboardGroup = self.create_file_group(
            parent = self.roomGroup,
            child = X3DFileNode("sideboard.x3d"),
            t = Vec3f(-0.15, -0.14, 0.17),
            s = Vec3f(0.5, 0.7, 0.63)
        )

        self.sideboardGroup2 = self.create_file_group(
            parent = self.roomGroup,
            child = X3DFileNode("sideboard.x3d"),
            t = Vec3f(0.15, -0.14, 0.17),
            s = Vec3f(0.5, 0.7, 0.63)
        )

        self.lampGroup = self.create_file_group(
            parent = self.roomGroup,
            child = X3DFileNode("lamp.x3d"),
            t = Vec3f(0.2, 0.02, 0.01),
            s = Vec3f(0.015, 0.015, 0.015),
            r = Rotation(0, 1, 0, -math.pi/2)
        )

        scoreTextGroup = hgn.Transform()
        scoreText = X3DNode("""
                <Group>
                <Shape>
                    <Appearance>
                        <Material diffuseColor="1 1 1" emissiveColor="1 1 1"/>
                    </Appearance>
                    <Text DEF="SCORE_TEXT" string="" >
                        <FontStyle family="Delicious" justify="MIDDLE" size="0.06" />
                    </Text>
                </Shape>
                </Group>
        """)
        scoreTextGroup.add(scoreText)
        scoreTextGroup.translation = Vec3f(0, -0.075, 0.031)
        self.roomGroup.add(scoreTextGroup)
        self.scoreTextNode = scoreText.dn["SCORE_TEXT"]

    # Temporary Hack
    def set_score(self, s):
        self.scoreTextNode.string.setValue([s])

    # Create bandit "moles"
    def build_bandits(self):
        targetGroup = hgn.Transform()
        self.roomGroup.add(targetGroup)
        targetGroup.scale = Vec3f(0.7, 0.7, 0.7)
        targetGroup.translation = Vec3f(0, -0.1, 0.1)

        targetPositions = [
            Vec3f(-0.13, 0, -0.04),
            Vec3f(0, 0, 0.03),
            Vec3f(0.13, 0, -0.04),
            Vec3f(-0.15, 0, 0.06),
            Vec3f(0.15, 0, 0.06),
        ]

        self.bandits = []

        difficulty = 0

        for pos in targetPositions:

            b = Mole(pos)
            targetGroup.add(b.transform)
            self.bandits.append(b)

            forceListener = ForceListener(b, self.hit, hitForce = 0.5)
            touchListener = TouchListener(b, self.touch)

            for geometry in b.geometries:
                geometry.isTouched.route(touchListener)
                geometry.force.route(forceListener)

            b.move_down()

            b.difficulty = difficulty
            difficulty += 1

        self.lastBanditTouched = self.bandits[1]

    # Setup initial camera motion
    def build_camera_motion(self):
        self.cameraMotion = ts = hgn.TimeSensor(
            cycleInterval = 2.0,
            loop = False,
            enabled = True
        )

        pi = hgn.SplinePositionInterpolator(
            key = [0, 0.5, 1.0],
            #keyVelocity = [0.1, 0.2, 0.3],
            keyValue = [
                self.cameraPos1,
                self.cameraPos2,
                self.cameraPos2,
            ]
        )

        hgt.world.add_nodes([ts, pi])

        ts.h3dNode.fraction_changed.route(
            pi.h3dNode.set_fraction
        )

        pi.h3dNode.value_changed.routeNoEvent(
            self.roomGroup.h3dNode.translation
        )

    # Setup music and sound effects
    def create_clip(self, url, intensity = SFX_VOLUME):
        clip = hgn.AudioClip(
            url = url,
            loop = False,
            startTime = -1
        )
        sound = hgn.Sound(
            clip,
            intensity = intensity
        )
        hgt.world.add_node(sound)
        return clip

    def build_audio(self):
        #theme = random.choice(["theme1.ogg", "theme2.ogg"])
        theme = "theme1.ogg"
        self.musicClip = self.create_clip(url = "sound/%s" % theme, intensity = MUSIC_VOLUME)
        self.hitClip = self.create_clip(url = "sound/hit.wav")
        self.missClip = self.create_clip(url = "sound/miss.wav")
        self.upClip = self.create_clip(url = "sound/up.wav")
        self.downClip = self.create_clip(url = "sound/down.wav")
        self.cashClip = self.create_clip(url = "sound/cash.wav")
        #self.ambientClip = self.create_clip(url = "sound/crowd.ogg")

        self.hitSound = Sound("sound/hit.wav", copies = 3)

        self.yells = []
        for i in range(9):
            #print i
            y = self.create_clip(url = "sound/yell%d.wav" % i)
            self.yells.append(y)

