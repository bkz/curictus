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
import hgt.game

from hgt.event import Event
from hgt.gameelements import Sound
from hgt.locale import translate as _
from hgt.gamemath import DEG2RAD
from hgt.nodes import X3DFileNode
from hgt.widgets.pushbutton import PushButton

from H3DUtils import *
import math
import random

import space

SPACE_TILT = 65.0
TOTAL_NUMBER_OF_BUTTONS = 12

REMINDER_PERIOD = 5.0

class Game(hgt.game.Game):
    def build(self):
        random.seed()
        hgt.world.tilt(-SPACE_TILT)

        cfg = self.load_config()
        self.level = cfg.settings["simon2_level"]

        if self.level == 1:
            self.level_button_ids = [11, 10, 9, 8]
            self.level_sounds = 'C3 F3 A3 C4'.split()
            self.play_interval = 0.5
        elif self.level == 2:
            self.level_button_ids = [12, 11, 10, 9, 8, 7]
            self.level_sounds = 'C3 F3 A3 C4 F5 A5'.split()
            self.play_interval = 0.45
        elif self.level == 3:
            self.level_button_ids = [
                12, 11, 10, 9, 8, 7,
                6, 5, 4, 3, 2, 1,
            ]
            self.level_sounds = 'C3 E3 G3 A3 C4 E4 G4 A4 C5 E5 G5 A5'.split()
            self.play_interval = 0.4

        assert(len(self.level_button_ids) == len(self.level_sounds))

        # Setup hgt world
        hgt.world.stereoInfo.focalDistance = 0.45
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        self.build_world()

        # Game vars
        self.player_input_enabled = False
        self.waiting_for_release = False
        self.sequence = []

    def start(self):
        self.start_time = hgt.time.now
        hgt.time.add_timeout(1.0, self.reset)

    def reset(self):
        hgt.time.add_timeout(1.0, self.reset_sequence)

        self.reminder_timeout = None

    # Game states
    def reset_sequence(self):
        self.sequence = []
        self.sequence_length_text.string = []
        hgt.time.add_timeout(1.0, self.play_sequence)

    def play_sequence(self):
        self.led_on(1)
        self.switch_sound.play()
        if len(self.sequence) > 0:
            self.sequence_length_text.string = [str(len(self.sequence))]
        self.sequence.append(random.choice(self.buttons))
        self.tmp_play_sequence = self.sequence[:]
        hgt.time.add_timeout(2.0, self.play_sequence2)

    def play_sequence2(self):
        self.reset_materials()
        hgt.time.add_timeout(self.play_interval, self.play_sequence3)

    def play_sequence3(self):
        b = self.tmp_play_sequence.pop(0)
        self.play_button_sound(b)
        self.glow_on(b)

        if len(self.tmp_play_sequence) > 0:
            hgt.time.add_timeout(self.play_interval, self.play_sequence2)
        else:
            hgt.time.add_timeout(self.play_interval, self.sequence_played)

    def sequence_played(self):
        self.reset_materials()
        hgt.time.add_timeout(0.5, self.sequence_played2)

    def sequence_played2(self):
        self.led_on(2)
        self.tmp_repeat_sequence = self.sequence[:]
        self.player_input_enabled = True

        self.reminder_timeout = hgt.time.add_timeout(REMINDER_PERIOD, self.show_reminder)

    def endgame(self):
        self.leds_off()
        self.dim_buttons()
        hgt.time.add_timeout(2.0, self.endgame2)

    def endgame2(self):
        self.ping_sound.play()
        self.large_text.string = ["%s: %d" % (_("Final Score"), len(self.sequence) - 1)]
        hgt.time.add_timeout(2.0, self.endgame3)

    def endgame3(self):
        self.ping_sound.play()

        l = len(self.sequence)
        if l <= 2:
            s = _("Please try again!")
            sc = 0.0
        elif l <= 3:
            s = _("You won the small trophy!")
            sc = 0.3
        elif l <= 5:
            s = _("You won the medium trophy!")
            sc = 0.5
        elif l <= 7:
            s = _("You won the large trophy!")
            sc = 0.7
        elif l <= 9:
            s = _("You won the huge trophy!")
            sc = 0.9
        elif l <= 11:
            s = _("You won the gigantic trophy!")
            sc = 0.9
        else:
            s = _("You won the gargantuan trophy!")
            sc = 1.0

        self.medium_text.string = [s]
        self.cup_transform.scale = sc * Vec3f(1, 1, 1)

        hgt.time.add_timeout(2.0, self.endgame4)

    def endgame4(self):
        if len(self.sequence) <= 2:
            hgt.time.add_timeout(1.0, self.endgame5)
        else:
            self.fanfare_sound.play()
            self.cup_dynamic_transform.angularMomentum = Vec3f(0, 0, 0.5)
            self.cup_toggle.hapticsOn = True
            self.cup_toggle.graphicsOn = True
            hgt.time.add_timeout(5.0, self.endgame5)

    def endgame5(self):
        self.log_score(
            level = self.level,
            score = len(self.sequence) - 1, # note: sequence is one item longer than successful attempts
            duration = hgt.time.now - self.start_time,
        )
        self.quit()

    # Interaction
    def play_button_sound(self, b):
        l = self.get_button_world_position(b)
        b["sound"].play(location = l)

    def get_button_world_position(self, b):
        m = b["transformInfo"].accForwardMatrix
        p = m * b["transform"].translation
        return p

    def press_button(self, evt):
        if self.player_input_enabled:

            self.clear_reminder()
            if self.reminder_timeout is not None:
                hgt.time.clear_timeout(self.reminder_timeout)

            b = evt.button
            self.glow_on(b)
            correct_button = self.tmp_repeat_sequence.pop(0)

            if b == correct_button:
                self.play_button_sound(b)

                # End of current sequence
                if len(self.tmp_repeat_sequence) == 0:
                    #self.sequence_length_text.string = [str(len(self.sequence))]
                    self.waiting_for_release = True
                    self.player_input_enabled = False

                # Still buttons to press in sequence
                else:
                    self.reminder_timeout = hgt.time.add_timeout(REMINDER_PERIOD, self.show_reminder)

            # Wrong button pressed
            else:
                self.error_sound.play()
                self.player_input_enabled = False
                hgt.time.add_timeout(2.0, self.endgame)

        # Input is disabled
        else:
            self.click_sound.play()

    def release_button(self, evt):
        self.reset_materials()

        if self.waiting_for_release:
            self.waiting_for_release = False
            self.reset_materials()
            hgt.time.add_timeout(1.0, self.play_sequence)

    # Visuals
    def reset_materials(self):
        for b in self.buttons:
            self.glow_off(b)

    def glow_on(self, button):
        button["material"].emissiveColor = RGB(0.5, 0.5, 0.5)
        self.button_glow_lamp.intensity = 0.25
        self.button_glow_lamp.color = button["material"].diffuseColor

        # FIXME: not really the correct position of the lamp
        self.button_glow_lamp.position = self.get_button_world_position(button)

    def glow_off(self, button):
        button["material"].emissiveColor = RGB(0, 0, 0)
        self.button_glow_lamp.intensity = 0.0

    def leds_off(self):
        for l in self.led_materials:
            l.diffuseColor = RGB(0, 0.1, 0)
            l.specularColor = RGB(0, 0.1, 0)

    def led_on(self, i):
        self.leds_off()
        self.led_materials[i - 1].diffuseColor = RGB(0, 1, 0)
        #self.switch_sound.play()

    def dim_buttons(self):
        for b in self.buttons:
            b["material"].diffuseColor = RGB(0, 0, 0)
            b["material"].emissiveColor = RGB(0, 0, 0)

    def show_reminder(self):
        self.fairy_sound.play()
        self.medium_text.string = [_("There are more tones to play...")]
        # FIXME: multiple callbacks might still be created
        self.reminder_timeout = None

    def clear_reminder(self):
        self.medium_text.string = []

    # Build
    def build_world(self):
        # Labels
        # FIXME: blender exporter bug requires fixing before the label names can
        # be changed to something more appropriate.
        space.nodes["Text_LengthLabel.001"].string = [_("Listen")]
        space.nodes["Text_LengthLabel.002"].string = [_("Repeat")]

        # Hide all buttons
        for i in range(TOTAL_NUMBER_OF_BUTTONS):
            t = space.nodes["ToggleGroup_Button.%03d" % (i + 1)]
            t.hapticsOn = False
            t.graphicsOn = False

        self.buttons = []
        for id in self.level_button_ids:
            # Make button visible again
            t = space.nodes["ToggleGroup_Button.%03d" % (id)]
            t.hapticsOn = True
            t.graphicsOn = True

            button = {
                "mesh": space.nodes["Mesh_Button.%03d" % (id)],
                "transformInfo": space.nodes["TransformInfo_Button.%03d" % (id)],
                "transform": space.nodes["Transform_Button.%03d" % (id)],
                "material": space.nodes["Material_Button.%03d" % (id)],
                "sound": Sound(
                        url = "sounds/instrument/%s.wav" % self.level_sounds.pop(0),
                        copies = 3,
                        intensity = 0.5
                    ),
            }
            self.buttons.append(button)

            e = Event()
            e.button = button

            pushButton = PushButton(
                transformNode = button["transform"].h3dNode,
                geometry = button["mesh"].h3dNode,
                onPress = self.press_button,
                onRelease = self.release_button,
                displacement = Vec3f(0, 0.01, 0),
                hitForce = 1.5,
                event = e,
            )

        # The reward
        self.cup_toggle = space.nodes["ToggleGroup_Cup"]
        self.cup_transform = space.nodes["Transform_Cup"]
        self.cup_dynamic_transform = space.nodes["DynamicTransform_Cup"]
        #self.cup_dynamic_transform.angularMomentum = Vec3f(0, 0, 0.5)
        self.cup_toggle.graphicsOn = False
        self.cup_toggle.hapticsOn = False

        # Build sounds
        self.click_sound = Sound(url = "sounds/click.wav", copies = 2, intensity = 0.2)
        self.switch_sound = Sound(url = "sounds/switch.wav", copies = 2, intensity = 0.2)
        self.error_sound = Sound(url = "sounds/error.wav", copies = 2, intensity = 0.2)
        self.fanfare_sound = Sound(url = "sounds/fanfare.wav", copies = 2, intensity = 0.2)
        self.ping_sound = Sound(url = "sounds/ping.wav", copies = 2, intensity = 0.2)
        self.fairy_sound = Sound(url = "sounds/fairy.wav", copies = 2, intensity = 0.2)

        # Lights
        self.button_glow_lamp = space.nodes["PointLight_ButtonGlow"]

        # Texts
        self.sequence_length_text = space.nodes["Text_LengthLabel"]
        self.sequence_length_text.string = []
        self.large_text = space.nodes["Text_LargeLabel"]
        self.large_text.string = []
        self.medium_text = space.nodes["Text_MediumLabel"]
        self.medium_text.string = []

        # Leds
        self.led_materials = []
        for i in range(2):
            m = space.nodes["Material_LED%d" % (i + 1)]
            self.led_materials.append(m)
        self.leds_off()
