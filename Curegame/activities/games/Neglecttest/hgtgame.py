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
from hgt.gamemath import DEG2RAD
from hgt.locale import translate as _
from hgt.widgets.pushbutton import PushButton

import math
import random
import space # space.py generated by Blender exporter

from H3DUtils import *

# The distance in meters that targets move in the z direction when pressed
TARGET_PRESS_Z_DISPLACEMENT = -0.004

###########################################################################
# Neglect assessment.
#
# Default Viewpoint, no transforms applied to world. The camera looks
# down in the negative z direction towards the x-y plane.
#
# Development version:
#   * pressed targets/distractors go black
#   * Press done button to end assessment
#   * Result logging not finisihed
#
# Created while listening to:
#   * Mamma Mia! - Various Artists
#   * Born to Run - Bruce Springsteen
#   * Fallout 3 - Various Artists
###########################################################################

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        cfg = self.load_config()

        # Tweak hgt world
        hgt.world.stereoInfo.focalDistance = 0.5
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        self.total_number_of_targets = 0
        self.total_number_of_distractors = 0
        self.assessment_running = False

        self.target_infos = []

        self.build_sounds()
        self.build_world()

        # Log target positions
        for ti in self.target_infos:
            t_id = ti['target_id']
            pos = ti['original_position']
            self.log_info(
                "target_position",
                "Target %d position" % t_id,
                id = t_id,
                x = pos.x,
                y = pos.y,
                z = pos.z,
            )

    # Initialization
    def start(self):
        self.start_time = hgt.time.now
        self.reset()

    def reset(self):
        self.any_target_or_distractor_pressed = False
        self.first_target_press_time = None
        self.target_represses = 0
        self.unique_target_presses = 0
        self.target_x_values = []
        self.target_y_values = []
        self.center_of_cancellation = 0.0

        # Scores for Dashboard (unique left target presses / unique right target presses)
        self.left_score = 0
        self.right_score = 0
        self.middle_score = 0

        # Display user instructions
        space.nodes["Text_Message"].string = [
            _("Press all green circles marked '1'."),
            _("Press a red '0' when you are finished."),
        ]

        # Enable target presses
        self.assessment_running = True

    # End of assessment
    def end_assessment(self):
        assert(len(self.target_x_values) == self.unique_target_presses)
        assert(len(self.target_y_values) == self.unique_target_presses)

        # Analytics reporting
        left_right_score = self.left_score + self.right_score
        if left_right_score > 0:
            laterality_index = self.left_score / float(left_right_score)

            self.log_info("assessment_vars", "Assessment variables",
                middle_targets_pressed=self.middle_score,
                target_represses=self.target_represses,
                laterality_index=laterality_index,
            )
        else:
            self.log_info("assessment_vars", "Assessment variables",
                middle_targets_pressed=self.middle_score,
                target_represses=self.target_represses,
            )

        # Report left/right score for Dashboard
        self.log_score(
            duration = hgt.time.now - self.start_time, # note: duration since self.start()
            left_score = self.left_score,
            right_score = self.right_score,
        )

        self.quit()

    """
    def calculate_scores(self):
        if self.unique_target_presses > 0:
            self.calculate_correlations()
            self.calculate_coc()

    def calculate_correlations(self):
        pass

    def calculate_coc(self):
            # http://www.cabiatl.com/CABI/resources/cancel/

            # 1. Find mean x of pressed targets
            avg = sum(self.target_x_values) / float(self.unique_target_presses)

            # 2. Baseline correction of all targets
            all_targets_x_values = [ti['original_position'].x for ti in self.target_infos]
            all_targets_avg_x = sum(all_targets_x_values) / float(len(self.target_infos))
            all_targets_translated = [x - all_targets_avg_x for x in all_targets_x_values]

            # Mean of translated targets should now be 0.0
            #all_targets_translated_avg_x = sum(all_targets_translated) / float(len(self.target_infos))
            #print all_targets_translated_avg_x

            # 3. Find scale for x axis s.t. distance between leftmost/rightmost targets
            # is 2.
            dx = max(all_targets_translated) - min(all_targets_translated)
            scaling_factor = 2.0 / dx

            # 4. CoC
            self.center_of_cancellation = avg * scaling_factor
    """

    # Interactivity
    def press_target(self, evt):
        # If we're done, do nothing when a target is pressed
        if not self.assessment_running:
            return

        # Else we're clicking a target or distractor
        self.any_target_or_distractor_pressed = True
        self.click_sound.play()
        ti = evt.targetInfo

        # Update target/distractor press count
        ti['press_count'] += 1

        # Change color of target
        ti['appearance'].material = space.nodes["Material_Pressed"].h3dNode

        self.log_event("target_or_distractor_press", "Pressed target/distractor %d" % ti['target_id'], id = ti['target_id'])

        # Target press
        if ti['type'] == 'target':

            # This happens only once per target
            if ti['press_count'] == 1:
                self.log_event("target_press", "Pressed target %d" % ti['target_id'], id = ti['target_id'])

                self.unique_target_presses += 1
                self.target_x_values.append(ti['original_position'].x)
                self.target_y_values.append(ti['original_position'].y)

                # Update left/right scores
                if ti['side'] == 'left':
                    self.left_score += 1
                elif ti['side'] == 'right':
                    self.right_score += 1
                else:
                    self.middle_score += 1

            # Subsequent target presses
            elif ti['press_count'] > 1:
                self.target_represses += 1
                self.log_event("target_press_repeated", "Pressed correct target repeated %d" % ti['target_id'], id = ti['target_id'])

        # Distractor press
        if ti['type'] == 'distractor':

            # This happens only once per distractor
            if ti['press_count'] == 1:
                self.log_event("distractor_press", "Pressed distractor %d" % ti['target_id'], id = ti['target_id'])
            # Subsequent distractor presses
            else:
                self.log_event("distractor_press_repeated", "Pressed distractor repeated %d" % ti['target_id'], id = ti['target_id'])

    def press_done(self, evt):
        self.log_event("exit_press", "Pressed exit button")

        space.nodes["Text_Message"].string = [_("Thanks!")]
        self.assessment_running = False
        hgt.time.add_timeout(2, self.end_assessment)

    # Build
    def build_world(self):
        # Scan sidecar file for targets and distractors
        for object_name in space.hgt_object_names:
            if object_name.startswith('TargetEmpty'):
                # Create pushButton for target
                self.build_target(object_name)

        # Exit buttons
        pushButton = PushButton(
            transformNode = space.nodes["Transform_ExitButton"].h3dNode,
            geometry = space.nodes["Mesh_ExitButton"].h3dNode,
            displacement = Vec3f(0, 0, TARGET_PRESS_Z_DISPLACEMENT), # push down 5 mm in negative z dir
            onRelease = self.press_done,
            hitForce = 1.0,
            pressSound = self.click_sound,
        )

        pushButton = PushButton(
            transformNode = space.nodes["Transform_ExitButton2"].h3dNode,
            geometry = space.nodes["Mesh_ExitButton2"].h3dNode,
            displacement = Vec3f(0, 0, TARGET_PRESS_Z_DISPLACEMENT), # push down 5 mm in negative z dir
            onRelease = self.press_done,
            hitForce = 1.0,
            pressSound = self.click_sound,
        )

    def build_target(self, name):
        target_id = name[-3:] # last three characters in name, "000"

        transform = space.nodes["Transform_%s" % name]
        mesh = space.nodes["Mesh_TargetMesh.%s" % target_id]
        appearance = space.nodes["Appearance_Cylinder.%s" % target_id]
        label = space.nodes["Text_TargetLabel.%s" % target_id]

        #material = space.nodes["Material_%s" % name]

        if label.string == ['1']:
            self.total_number_of_targets += 1
            targetType = 'target'
        else:
            self.total_number_of_distractors += 1
            targetType = 'distractor'

        if transform.translation.x > 0.0:
            side = 'right'
        elif transform.translation.x < 0.0:
            side = 'left'
        else:
            side = 'middle'

        original_position = Vec3f(
            transform.translation.x,
            transform.translation.y,
            transform.translation.z
        )

        e = Event()
        e.targetInfo = {
            'type': targetType, # target or distractor
            'appearance': appearance,
            #'material': material,
            'press_count': 0,
            'side': side,
            'original_position': original_position,
            'target_id': int(target_id),
        }
        if targetType == 'target':
            self.target_infos.append(e.targetInfo)

        pushButton = PushButton(
            transformNode = transform.h3dNode,
            geometry = mesh.h3dNode,
            displacement = Vec3f(0, 0, TARGET_PRESS_Z_DISPLACEMENT),
            event = e,
            onPress = self.press_target,
            hitForce = 1.0,
       )

    def build_sounds(self):
        self.click_sound = Sound("../../../media/sounds/click.wav", copies = 3, intensity = 0.3)
