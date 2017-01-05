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
from hgt.listeners import MFBoolListener
from hgt.locale import translate as _
from hgt.nodes import *
from hgt.widgets.pushbutton import PushButton
from hgt.gameelements import Sound
from grabber import GrabManager, GrabObject
import hgt.game
import math
import random

import space

SPACE_TILT = 65.0
DEG2RAD = math.pi / 180.0
EXIT_TIME = 1.0

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        cfg = self.load_config()

        # Setup hgt world
        hgt.world.tilt(-SPACE_TILT)
        hgt.world.stereoInfo.focalDistance = 0.50
        hgt.world.load_stylus('ball')
        #hgt.world.load_stylus('spoon')

        # Load Blender scene
        self.add_child(space.world)

        # Force field used to simulate drag/gravity for grabbable objects
        self.forceField = hgn.ForceField()
        self.add_child(self.forceField)

        # Matrix used to compensate for TILT
        self.tiltMatrix = Rotation(1, 0, 0, SPACE_TILT * DEG2RAD)

        self.grabManager = GrabManager(self, self.tiltMatrix)

        self.build_environment()
        self.build_sounds()

        # Add apples in scene as grabbable objects
        for i in [("Apple", 0.3), ("Strawberry", 0.1), ("Melon", 1.0), ("Orange", 0.3)]:
            thing = GrabObject(self.grabManager, space.nodes, name = i[0], mass = i[1])

    def start(self):
        space.nodes["Text_UserMessage"].string = [_("Touch everything.")]
        space.nodes["Text_UserMessage2"].string = [_("Press exit sign when done.")]
        self.startTime = hgt.time.now

    def update(self):
        #print self.tiltMatrix * hgt.haptics.trackerPosition
        self.grabManager.update()
        self.update_trail()
        self.update_earth()
        self.update_guide_arrow()
        self.update_fish()

    def update_guide_arrow(self):
        # Bob the arrow up and down if it's visible
        if self.guideToggle.graphicsOn:
            v = Vec3f(0, 0, 0.005 * math.cos(hgt.time.now * 3))
            self.guideArrow.translation = v

    def update_fish(self):
        o = self.fishTransform.orientation
        m = o * (0.005 * Vec3f(-1, 0, 0))
        self.fishTransform.momentum = m

    def update_earth(self):
        f = hgt.haptics.deviceForce
        if self.touchingEarth:
            # This is just plain wrong, you can only spin the earth in one direction...
            self.earthSpinner.torque = f
        else:
            self.earthSpinner.torque = Vec3f(0, 0, 0)

        # Simulate friction
        self.earthSpinner.angularMomentum = 0.995 * Vec3f(0, 0, self.earthSpinner.angularMomentum.z)

    def update_trail(self):
        # Todo: see if we can add the trail to the topmost (untilted) node to
        # remove the need for tilt compensation
        tp = self.tiltMatrix * hgt.haptics.proxyPosition
        self.trailParticleEmitter.position = tp
        #self.particleTrail.translation = tp
        #self.stylusLight.location = tp

    def clear_user_message(self):
        space.nodes["Text_UserMessage"].string = [" "]
        space.nodes["Text_UserMessage2"].string = [" "]

    def build_environment(self):
        # Spinning earth
        self.earthSpinner = hgn.DynamicTransform(
            angularMomentum = Vec3f(0, 0, 0)
        )
        space.nodes["Transform_EarthSea"].reparent_children_to(self.earthSpinner)

        bl = MFBoolListener(
            onTrue = self.touch_earth,
            onFalse = self.untouch_earth,
        )
        space.nodes["Mesh_EarthSea"].h3dNode.isTouched.routeNoEvent(bl)

        self.touchingEarth = False

        # Touchable fruit plate bottom, coupled to release of grabbed objects
        bl = MFBoolListener(
            onTrue = self.grabManager.release,
        )
        space.nodes["Mesh_GrabReleaseSensor"].h3dNode.isTouched.routeNoEvent(bl)

        # Bobbing guide arrow
        self.guideArrow = hgn.Transform()
        self.guideToggle = hgn.ToggleGroup(graphicsOn = False)
        self.guideArrowPos = space.nodes["Transform_GuideArrow"]
        self.guideArrowPos.reparent_children_to(self.guideArrow)
        self.guideArrowPos.reparent_children_to(self.guideToggle)

        # A light that follows the stylus
        """
        self.stylusLight = hgn.PointLight(
            intensity = 0.1,
            attenuation = Vec3f(0, 10, 50),
        )
        self.add_child(self.stylusLight)
        """

        # An unreachable fish swimming in the aquarium
        self.fishTransform = hgn.DynamicTransform(
            position = Vec3f(0, 0.24, 0),
            angularMomentum = Vec3f(0, 0, 0.075),
        )
        fish = X3DFileNode("fish.x3d")
        self.fishTransform.add(fish)
        self.add_child(self.fishTransform)

        # A button that toggles the "aquarium light" on/off. Really controls
        # the aquarium glass transparency.
        button = space.nodes["Transform_LightButton"]
        buttonMesh = space.nodes["Mesh_LightButton"]
        b = PushButton(
            transformNode = button.h3dNode,
            geometry = buttonMesh.h3dNode,
            onPress = self.press_aquarium_button,
            displacement = Vec3f(0, 0.0025, 0),
            hitForce = 1.0,
        )
        space.nodes["ToggleGroup_AquariumGlassEmpty"].graphicsOn = False
        self.aquariumLightOn = False

        self.aquariumLamp = space.nodes["PointLight_AquariumLamp"]
        self.exitLamp = space.nodes["PointLight_ExitLamp"]

        # Tapping on aquarium glass
        bl = MFBoolListener(
            callbackObject = None,
            onTrue = self.tap_glass,
        )
        space.nodes["Mesh_AquariumGlass"].h3dNode.isTouched.routeNoEvent(bl)

        # Something that when touched initiates the exit procedure
        bl = MFBoolListener(
            callbackObject = None,
            onTrue = self.initiate_exit,
        )
        space.nodes["Mesh_ExitSign"].h3dNode.isTouched.routeNoEvent(bl)
        self.exitSignMaterial = space.nodes["Material_ExitSign"]
        self.exiting = False
        self.readyToQuit = False

        # Particle systems

        # Device trail
        p = X3DFileNode("trail_particles.x3d")
        self.trailParticleEmitter = p.find("EMITTER")
        self.add_child(p)

        # Aquarium bubbles
        #p = X3DFileNode("bubble_particles.x3d")
        #self.add_child(p)
        #self.bubbleParticleSystem = p.find("PARTICLE_SYSTEM")
        #self.bubbleParticleSystem.createParticles = False

    def build_sounds(self):
        self.lightOnSound = Sound("sounds/light_on.wav", intensity = 1.0, copies = 2)
        self.lightOffSound = Sound("sounds/light_off.wav", intensity = 1.0, copies = 2)
        self.melonDropSound = Sound("sounds/melon_drop.wav", intensity = 1.0)
        self.glassTapSound = Sound("sounds/glass_tap.wav", intensity = 0.25, copies = 4)
        self.exitSwitchSound = Sound("sounds/exit_switch.wav", intensity = 0.5, copies = 3)
        self.squeakSound = Sound("sounds/squeak.wav", intensity = 0.5)

    def press_aquarium_button(self, event):
        self.clear_user_message()

        if self.aquariumLightOn:
            self.lightOffSound.play()
            self.aquariumLamp.intensity = 0.0
            #self.bubbleParticleSystem.createParticles = False
        else:
            self.lightOnSound.play()
            self.aquariumLamp.intensity = 0.3
            #self.bubbleParticleSystem.createParticles = True
        self.aquariumLightOn = not self.aquariumLightOn

    def touch_earth(self):
        self.clear_user_message()

        space.nodes["Text_UserMessage"].string = []

        self.touchingEarth = True

        # "The Earth only squeaks when it's not spinning"
        # -Fantomen
        az = self.earthSpinner.angularMomentum.z
        l = 0.08
        if az > -l and az < l:
            self.squeakSound.play(location = hgt.haptics.trackerPosition)

    def untouch_earth(self):
        self.touchingEarth = False

    def tap_glass(self):
        self.clear_user_message()

        self.glassTapSound.play(location = hgt.haptics.trackerPosition)

    def initiate_exit(self):
        self.clear_user_message()

        if not self.exiting:
            self.exitSignMaterial.emissiveColor = RGB(1, 1, 1)
            self.exitLamp.intensity = 0.25
            self.exitSwitchSound.play(location = hgt.haptics.trackerPosition)
            self.exiting = True
            self.exitTimeout = hgt.time.add_timeout(EXIT_TIME, self.check_exit)

    def check_exit(self):
        if self.exiting == True:
            space.nodes["PointLight_LeftLamp"].intensity = 0.2
            space.nodes["PointLight_RightLamp"].intensity = 0.2

            self.lightOffSound.play()
            self.aquariumLamp.intensity = 0.0

            hgt.time.add_timeout(EXIT_TIME, self.quit)
