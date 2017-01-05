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
from hgt.gameelements import Sound, LineShape
from hgt.listeners import MFBoolListener
from hgt.locale import translate as _
from hgt.nodes import X3DFileNode
from hgt.widgets.pushbutton import PushButton

from H3DUtils import Vec3f, Rotation

import math
import random

import space # space.py generated by Blender exporter
SPACE_TILT = 65.0 # degrees

NUMBER_OF_TARGETS = 9
END_TIMEOUT = 3.0

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        cfg = self.load_config()

        # Setup hgt world
        hgt.world.tilt(-SPACE_TILT)
        hgt.world.stereoInfo.focalDistance = 0.50
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        self.build_world()

        # Log target positions
        for ti in self.target_infos:
            t_id = ti['target_id']
            pos = ti['original_position']

            # Reset tilt correction
            #print pos
            #r = Rotation(1, 0, 0, -SPACE_TILT)
            #pos = r * pos
            #print pos

            self.log_info(
                "target_position",
                "Target %d position" % t_id,
                id = t_id,
                x = pos.x,
                y = pos.y,
                z = pos.z,
            )

    # Start & end
    def start(self):
        self.start_time = hgt.time.now
        self.sequence_index = 0
        space.nodes["Text_Message"].string = [_('Touch the green bubble.'), _('Follow the arrows.')]

    def end_assessment(self):
        self.log_score(
            duration = hgt.time.now - self.start_time,
        )
        self.quit()

    # Interactivity & visuals
    def touch_target(self, evt):
        ti = evt.target_info
        # Correct target
        if ti['target_id'] == self.sequence_index:
            ti['toggle'].graphicsOn = False
            ti['toggle'].hapticsOn = False

            self.pop_sound.play()

            self.log_event("press_target", "Press target %02d" % ti['target_id'], target=ti['target_id'])

            self.sequence_index += 1
            if self.sequence_index == NUMBER_OF_TARGETS:
                space.nodes["Text_Message"].string = [_('Thanks!')]
                hgt.time.add_timeout(END_TIMEOUT, self.end_assessment)
            else:
                self.target_infos[self.sequence_index]['appearance'].material = self.next_target_material.h3dNode
                #self.target_infos[self.sequence_index]['toggle'].graphicsOn = True
                self.target_infos[self.sequence_index]['toggle'].hapticsOn = True

    # Build
    def build_world(self):
        # Labels
        #space.nodes["Text_Message"].string = [_("Touch all targets in order, man.")]

        # Sounds
        self.pop_sound = Sound("sounds/pop.wav", copies=3, intensity=0.5)

        # Gather target materials
        self.default_target_material = space.nodes["Material_DefaultTarget"]
        self.next_target_material = space.nodes["Material_NextTarget"]

        self.target_infos = []

        for i in range(NUMBER_OF_TARGETS):
            target = X3DFileNode("target.hgt")
            self.add_child(target)

            # Position the target according to the corresponding
            # empty in the scene.
            transform = target.find("Transform_TargetEmpty")
            empty_transform = space.nodes["Transform_BubbleEmpty.%03d" % i]
            transform.translation = empty_transform.translation

            appearance = target.find("Appearance_TargetHaptic")
            toggle = target.find("ToggleGroup_TargetHaptic")

            if i == 0:
                appearance.material = self.next_target_material.h3dNode
                #toggle.graphicsOn = True
                toggle.hapticsOn = True
            else:
                appearance.material = self.default_target_material.h3dNode
                #toggle.graphicsOn = False
                toggle.hapticsOn = False


            # Create target info
            target_info = {
                'target_id': i,
                'appearance': appearance,
                'done': False,
                'original_position': transform.translation,
                'toggle': toggle,
            }

            self.target_infos.append(target_info)

            # Bind touch
            evt = Event()
            evt.target_info = target_info

            bl = MFBoolListener(
                onTrue=self.touch_target,
                callbackObject=evt
            )

            target.find("Mesh_TargetHaptic").h3dNode.isTouched.routeNoEvent(bl)


