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

# Racer
# Copyright Curictus AB

import hgt
from hgt.utils import *
from hgt.nodes import *
from hgt.gameelements import *
from H3DInterface import *
import hgt.game
from hgt.locale import translate as _

import random
import math
import datetime
import re

NUMBER_OF_LAPS = 1
MAX_VELOCITY_KPH = 140 # kph
VELOCITY_SCALE = 0.023
MAX_VELOCITY = MAX_VELOCITY_KPH * VELOCITY_SCALE
MAX_THUD_PERIOD = 0.2

# Frame delay for camera follow
CAMSTACK_SIZE = 10

# Radius and position (m) of goal sensors
fixme("Lap counter can be circumvented by driving back and forth across goal line.")
SENSOR_RADIUS = 1.0
SENSOR_P1 = Vec3f(0, 0, 0)
SENSOR_P2 = Vec3f(0, 0, -1.5)

# Blender exported track file
TRACK_DIR = "tracks/track2/"
TRACK_FILE = "tracks/track2/track2.x3d"

START_LAMP_PATTERN = "MA_lamp%d"
TRACK_CENTER_OBJECT = "coord_MidTrack"

# For debugging
ENABLE_TEXTURES = True
#ENABLE_TEXTURES = False

class Game(hgt.game.Game):
    def build(self):
        # Illuminate world
        hgt.world.headlight_off()
        hgt.world.stereoInfo.interocularDistance = 0.008
        hgt.world.stereoInfo.focalDistance = 1.00

        cfg = self.load_config()
        self.level = cfg.settings["racer_level"]
        self.setup_difficulty()

        self.build_lights()

        self.build_car()
        self.build_cam()
        self.build_hud()
        self.build_environment()
        self.build_sounds()
        self.build_controls()

        self.speed = 0
        self.started = False
        self.finished = False
        self.laps = 0
        self.maxLaps = 0

        self.previousSensorState = self.get_sensor_state()


    def setup_difficulty(self):
        global NUMBER_OF_LAPS
        global MAX_VELOCITY_KPH
        global VELOCITY_SCALE
        global MAX_VELOCITY

        if self.level == 1:
            NUMBER_OF_LAPS = 1
            MAX_VELOCITY_KPH = 100
            MAX_VELOCITY = MAX_VELOCITY_KPH * VELOCITY_SCALE
        elif self.level == 2:
            NUMBER_OF_LAPS = 2
            MAX_VELOCITY_KPH = 140
            MAX_VELOCITY = MAX_VELOCITY_KPH * VELOCITY_SCALE
        elif self.level == 3:
            NUMBER_OF_LAPS = 3
            MAX_VELOCITY_KPH = 180
            MAX_VELOCITY = MAX_VELOCITY_KPH * VELOCITY_SCALE
        else:
            assert(0)



    # Main update loop
    def update(self):
        if self.started and not self.finished:
            self.update_car()
            self.check_lap()
        if self.finished:
            self.car.momentum *= 0.95
            self.car.angularMomentum *= 0.95
            self.forceField.force *= 0.95
            self.update_cam(self.car.angularMomentum, self.car.momentum)

    def start(self):
        self.engineStartSound.play()
        self.startLampCounter = 0
        hgt.time.add_timeout(2, self.start_lamps)

    def start_lamps(self):
        lampColors = [
            RGB(1, 0, 0),
            RGB(1, 0, 0),
            RGB(1, 1, 0),
            RGB(0, 1, 0),
        ]

        # Turn on current start lamp only
        self.reset_lamps()
        self.startLamps[self.startLampCounter].diffuseColor = lampColors[self.startLampCounter]

        if self.startLampCounter == 3:
            self.startBeep2Sound.play()
            self.start_race()
        else:
            self.startBeepSound.play()
            self.startLampCounter += 1
            hgt.time.add_timeout(1, self.start_lamps)

    def start_race(self):
        self.arrowToggle.graphicsOn = True
        self.started = True
        self.startTime = hgt.time.now
        self.music.play()

    # Helper functions
    def reset_lamps(self):
        for l in self.startLamps:
            l.diffuseColor = RGB(0, 0, 0)

    def unthud(self):
        self.thuddable = True

    def get_sensor_state(self):
        s1 = (self.car.position - SENSOR_P1).length() < SENSOR_RADIUS
        s2 = (self.car.position - SENSOR_P2).length() < SENSOR_RADIUS
        return (s1, s2)

    def check_lap(self):
        goalPosition = Vec3f(0, 0, 0)
        c = self.car.position
        v = c - goalPosition
        d = v.length()

        state = self.get_sensor_state()

        if state != self.previousSensorState:
            if state == (False, False):
                if self.previousSensorState == (False, True):
                    self.laps += 1
                    self.maxLaps = self.laps
                    if self.laps > 1:
                        self.lapSound.play(location = self.car.position)
                if self.previousSensorState == (True, False):
                    self.laps -= 1
                    self.lapSound.play(location = self.car.position)
                self.update_lap()

            self.previousSensorState = state

    def update_lap(self):
        if self.laps >= self.maxLaps:
            # Goal reached
            if self.laps > NUMBER_OF_LAPS:
                self.finished = True
                self.set_result('max_result', 80.0)
                self.set_result('min_result', 0.0)
                self.set_result('result_type', 'min_seconds')
                self.set_result('result', hgt.time.now - self.startTime)

                self.log_score(
                    level = self.level,
                    duration = hgt.time.now - self.startTime
                )

                log_info("Racer finished")
                hgt.time.add_timeout(3, self.quit)
            else:
                self.lapText.text.string = ["%s/%s" % (self.laps, NUMBER_OF_LAPS)]


    def update_cam(self, a, m):
        if not self.finished:
            self.camStack.append((a,m))
            (a, m) = self.camStack.pop(0)
            self.cam.angularMomentum = a
            self.cam.momentum = m
        else:
            self.cam.angularMomentum = Vec3f(0, 0, 0)
            self.cam.momentum = Vec3f(0, 0, 0)

    def update_car(self):
        self.controls.update()

        c = self.car.position
        m = 100.0
        mv = mc = Vec3f(0, 0, 0)
        r = Rotation(1, 0, 0, -math.pi/2)
        for v in self.trackCoords:
            d = c - r*v
            if d.length() < m:
                m = d.length()
                mv = d
                mc = r*v
        #self.ball.translation = mc #+ Vec3f(0, 0.4, 0)

        self.car.angularMomentum = Vec3f(0, -self.controls.yaw * 1, 0) * 6

        co = self.car.orientation
        a = co.angle * co.y
        directionVector = Vec3f(-math.sin(a), 0, -math.cos(a))

        oldMom = self.car.momentum

        acc = self.controls.acceleration
        if self.car.velocity.length() > MAX_VELOCITY:
            acc = min(acc, 0)

        self.car.momentum = (
            directionVector * self.car.velocity.length() +
            directionVector * acc * 0.3
        )

        dist = 0.39
        if m > dist:
            counterForce = mv * (m - dist) * 8
            self.car.momentum -= counterForce

            if m > 0.20 and self.thuddable:
                self.thuddable = False
                rattle = random.choice(self.rattleSounds)
                rattle.play(location = self.car.position)
                timeout = MAX_THUD_PERIOD + ((MAX_VELOCITY - self.car.velocity.length()) / MAX_VELOCITY)
                hgt.time.add_timeout(timeout, self.unthud)
                f = self.controls.forceField.force
                f = f - counterForce * 10
                f2 = Vec3f(
                    clamp(f.x, -1, 1),
                    clamp(f.y, -1, 1),
                    clamp(f.z, -1, 1),
                )
                self.controls.forceField.force = f2

        self.update_cam(self.car.angularMomentum, self.car.momentum)

        kph = self.car.velocity.length() / VELOCITY_SCALE
        if kph < 2:
            kph = 0
        self.speedText.text.string = ["%d" % int(kph)]

        if not self.finished:
            dt = hgt.time.now - self.startTime
            minutes = dt / 60
            seconds = dt % 60
            millis = (dt - int(dt)) * 100
            self.timeText.text.string = ["%02d:%02d:%02d" % (minutes, seconds, millis)]
            #self.lapText.text.string = ["%d" % (self.laps)]

        self.arrow.rotation = Rotation(0, 1, 0, -self.controls.yaw * 4)
        #if self.controls.acceleration > 1:


        if self.controls.acceleration > 0:
            self.arrow2.scale = Vec3f(1, 1, 1) * 0.5 * (self.controls.acceleration * 30 + 1)
            self.arrow2.rotation = Rotation(1, 0, 0, 0)
            self.arrow2.translation = Vec3f(0, 0, -0.5)
        else:
            self.arrow2.rotation = Rotation(0, 1, 0, math.pi)
            self.arrow2.translation = Vec3f(0, 0, -1.0)

        # Friction
        if self.controls.acceleration < 0.05:
            self.car.momentum *= 0.99

    # DISABLED: distorted sounds, acquire real car samples
    # Theory: blend several constant car sound samples
    def update_sounds(self):
        v = clamp(self.car.momentum.length() / MAX_VELOCITY, 0, 1)
        sections = 10
        for i in range(sections):
            if i == 0:
                center = 0
            else:
                center = i / float(sections)
            val = v - center
            intensity = clamp((1 - ((val * sections) ** 2)), 0, 1)
            s = self.speedSounds[i]
            s.sound.intensity = intensity
            s.sound.location = self.car.position

    # Build functions
    def build_controls(self):
        self.controls = Controls(forceField = self.forceField, car = self.car)

    def build_lights(self):
        self.add_node(hgn.DirectionalLight(
            direction = Vec3f(0.2, -1, 0),
            intensity = 0.5
        ))
        self.add_node(hgn.DirectionalLight(
            direction = Vec3f(1, -1, 0),
            intensity = 0.5
        ))

    def build_sounds(self):
        # Thud flag, so off-track sounds don't repeat too often
        self.unthud()

        # Music
        self.music = Music("sounds/music.ogg", intensity = 0.4)

        # Track sounds
        self.startBeepSound = Sound("sounds/beep1.wav", intensity = 0.5)
        self.startBeep2Sound = Sound("sounds/beep2.wav", intensity = 0.5)
        self.lapSound = Sound("sounds/ding.wav", intensity = 0.5)

        # Variuos car sounds
        self.thudSound = Sound("sounds/thud1.wav", intensity = 0.5)
        self.engineStartSound = Sound("sounds/engine_start.wav", intensity = 0.3)

        self.rattleSounds = [
            Sound("sounds/rattle1.wav", intensity = 0.5),
            Sound("sounds/rattle2.wav", intensity = 0.5),
            Sound("sounds/rattle3.wav", intensity = 0.5),
        ]

    def build_car(self):
        d = X3DFileNode("car.x3d")
        t = hgn.Transform(scale = Vec3f(1, 1, 1))
        t.add(d)
        carToggle = hgn.ToggleGroup()
        carToggle.add(t)

        self.car = car = hgn.DynamicTransform()
        car.add(carToggle)
        self.add_node(car)

        self.arrowToggle = hgn.ToggleGroup(graphicsOn = False)
        self.arrow = hgn.Transform()
        self.arrow2 = hgn.Transform(translation = Vec3f(0, 0, -0.5))
        self.arrow2.add(X3DFileNode("arrow.x3d"))
        self.arrow.add(self.arrow2)
        self.arrowToggle.add(self.arrow)
        car.add(self.arrowToggle)

        # Disabled:

        # Tire rotation.
        fixme("Reenable tire rotation.")
        """
        self.ts = ts = hgn.TimeSensor(
            cycleInterval = 0.25,
            loop = True,
            enabled = True
        )

        oi = hgn.OrientationInterpolator(
            key = [0, 0.5, 1],
            keyValue = [
                Rotation(1, 0, 0, math.pi / 2),
                Rotation(1, 0, 0, 0),
                Rotation(1, 0, 0, -math.pi / 2),
            ]
        )

        ts.h3dNode.fraction_changed.route(
            oi.h3dNode.set_fraction
        )
        for n in [
            "Beetle_tire_RR",
            "Beetle_tire_RL",
            "Beetle_tire_FR",
            "Beetle_tire_FL",
        ]:
            oi.h3dNode.value_changed.routeNoEvent(
                d.dn[n].rotation
            )

        self.add_node(ts)
        self.add_node(oi)
        """

        # Car headlight. Doesn't look too good.
        """
        carLight = hgn.SpotLight(
            direction = Vec3f(0, 0, -1),
            cutOffAngle = math.pi / 8,
        )
        self.car.add(carLight)
        """

    def build_cam(self):
        self.cam = hgn.DynamicTransform()

        vp = hgn.Viewpoint(
            position = Vec3f(0, 0.5, 1),
            orientation = Rotation(1, 0, 0, -math.pi/15),
            fieldOfView = 0.5336
        )
        self.cam.add(vp)
        self.add_node(self.cam)

        self.camStack = []
        for i in range(CAMSTACK_SIZE):
            self.camStack.append((
                Vec3f(0, 0, 0),
                Vec3f(0, 0, 0),
            ))

        self.forceField = hgn.ForceField(
            force = Vec3f(0, 0, 0)
        )
        self.cam.add(self.forceField)

    def build_hud(self):
        self.speedText = hud = TextShape(string = ["0"])
        hud.material.emissiveColor = RGB(1, 1, 1)
        t = hgn.Transform(translation = Vec3f(0.25, 0.52, 0))
        t.add(hud.node)
        self.cam.add(t)

        hud = TextShape(size = 0.02, string = [_("KM/H")])
        hud.material.emissiveColor = RGB(1, 1, 1)
        t = hgn.Transform(translation = Vec3f(0.25, 0.49, 0))
        t.add(hud.node)
        self.cam.add(t)

        self.timeText = hud = TextShape(string = ["0:00:00"])
        hud.material.emissiveColor = RGB(1, 1, 1)
        t = hgn.Transform(translation = Vec3f(0, 0.52, 0))
        t.add(hud.node)
        self.cam.add(t)

        hud = TextShape(size = 0.02, string = [_("Time")])
        hud.material.emissiveColor = RGB(1, 1, 1)
        t = hgn.Transform(translation = Vec3f(0, 0.49, 0))
        t.add(hud.node)
        self.cam.add(t)

        self.lapText = hud = TextShape(string = ["1/%s" % NUMBER_OF_LAPS])
        hud.material.emissiveColor = RGB(1, 1, 1)
        t = hgn.Transform(translation = Vec3f(-0.25, 0.52, 0))
        t.add(hud.node)
        self.cam.add(t)

        hud = TextShape(size = 0.02, string = [_("Lap", "Laps", count=NUMBER_OF_LAPS)])
        hud.material.emissiveColor = RGB(1, 1, 1)
        t = hgn.Transform(translation = Vec3f(-0.25, 0.49, 0))
        t.add(hud.node)
        self.cam.add(t)

    def build_environment(self):
        f = open(TRACK_FILE)
        t = f.read()
        f.close()

        if ENABLE_TEXTURES:
            t = re.sub(r'(ImageTexture[^>]+url=")', '\\1' + TRACK_DIR, t)
        else:
            t = re.sub(r"\<ImageTexture [^>]+\>", "", t)

        self.trackNode = d = X3DNode(t)

        t = hgn.Transform(scale = Vec3f(1, 1, 1))
        t.add(d)
        self.add_node(t)

        self.trackCoords = d.dn[TRACK_CENTER_OBJECT].point.getValue()

        b = hgn.Background(
            skyColor = [
                RGB(0, 0, 0.15),
                RGB(0, 0, 0.25),
                RGB(0, 0.5, 0.5),
            ],
            skyAngle = [
                math.pi / 2.5,
                math.pi / 2
            ]
        )
        self.add_node(b)

        c1 = Shape(
            geometry = hgn.Disk2D(
                outerRadius = SENSOR_RADIUS,
            ),
            material = hgn.Material(diffuseColor = RGB(0, 0, 0)),
        )
        ct = hgn.Transform(
            translation = SENSOR_P1 + Vec3f(0, 0.01, 0),
            rotation = Rotation(1, 0, 0, math.pi / 2),
        )
        ct.add(c1.node)
        #t.add(ct)

        c2 = Shape(
            geometry = hgn.Disk2D(
                outerRadius = SENSOR_RADIUS,
            ),
            material = hgn.Material(diffuseColor = RGB(1, 1, 1)),
        )
        ct2 = hgn.Transform(
            translation = SENSOR_P2 + Vec3f(0, 0, 0),
            rotation = Rotation(1, 0, 0, math.pi / 2),
        )
        ct2.add(c2.node)
        #t.add(ct2)

        self.startLamps = []
        for i in range(4):
            self.startLamps.append(self.trackNode.find(START_LAMP_PATTERN % (i + 1)))
        self.reset_lamps()

class Controls(object):
    def __init__(self, forceField, car):
        self.forceField = forceField
        self.car = car

        self.acceleration = 0.0
        self.yaw = 0.0
        self.braking = False

    def update(self):
        self.velocity = self.car.velocity.length()
        pos = hgt.haptics.devicePosition

        # Arbitrary non-linear mapping of steering (yaw)
        a = 0.18
        p = pos.x / a
        e = 1.5
        pe = abs(p) ** e
        o = pe * a * sgn(p)
        #self.yaw = -o
        # Also reverse force below!
        self.yaw = o

        z = -pos.z # forward = positive direction
        if z > -0.03:
            self.acceleration = max(0, z + 0.03)
            self.stop_braking()

        elif z < -0.05:
            self.acceleration = z * 5
            self.brake()

        self.forceField.force = Vec3f(
            clamp(min(1.0, -self.yaw * 10 * self.velocity), -1, 1),
            0,
            clamp(max(0, self.acceleration * 20), 0, 1)
        )

        self.acceleration = clamp(self.acceleration, -3, 0.09)

    def brake(self):
        if not self.braking:
            self.braking = True

    def stop_braking(self):
        self.braking = False
