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
from hgt.gameutils import Enum, StateManager
from hgt.listeners import MFBoolListener
from hgt.locale import translate as _
from hgt.nodes import X3DFileNode, hgn
from hgt.utils import unique
from hgt.widgets.grabber import Grabber

from feedbacklabel import FeedbackLabel

import math
import random
import space # space.py generated by Blender exporter

from H3DUtils import *

SPACE_TILT = 0.0 # Looking down at the xy plane

###########################################################################
# Bingo2 Game (Replaces Bingo).
###########################################################################

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        self._saved_references = []

        cfg = self.load_config()
        self.level = cfg.settings["bingo2_level"]

        # Levels and game variables
        if self.level == 1:
            self.square_size = 3
            self.min_number = 1
            self.max_number = 9
            self.bonus_time = 4.0

        elif self.level == 2:
            self.square_size = 4
            self.min_number = 1
            self.max_number = 16
            self.bonus_time = 3.5

        elif self.level == 3:
            self.square_size = 5
            self.min_number = 1
            self.max_number = 99
            self.bonus_time = 3.0

        self.score_increment = 100
        self.max_bonus = 100

        self.button_spacing = 0.05
        self.grid_scale = 0.2 / (self.square_size * self.button_spacing)
        self.number_of_buttons = self.square_size ** 2

        numbers = range(self.min_number, self.max_number + 1)
        random.shuffle(numbers)
        self.sequence = numbers[:self.number_of_buttons]

        self.check_sanity()

        # hgt world
        hgt.world.stereoInfo.focalDistance = 0.5
        hgt.world.tilt(-SPACE_TILT)
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        # Build
        self.build_sounds()
        self.build_world()

        # States
        self.states = Enum('beginning', 'waiting', 'interacting', 'ending')
        self.state = StateManager(self.states, self.states.beginning)
        self.state.add(self.states.beginning, self.states.waiting)
        self.state.add(self.states.waiting, self.states.interacting)
        self.state.add(self.states.interacting, self.states.waiting)
        self.state.add(self.states.interacting, self.states.ending)

    def check_sanity(self):
        """ Let's be anal this time. """
        assert(self.level in [1, 2, 3])
        assert(self.min_number < self.max_number)
        assert((self.max_number - self.min_number) >= self.number_of_buttons - 1)
        assert(len(self.sequence) == self.number_of_buttons)
        assert(unique(self.sequence) == self.sequence)

    def save_ref(self, r):
        """ Save reference to object to a global list to avoid H3D crash. """
        self._saved_references.append(r)

    def end_game(self):
        self.update_board()
        hgt.time.add_timeout(3.0, self.end_game2)

    def end_game2(self):
        self.log_score(
            level = self.level,
            score = self.score,
            duration = hgt.time.now - self.start_time,
        )
        self.quit()

    # Update
    def update(self):
        # FIXME: Crappy music fader.
        if self.state == self.states.ending:
            intensity = self.music_sound.sounds[0].intensity
            self.music_sound.sounds[0].intensity = intensity * 0.97

    # Initialization
    def start(self):
        self.start_time = hgt.time.now
        self.reset()

    def reset(self):
        space.nodes["Text_LevelLabel"].string = [_('LEVEL')]
        space.nodes["Text_ScoreLabel"].string = [_('SCORE')]
        space.nodes["Text_Level"].string = [[_('Easy'), _('Medium'), _('Hard')][self.level - 1]]

        self.sequence_index = 0
        self.score = 0
        self.current_number = 0
        self.sequence_index = -1

        if self.level == 3:
            self.music_sound.play()

        random.shuffle(self.sequence)

        self.new_round()

    # Game sequence
    def new_round(self):
        self.sequence_index += 1
        self.update_labels()

        space.nodes["ToggleGroup_CurrentNumberLabel"].graphicsOn = False
        space.nodes["Text_CurrentNumber"].string = []
        space.nodes["Text_CurrentNumberLabel"].string = [_('FIND:')]

        # End game
        if self.sequence_index == self.number_of_buttons: # note: sequence_index updated above
            self.state.change(self.states.ending)
            hgt.time.add_timeout(1.0, self.end_game)

        # Continue game
        else:
            self.state.change(self.states.waiting)
            hgt.time.add_timeout(1.0, self.clean_board)

    def clean_board(self):
        self.update_board()
        hgt.time.add_timeout(1.0, self.draw_number)

    def update_board(self):
        for bi in self.button_infos:
            if not bi['found']:
                bi['pressed'] = False
                bi['appearance'].material = self.button_material.h3dNode

        # FIXME: a very complicated and inelegant way to check for Bingo.
        # Rows and columns
        bingo_buttons = []
        tmp_cols = []
        for col in range(self.square_size):
            tmp_cols.append([])

        for col in range(self.square_size):
            tmp_row = []
            for row in range(self.square_size):
                index = col * self.square_size + row
                bi = self.button_infos[index]
                tmp_row.append(bi)
                tmp_cols[row].append(bi)

            if all([bi['found'] for bi in tmp_row]):
                bingo_buttons.extend(tmp_row)

        for col in tmp_cols:
            if all([bi['found'] for bi in col]):
                bingo_buttons.extend(col)

        # Diagonals
        ds = [[],[]]
        for bi in self.button_infos:
            if bi['col'] == bi['row']:
                ds[0].append(bi)
            if bi['col'] + bi['row'] == self.square_size - 1:
                ds[1].append(bi)

        for d in ds:
            if all([bi['found'] for bi in d]):
                bingo_buttons.extend(d)

        if len(bingo_buttons) > 0:
            self.mark_as_bingoed(bingo_buttons)
            #self.ping_sound.play()

    def mark_as_bingoed(self, bis):
        new_bingo = False
        for bi in bis:
            if not bi['bingoed']:
                new_bingo = True
            bi['appearance'].material = self.bingo_button_material.h3dNode
            bi['bingoed'] = True

        if new_bingo:
           self.bongo_sound.play()

    def draw_number(self):
        self.current_number = self.sequence[self.sequence_index]
        space.nodes["Text_CurrentNumber"].string = [str(self.current_number)]
        space.nodes["ToggleGroup_CurrentNumberLabel"].graphicsOn = True
        self.switch_sound.play()
        self.draw_time = hgt.time.now
        self.state.change(self.states.interacting)

    # Visuals
    def update_labels(self):
        space.nodes["Text_Score"].string = [str(self.score)]
        #space.nodes["Text_CurrentNumber"].string = [str(self.current_number)]

    # Interactivity
    def touch_button(self, evt):
        bi = evt.info
        if self.state == self.states.interacting:
            if not bi['pressed']:
                bi['pressed'] = True
                if bi['number'] == self.current_number:
                    bi['found'] = True
                    bi['appearance'].material = self.completed_button_material.h3dNode

                    score = self.score_increment
                    time_delta = hgt.time.now - self.draw_time
                    print time_delta
                    if time_delta < self.bonus_time:
                        bonus_factor = 1.0 - (time_delta / self.bonus_time)
                        bonus = int(bonus_factor * self.max_bonus)
                        score += bonus

                    self.feedback_label.show(msg="+%d" % score, pos=hgt.haptics.proxyPosition + Vec3f(0, 0.025, 0.025))
                    self.score += score

                    self.ping_sound.play()
                    self.new_round()
                else:
                    #self.click_sound.play()
                    pass
                    #bi['appearance'].material = self.pressed_button_material.h3dNode

    # Build
    def build_sounds(self):
        self.click_sound = Sound("sounds/click.wav", copies=2, intensity=0.5)
        self.ping_sound = Sound("sounds/ping.wav", copies=2, intensity=0.5)
        self.switch_sound = Sound("sounds/switch.wav", copies=2, intensity=0.5)
        self.bongo_sound = Sound("sounds/bongo.wav", copies=2, intensity=0.5)
        self.music_sound = Sound("sounds/fast_music.ogg", intensity=0.4, loop=True)

    def build_world(self):
        self.feedback_label = FeedbackLabel(
            topnode=self.node,
            text=space.nodes["Text_FeedbackLabel"],
            transform=space.nodes["Transform_FeedbackLabel"],
            material=space.nodes["Material_FeedbackLabel"],
            toggle=space.nodes["ToggleGroup_FeedbackLabel"],
        )

        self.button_infos = []

        self.button_material = space.nodes["Material_BingoButton"]
        self.pressed_button_material = space.nodes["Material_BingoButtonPressed"]
        self.completed_button_material = space.nodes["Material_BingoButtonCompleted"]
        self.bingo_button_material = space.nodes["Material_BingoButtonBingo"]

        space.nodes["Transform_ButtonAnchor"].scale = self.grid_scale * Vec3f(1, 1, 1)

        # Center buttons about x = 0
        c = ((self.square_size - 1) * self.button_spacing) / 2.0
        centering_vector = Vec3f(-c, 0, 0)

        for col in range(self.square_size):
            for row in range(self.square_size):
                index = col * self.square_size + row

                bb = X3DFileNode("bingobutton.hgt")
                space.nodes["Transform_ButtonAnchor"].add_child(bb)

                transform = bb.find("Transform_BingoButtonEmpty")
                mesh = bb.find("Mesh_BingoButtonMesh")
                appearance = bb.find("Appearance_BingoButton")
                appearance.material = self.button_material.h3dNode

                label = bb.find("Text_BingoLabel")

                # Put the button in position and mark it
                transform.translation += Vec3f(col * self.button_spacing, row * self.button_spacing, 0) + centering_vector
                number = self.sequence[index]
                label.string = [str(number)]

                # Button touch listener
                info = {
                    'pressed': False,
                    'found': False,
                    'appearance': appearance,
                    'number': number,
                    'transform': transform,
                    'row': row,
                    'col': col,
                    'index': index,
                    'bingoed': False,
                }
                evt = Event()
                evt.info = info
                self.button_infos.append(info)
                bl = MFBoolListener(
                    onTrue=self.touch_button,
                    callbackObject=evt,
                )
                self.save_ref(bl)
                mesh.h3dNode.isTouched.routeNoEvent(bl)
