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
from H3DUtils import *
from hgt.gameelements import *
from hgt.locale import translate as _

import hgt.game
import random
import math

import space

COURT_WIDTH = 0.3
COURT_HEIGHT = 0.2
COURT_DEPTH = 0.6

PLAYER_PAD_RADIUS = 0.035
OPPONENT_PAD_RADIUS = 0.035
BALL_RADIUS = 0.015
SERVE_TOLERANCE = 0.04
CHEER_WAIT = 2.0
TRAIL_LENGTH = 15
# Minimum time to wait before opponent serves
OPPONENT_SERVE_MIN_DELAY = 1.5
# Maximum time to wait after minimum delay before opponent serve
OPPONENT_SERVE_RANDOM_DELAY = 1.0

SHADOW_Y = -((COURT_HEIGHT + BALL_RADIUS * 2) / 2) * 0.99

class Game(hgt.game.Game):
    def build(self):
        hgt.world.hide_stylus()
        hgt.world.stereoInfo.focalDistance = 0.45
        hgt.world.stereoInfo.interocularDistance = 0.01

        random.seed()

        cfg = self.load_config()
        self.level = cfg.settings["pong_level"]

        self.racketOffset = Vec3f(0, 0.05, 0)

        # Level 1 - Easy
        if self.level == 1:
            # The probability (0-1) that the opponent will hit the ball
            self.blockProbability = 0.9

            # Ball speed, in m/s
            self.initialBallSpeed = 0.4

            # The number of racket bounces until the ball's speed has increased to
            # double the initial speed
            self.hitsUntilSpeedDoubling = 30

        # Level 2 - Medium
        elif self.level == 2:
            self.blockProbability = 0.9
            self.initialBallSpeed = 0.7
            self.hitsUntilSpeedDoubling = 40

        # Level 3 - Hard
        elif self.level == 3:
            self.blockProbability = 0.9
            self.initialBallSpeed = 1.1
            self.hitsUntilSpeedDoubling = 30

        self.ballSpeed = self.initialBallSpeed

        # Add ball trail spheres (must be added before player pads due to transparency
        self.build_trail()

        # Import blender world
        self.add_child(space.world)

        self.ball = Ball(ballNode = space.nodes["Transform_BALL"], radius = BALL_RADIUS)
        self.playerPad = Pad(radius = PLAYER_PAD_RADIUS)
        self.opponentPad = Pad(radius = OPPONENT_PAD_RADIUS)

        # add HGT nodes
        self.add_nodes([
            self.ball.dt,
            self.ball.shadow.transform,
            self.opponentPad.node, # add before player pad
            self.playerPad.node,
        ])

        # "Laser" marker for testing out new AI
        self.laser = space.nodes["Transform_LASER"]

        # score markers
        self.build_markers()

        self.scoreText = space.nodes["Text_SCORE"]
        scoreMaterial = space.nodes["Material_SCORE"]
        scoreMaterial.emissiveColor = RGB(1, 1, 1)
        scoreMaterial.diffuseColor = RGB(0, 0, 0)

        self.msgText = space.nodes["Text_MSG"]
        msgMaterial = space.nodes["Material_MSG"]
        msgMaterial.transparency = 1.0
        msgMaterial.emissiveColor = RGB(1, 1, 1)
        msgMaterial.diffuseColor = RGB(0, 0, 0)
        self.msgFlasher = self.build_transparency_interpolator(msgMaterial)

        self.playerLampMaterial = space.nodes["Material_BallMarker1"]
        self.opponentLampMaterial = space.nodes["Material_BallMarker2"]

        # force field
        self.forceField = hgn.ForceField()
        self.add_node(self.forceField)

        # sounds
        self.ballSound = Sound(url = "sounds/thud2.wav", intensity = 0.5)
        self.wallSound = Sound(url = "sounds/thud.wav", intensity = 0.5)
        self.cheerSound = Sound(url = "sounds/cheer.wav", intensity = 0.5)
        self.dingSound = Sound(url = "sounds/ding.wav", intensity = 0.5)

        self.add_nodes([
            self.ballSound.node,
            self.wallSound.node,
            self.cheerSound.node,
            self.dingSound.node,
        ])

        # game variables
        self.playerServing = False
        self.opponentServing = False
        self.ballMovingAway = False
        self.resetPending = False

        self.hitLocation = Vec3f(0, 0, 0)
        self.missVector = Vec3f(0, 0, 0)
        self.hitLocationKnown = False
        self.winThisBall = False
        self.gameOver = False

        self.playerScore = 0
        self.opponentScore = 0

        self.opponentPad.dt.position = Vec3f(0, 0, -COURT_DEPTH)

        self.update_score()

        self.playing = True

    def start(self):
        self.reset_ball()
        hgt.time.add_timeout(1.0, self.countdown, (3,))

    def countdown(self, i):
        if i > 0:
            self.flash_msg(str(i), t = 0.9)
            hgt.time.add_timeout(1.0, self.countdown, (i - 1,))
        else:
            self.flash_msg(_("Play!"), t = 3.0)
            self.startTime = hgt.time.now
            self.player_serve()

    def player_serve(self):
        self.playerServing = True
        self.ballMovingAway = True
        self.ball.dt.position = Vec3f(0, 0, 0)
        self.reset_ball()

        self.opponentLampMaterial.diffuseColor = RGB(0.073, 0.323, 0.11)
        self.opponentLampMaterial.emissiveColor = RGB(0, 0, 0)
        self.playerLampMaterial.diffuseColor = RGB(0.186, 0.825, 0.281)
        self.playerLampMaterial.emissiveColor = RGB(0.067, 0.295, 0.1)

    def opponent_serve(self):
        self.opponentServing = True
        self.opponentServingTime = hgt.time.now + OPPONENT_SERVE_MIN_DELAY + random.random() * OPPONENT_SERVE_RANDOM_DELAY
        self.ballMovingAway = False
        self.ball.dt.position = Vec3f(0, 0, -COURT_DEPTH)
        self.reset_ball()

        self.playerLampMaterial.diffuseColor = RGB(0.073, 0.323, 0.11)
        self.playerLampMaterial.emissiveColor = RGB(0, 0, 0)
        self.opponentLampMaterial.diffuseColor = RGB(0.186, 0.825, 0.281)
        self.opponentLampMaterial.emissiveColor = RGB(0.067, 0.295, 0.1)

    def reset_ball(self):
        self.resetPending = False
        self.ball.dt.momentum = Vec3f(0, 0, 0)
        self.ball.dt.angularMomentum = Vec3f(0, 0, 0)

    def update(self):
        # dampen force field
        if self.forceField.force.length() > 0.0:
            self.forceField.force *= 0.9

        # update player pad
        tp = hgt.haptics.trackerPosition
        tp.z = clamp(tp.z, -0.2, 10)
        tp += self.racketOffset
        self.playerPad.dt.position = tp

        # update shadows
        self.playerPad.update_shadow(elevation = SHADOW_Y)
        self.opponentPad.update_shadow(elevation = SHADOW_Y)
        self.ball.update_shadow(elevation = SHADOW_Y)

        # perform various checks
        self.update_ball()
        self.update_opponent()
        self.check_wall_collisions()

        if not self.resetPending:
            self.check_hits()
            self.check_outside()

    # states
    def check_hits(self):
        m = self.ball.dt.momentum
        bp = self.ball.dt.position

        pp = self.playerPad.dt.position
        dv = bp - pp

        pp2 = self.opponentPad.dt.position
        dv2 = bp - pp2

        nearPlayer = within(pp.z - bp.z, 0, SERVE_TOLERANCE)
        nearOpponent = within(pp2.z - bp.z, 0, SERVE_TOLERANCE)

        # player serve
        if self.playerServing and nearPlayer:
            if dv.length() < PLAYER_PAD_RADIUS + BALL_RADIUS:
                self.ballSpeed = self.initialBallSpeed
                self.haptic_ball_collision(dv)
                self.playerServing = False

        # opponent serve
        if self.opponentServing:
            if self.opponentServingTime < hgt.time.now:
                self.opponentServing = False
                self.ballMovingAway = False
                self.ballSpeed = self.initialBallSpeed
                self.ball.dt.momentum = Vec3f((random.random() * 0.5 - 0.25), m.y, self.ballSpeed).normalize() * self.ballSpeed
                self.ballSound.play(location = self.ball.dt.position)

        # collision with opponent
        if self.ballMovingAway:
            if nearOpponent:
                if dv2.length() < OPPONENT_PAD_RADIUS + BALL_RADIUS:
                    self.ball.dt.momentum = Vec3f(m.x, m.y, -m.z)
                    self.ballMovingAway = False
                    self.ballSound.play(location = self.ball.dt.position)
                    self.ballSpeed += self.ballSpeedAcceleration

        # collision with player
        else:
            if nearPlayer:
                if dv.length() < PLAYER_PAD_RADIUS + BALL_RADIUS:
                    self.haptic_ball_collision(dv)
                    self.ballSpeed += self.ballSpeedAcceleration

    def haptic_ball_collision(self, dv):
        vel = hgt.haptics.deviceVelocity.length()

        speed = self.ballSpeed
        dv.z = 0.0
        #m = dv * 8 + Vec3f(0, 0, -speed)
        m = (dv * 8 + Vec3f(0, 0, -speed)).normalize() * speed
        self.ball.dt.momentum = m
        self.ballSound.play(location = self.ball.dt.position)
        self.forceField.force = Vec3f(0, 0, 3)
        self.ballMovingAway = True

        if random.random() < self.blockProbability:
            self.winThisBall = True
            self.missVector = \
                random.random() * \
                (Rotation(0, 0, 1, 2 * math.pi * random.random()) * \
                Vec3f(1, 1, 0) * (OPPONENT_PAD_RADIUS * random.random()))
        else:
            self.winThisBall = False
            self.missVector = \
                Rotation(0, 0, 1, 2 * math.pi * random.random()) * \
                Vec3f(1, 1, 0) * (OPPONENT_PAD_RADIUS + BALL_RADIUS)

    def update_ball(self):
        m = self.ball.dt.momentum

        if self.resetPending:
            m *= 0.99

        self.ball.dt.momentum = m
        self.ball.dt.angularMomentum = 5 * (Rotation(0, 1, 0, math.pi / 2) * m)

        # Ball trail
        self.ballpos.append(self.ball.dt.position)
        if len(self.ballpos) > TRAIL_LENGTH:
            self.ballpos.pop(0)
        for (p, index) in zip(self.ballpos, range(len(self.ballpos))):
            self.trail[index].translation = p

    # Ball trail
    def build_trail(self):
        self.trail = []
        self.ballpos = []

        for x in range(TRAIL_LENGTH):
            r = 0.001 + (BALL_RADIUS) * ((x / float(TRAIL_LENGTH)) ** 2.5)
            t = hgn.Transform()
            a = hgn.Appearance()
            m = hgn.Material(
                emissiveColor = RGB(1, 1, 1),
                transparency = 0.7
            )
            sh = hgn.Shape()
            s = hgn.Sphere(radius = r)
            a.material = m
            sh.appearance = a
            sh.geometry = s
            t.add(sh)
            self.add_child(t)
            self.trail.append(t)

    def update_opponent(self):
        self.calculate_game_properties()

        bp = self.ball.dt.position
        pp = self.playerPad.dt.position
        pp2 = self.opponentPad.dt.position

        ballVector = bp - pp2
        ballVector.z = 0

        playerVector = pp - pp2
        playerVector.z = 0

        serveVector = -pp2
        serveVector.z = 0

        opponentVector = playerVector
        opponentVector.z = 0

        self.find_intersection(
            self.ball.dt.position,
            self.ball.dt.momentum,
            pp2.z
        )

        if self.winThisBall:
            hitLocationVector = self.hitLocation + self.missVector - pp2
        else:
            hitLocationVector = self.hitLocation + self.missVector - pp2
        hitLocationVector.z = 0

        if self.resetPending or self.opponentServing:
            self.opponentPad.dt.momentum = serveVector * 4
        elif self.ballMovingAway:
            if self.hitLocationKnown:
                if bp.z < -COURT_DEPTH / 2.0 :
                    self.opponentPad.dt.momentum = hitLocationVector * self.momentumAcc
                else:
                    self.opponentPad.dt.momentum = opponentVector * 0.2
            else:
                self.opponentPad.dt.momentum = opponentVector
        else:
            self.opponentPad.dt.momentum = opponentVector

    def calculate_game_properties(self):
        self.ballSpeedAcceleration = self.initialBallSpeed / float(self.hitsUntilSpeedDoubling)
        ballFactor = self.ballSpeed / self.initialBallSpeed
        self.momentumAcc = self.ballSpeed * 6

    def find_intersection(self, p, v, zd):
        self.hitLocation = Vec3f(-10, -10, 0)
        self.hitLocationKnown = False
        if self.ballMovingAway and v.z != 0:
            t = (zd - p.z) / v.z
            x = p.x + v.x * t
            y = p.y + v.y * t

            w = COURT_WIDTH / 2.0
            h = COURT_HEIGHT / 2.0

            x = clamp(x, -w, w)
            y = clamp(y, -h, h)

            self.hitLocation = Vec3f(x, y, zd)
            self.hitLocationKnown = True

        # "Laser" sight, for debugging/development
        self.laser.translation = Vec3f(10, 0, 0) #self.hitLocation

    def check_wall_collisions(self):
        bp = self.ball.dt.position
        m = self.ball.dt.momentum

        # check for wall collisions
        if not within(bp.x, -COURT_WIDTH / 2, COURT_WIDTH / 2):
            if sgn(bp.x) == sgn(m.x):
                m.x = -m.x * 0.9
                self.ball.dt.momentum = m
                self.wallSound.play(location = bp)
        if not within(bp.y, -COURT_HEIGHT / 2, COURT_HEIGHT / 2):
            if sgn(bp.y) == sgn(m.y):
                m.y = -m.y * 0.9
                self.ball.dt.momentum = m
                self.wallSound.play(location = bp)

    def check_outside(self):
        m = self.ball.dt.momentum
        bp = self.ball.dt.position

        if bp.z > 0.3 and sgn(m.z) > 0:
            self.opponentScore += 1
            self.update_score()
            self.dingSound.play()
            self.playerMarker.startTime = hgt.time.now
            if self.playing:
                self.resetPending = True
                hgt.time.add_timeout(CHEER_WAIT, self.player_serve)
            else:
                self.ball.dt.position = Vec3f(0, 0.6, 0.3)
                self.ball.dt.momentum = Vec3f(0, 0, 0)

        if bp.z < -COURT_DEPTH - 0.1 and sgn(m.z) < 0:
            self.playerScore += 1
            self.flash_msg(_("Great!"))
            self.update_score()
            self.cheerSound.play()
            self.dingSound.play()
            self.opponentMarker.startTime = hgt.time.now
            if self.playing:
                self.resetPending = True
                hgt.time.add_timeout(CHEER_WAIT, self.opponent_serve)
            else:
                self.ball.dt.position = Vec3f(0, 10, 10)
                self.ball.dt.momentum = Vec3f(0, 0, 0)

    def update_score(self):
        scrStr = "%02d - %02d" % (self.playerScore, self.opponentScore)
        self.scoreText.string = [scrStr]

        if self.playerScore == 5 or self.opponentScore == 5:
            self.playing = False
            self.gameOver = True
            win = self.playerScore > self.opponentScore

            self.log_score(
                level = self.level,
                player_score = self.playerScore,
                opponent_score = self.opponentScore,
                win = win,
                duration = hgt.time.now - self.startTime,
            )

            hgt.time.add_timeout(4, self.quit)

    def build_markers(self):
        self.opponentMarker = self.build_marker(space.nodes["Material_OpponentMarker"])
        self.playerMarker = self.build_marker(space.nodes["Material_PlayerMarker"])

    def build_marker(self, m):
        ti = hgn.TimeSensor(
            cycleInterval = 0.5,
            loop = False
        )
        co = hgn.ColorInterpolator(
            key = [0, 0.8, 1],
            keyValue = [
                RGB(0, 1, 0),
                RGB(0, 1, 0),
                RGB(0, 0, 0)
            ]
        )
        self.add_node(ti)
        self.add_node(co)
        ti.h3dNode.fraction_changed.route(
            co.h3dNode.set_fraction
        )
        co.h3dNode.value_changed.routeNoEvent(
            m.h3dNode.emissiveColor
        )
        return ti

    def build_transparency_interpolator(self, m):
        ti = hgn.TimeSensor(
            cycleInterval = 2.0,
            loop = False
        )
        si = hgn.ScalarInterpolator(
            key = [0, 0.5, 1],
            keyValue = [
                0.0,
                0.0,
                1.0
            ]
        )
        self.add_node(ti)
        self.add_node(si)
        ti.h3dNode.fraction_changed.route(
            si.h3dNode.set_fraction
        )
        si.h3dNode.value_changed.routeNoEvent(
            m.h3dNode.transparency
        )
        return ti

    def flash_msg(self, msg, t = 1.5):
        self.msgText.string = [msg]
        self.msgFlasher.cycleInterval = t
        self.msgFlasher.startTime = hgt.time.now

# Game Elements
class Shadow:
    def __init__(self, radius):
        self.shadow = shadow = Shape(hgn.Disk2D(outerRadius = radius))
        shadow.material.diffuseColor = RGB(0, 0, 0)
        shadow.material.shininess = 0.0
        shadow.material.transparency = 0.5

        self.transform = hgn.Transform(rotation = Rotation(1, 0, 0, math.pi/2)) #, scale=Vec3f(1, 0.1, 1))
        self.transform.add(shadow.node)

class Ball:
    def __init__(self, ballNode, radius = 0.015):
        self.radius = radius
        self.dt = hgn.DynamicTransform(position = Vec3f(0, 0.8, 0), mass = 1.0)
        ballNode.reparent(self.dt)
        self.shadow = Shadow(radius = self.radius)

    def update_shadow(self, elevation = 0.0):
        pp = self.dt.position
        pp.y = elevation + 0.001
        self.shadow.transform.translation = pp

        t = (self.dt.position.y - elevation) * 4
        self.shadow.shadow.material.transparency = t
        self.shadow.transform.scale = (t + 1.0) * Vec3f(1, 1, 1)

def build_pad_shadow(radius):
        shadow = Shape(hgn.Disk2D(outerRadius = radius))
        shadow.material.diffuseColor = RGB(0, 0, 0)
        shadow.material.shininess = 0.0
        shadow.material.transparency = 0.5

        shadowTransform = hgn.Transform(rotation = Rotation(1, 0, 0, math.pi/2), scale=Vec3f(1, 0.3, 1))
        shadowTransform.add(shadow.node)

        return shadowTransform

class Pad(GameElement):
    def __init__(self, radius = 0.035):
        self.radius = radius

        self.dt = self.padTransform = hgn.DynamicTransform(mass = 1.0)

        racket = X3DFileNode("racket.x3d")
        self.padTransform.add(racket)
        self.add_node(self.padTransform)

        # shadow
        self.shadowTransform = build_pad_shadow(radius = self.radius)
        self.add_node(self.shadowTransform)

    def update_shadow(self, elevation = 0.0):
        pp = self.dt.position
        pp.y = elevation
        self.shadowTransform.translation = pp

