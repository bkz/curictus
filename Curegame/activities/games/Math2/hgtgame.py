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
from hgt.gameelements import Sound
from hgt.locale import translate as _
from hgt.listeners import MFBoolListener
from hgt.nodes import hgn
from hgt.widgets.pushbutton import PushButton
import hgt.game
import math
import random
import space

from H3DUtils import *

SPACE_TILT = 90.0

SHORT_TIMEOUT = 0.5
MEDIUM_TIMEOUT = 1.0
END_TIMEOUT = 4.0
###########################################################################
# Math2
###########################################################################

class Game(hgt.game.Game):
    def build(self):
        random.seed()
        hgt.world.tilt(-SPACE_TILT)

        cfg = self.load_config()
        self.level = cfg.settings["math2_level"]

        self.number_of_problems = 10
        self.number_of_answers = 4
        self.writing_pause = 0.2
        self.score_increment = 100
        self.max_bonus = 100
        self.bonus_time = 2.0
        self.mistake_penalty = 50

        if self.level == 1:
            self.problem_generators = [
                self.easy_addition_problem,
            ]
        elif self.level == 2:
            self.problem_generators = [
                self.medium_addition_problem,
                self.easy_subtraction_problem,
            ]
        elif self.level == 3:
            self.problem_generators = [
                self.medium_addition_problem,
                self.hard_subtraction_problem,
                self.easy_multiplication_problem,
            ]

        # Setup hgt world
        hgt.world.stereoInfo.focalDistance = 0.5
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        self.build_world()
        self.build_sounds()

    def start(self):
        self.start_time = hgt.time.now
        self.reset()

    def reset(self):
        # Clear labels
        space.nodes["Text_Hint"].string = [_("Touch correct answer!")]
        space.nodes["Text_Solution"].string = []
        space.nodes["Text_ProblemLine1"].string = []
        space.nodes["Text_ProblemLine2"].string = []
        space.nodes["Text_ProblemNumberLabel"].string = [_("Problem") + ':']
        space.nodes["Text_ProblemNumber"].string = ["1 / %d" % self.number_of_problems]
        space.nodes["Text_Score"].string = ["0"]
        space.nodes["Text_ScoreLabel"].string = [_("Score") + ':']
        space.nodes["Text_EndLabel"].string = [""]
        for i in range(self.number_of_answers):
            space.nodes["Text_Answer%d" % i].string = []

        # Reset stats
        self.score = 0
        self.problem_number = 0
        self.mistakes = 0
        self.current_mistakes = 0
        self.perfect_answers = 0
        self.streak = 0
        self.answering_enabled = False
        hgt.time.add_timeout(MEDIUM_TIMEOUT, self.create_problem)

        if self.level == 3:
            self.music_sound.play()
        self.game_ending = False

    def update(self):
        if self.game_ending:
            # FIXME: Crappy music fader.
            intensity = self.music_sound.sounds[0].intensity
            self.music_sound.sounds[0].intensity = intensity * 0.97

    # Math problems
    # TODO: even more difficult problems
    # TODO: adaptable?
    def easy_addition_problem(self):
        a = random.randint(1, 20)
        b = random.randint(1, 10)
        self.problem_line1 = str(a)
        self.problem_line2 = "+ %d" % b
        c = a + b
        # Generate solutions differing by 2
        self.generate_solutions(c, range(c - 2 * 3, c + 2 * 4, 2))

    def medium_addition_problem(self):
        a = random.randint(1, 50)
        b = random.randint(10, 50)
        self.problem_line1 = str(a)
        self.problem_line2 = "+ %d" % b
        c = a + b
        # Generate solutions differing by 10
        self.generate_solutions(c, range(c - 30, c + 40, 10))

    def easy_subtraction_problem(self):
        a = random.randint(10, 20)
        b = random.randint(1, 10)
        self.problem_line1 = str(a)
        self.problem_line2 = "- %d" % b
        c = a - b
        # Generate solutions differing by 2
        self.generate_solutions(c, range(c - 2 * 3, c + 2 * 4, 2))

    def hard_subtraction_problem(self):
        a = random.randint(10, 99)
        b = random.randint(10, 30)
        # Swap values to avoid negative results
        if a < b:
            a, b = b, a
        self.problem_line1 = str(a)
        self.problem_line2 = "- %d" % b
        c = a - b
        # Generate solutions differing by 10
        self.generate_solutions(c, range(c - 30, c + 40, 10))

    def easy_multiplication_problem(self):
        a = random.randint(1, 12)
        b = random.randint(2, 12)
        self.problem_line1 = str(a)
        self.problem_line2 = "X %d" % b
        c = a * b
        # Generate solutions differing by 2
        self.generate_solutions(c, range(c - 2 * 3, c + 2 * 4, 2))

    # Unused easter egg problem
    def pulp_fiction_problem(self):
        a = 25
        b = 17
        self.problem_line1 = str(a)
        self.problem_line2 = "- %d" % b
        c = a - b
        self.generate_solutions(c, [42, 25, 17, 8])

    def test_problem(self):
        a = 0
        b = 0
        self.problem_line1 = str(a)
        self.problem_line2 = "- %d" % b
        c = a - b
        self.generate_solutions(c, range(c - 2 * 3, c + 2 * 4, 2))

    def generate_solutions(self, solution, candidates):
        self.problem_solution = solution

        ss = [d for d in candidates if d >= 0]
        random.shuffle(ss)
        self.problem_solutions = ss[:self.number_of_answers]

        if solution not in self.problem_solutions:
            self.problem_solutions[0] = solution

        random.shuffle(self.problem_solutions)

    # Game sequence
    def create_problem(self):
        self.problem_number += 1
        space.nodes["Text_ProblemNumber"].string = ["%d / %d" % (self.problem_number, self.number_of_problems)]

        generate_problem = random.choice(self.problem_generators)
        generate_problem()

        for i, s in zip(range(len(self.problem_solutions)), self.problem_solutions):
            ap = self.answer_pads[i]
            ap['answer'] = s
            ap['answered'] = False
            ap['material'].diffuseColor = RGB(1, 1, 1)

        self.write_problem(0)

    def write_problem(self, i):
        random.choice(self.chalktap_sounds).play()
        if i == 0:
            space.nodes["Text_ProblemLine1"].string = [self.problem_line1]
            hgt.time.add_timeout(SHORT_TIMEOUT, self.write_problem, (1,))
        else:
            space.nodes["Text_ProblemLine2"].string = [self.problem_line2]
            hgt.time.add_timeout(SHORT_TIMEOUT, self.write_answers, (0,))

    def write_answers(self, i):
        if i < self.number_of_answers:
            ap = self.answer_pads[i]
            random.choice(self.chalktap_sounds).play()
            space.nodes["Text_Answer%d" % i].string = ["%s %d" % (ap['prefix'], ap['answer'])]
            hgt.time.add_timeout(self.writing_pause, self.write_answers, (i + 1,))
        else:
            self.answer_time = hgt.time.now
            self.answering_enabled = True

    def write_answer(self):
        self.bell_sound.play()

        #score_inc = 100 - (self.current_mistakes * 25)
        #self.score += score_inc
        score = self.score_increment
        time_delta = hgt.time.now - self.answer_time
        if time_delta < self.bonus_time:
            bonus_factor = 1.0 - (time_delta / self.bonus_time)
            bonus = int(bonus_factor * self.max_bonus)
            score += bonus
        self.score += score

        if self.current_mistakes == 0:
            self.perfect_answers += 1

        space.nodes["Text_FeedbackLabel"].string = ["+%d" % score]
        self.feedback_fader.startTime = hgt.time.now

        space.nodes["Text_Score"].string = [str(self.score)]
        self.current_mistakes = 0

        self.solution_string = str(self.problem_solution)
        space.nodes["Text_Solution"].string = [self.solution_string]

        hgt.time.add_timeout(SHORT_TIMEOUT, self.erase_answers, (0,))

    def erase_answers(self, i):
        if i < self.number_of_answers:
            random.choice(self.eraser_sounds).play()
            space.nodes["Text_Answer%d" % i].string = []
            hgt.time.add_timeout(self.writing_pause, self.erase_answers, (i + 1,))
        else:
            hgt.time.add_timeout(MEDIUM_TIMEOUT, self.erase_problem, (0,))

    def erase_problem(self, i):
        random.choice(self.eraser_sounds).play()
        if i == 0:
            space.nodes["Text_Solution"].string = []
            hgt.time.add_timeout(self.writing_pause, self.erase_problem, (1,))
        elif i == 1:
            space.nodes["Text_ProblemLine2"].string = []
            hgt.time.add_timeout(self.writing_pause, self.erase_problem, (2,))
        else:
            space.nodes["Text_ProblemLine1"].string = []
            if self.problem_number < self.number_of_problems:
                hgt.time.add_timeout(MEDIUM_TIMEOUT, self.create_problem)
            else:
                hgt.time.add_timeout(MEDIUM_TIMEOUT, self.finished)

    def finished(self):
        self.game_ending = True

        if self.perfect_answers == 10:
            space.nodes["Text_EndLabel"].string = [_("Flawless!")]
        elif self.perfect_answers == 9:
            space.nodes["Text_EndLabel"].string = [_("Excellent!")]
        elif self.perfect_answers > 6:
            space.nodes["Text_EndLabel"].string = [_("Good job!")]
        elif self.perfect_answers > 4:
            space.nodes["Text_EndLabel"].string = [_("Well done!")]
        else:
            space.nodes["Text_EndLabel"].string = [_("Keep working!")]

        hgt.time.add_timeout(END_TIMEOUT, self.finished2)

    def finished2(self):
        self.log_score(
            level = self.level,
            score = self.score,
            duration = hgt.time.now - self.start_time,
        )
        self.quit()

    # Interaction
    def press_answer_pad(self, evt):
        ap = evt.info

        #self.play_chalk_sound()

        if self.answering_enabled and not ap['answered']:
            if ap['answer'] == self.problem_solution:
                self.answering_enabled = False
                ap['material'].diffuseColor = RGB(0, 1, 0)
                self.streak += 1
                if self.streak > 2:
                    space.nodes["Text_Hint"].string = ["%d %s" % (self.streak, _("in a row!"))]

                # Set feedback position
                space.nodes["Transform_FeedbackLabel"].translation = ap['feedback_pos']

                self.write_answer()
            else:
                ap['material'].diffuseColor = RGB(1, 0, 0)
                self.mistakes += 1
                self.current_mistakes += 1
                self.streak = 0
                ap['answered'] = True
                space.nodes["Text_Hint"].string = [_("Touch correct answer!")]

                # Negative score feedback
                random.choice(self.chalktap_sounds).play()
                penalty = self.mistake_penalty
                space.nodes["Transform_FeedbackLabel"].translation = ap['feedback_pos']
                space.nodes["Text_FeedbackLabel"].string = ["-%d" % penalty]
                self.feedback_fader.startTime = hgt.time.now
                self.score -= penalty
                if self.score < 0:
                    self.score = 0
                space.nodes["Text_Score"].string = [str(self.score)]

    def touch_chalkboard(self):
        pass
        #self.play_chalk_sound()

    def play_chalk_sound(self):
        random.choice(self.chalktap_sounds).play()

    # Build
    def build_world(self):
        # Invisible answer buttons
        self.answer_pads = []
        for i in range(self.number_of_answers):
            prefix = "%s." % ['a', 'b', 'c', 'd'][i]
            space.nodes["ToggleGroup_AnswerPad%d" % i].graphicsOn = False
            material = space.nodes["Material_Answer%d" % i]
            info = {
                'id': i,
                'answer': None,
                'answered': False,
                'material': material,
                'prefix': '', #prefix,
                'feedback_pos': space.nodes["Transform_AnswerPad%d" % i].translation + Vec3f(0, -0.02, 0.02)
            }
            self.answer_pads.append(info)

            e = Event()
            e.info = info

            pushButton = PushButton(
                transformNode = space.nodes["Transform_AnswerPad%d" % i].h3dNode,
                geometry = space.nodes["Mesh_AnswerPad%d" % i].h3dNode,
                displacement = Vec3f(0, 0, 0),
                event = e,
                onPress = self.press_answer_pad,
            )

        # Chalk tap sounds when touching blackboard
        bl = MFBoolListener(
            onTrue=self.touch_chalkboard,
        )
        space.nodes["Mesh_Chalkboard"].h3dNode.isTouched.routeNoEvent(bl)

        self.build_feedback_label()

    def build_feedback_label(self):
        # "Hide" feedback label
        space.nodes["Text_FeedbackLabel"].string = [""]

        # Build fading interpolator
        self.feedback_fader = ts = hgn.TimeSensor(
            cycleInterval = 2.0,
            loop = False
        )

        si = hgn.ScalarInterpolator(
            key = [0, 0.1, 1],
            keyValue = [1, 0, 1],
        )

        pi = hgn.PositionInterpolator(
            key = [0, 1],
            keyValue = [
                Vec3f(1, 1, 1),
                Vec3f(1, 1, 1) * 1.5,
            ],
        )

        self.add_child(ts)
        self.add_child(si)
        self.add_child(pi)

        ts.h3dNode.fraction_changed.route(
            si.h3dNode.set_fraction
        )
        si.h3dNode.value_changed.routeNoEvent(
            space.nodes["Material_YellowChalky"].h3dNode.transparency
        )

        ts.h3dNode.fraction_changed.route(
            pi.h3dNode.set_fraction
        )
        pi.h3dNode.value_changed.routeNoEvent(
            space.nodes["Transform_FeedbackLabel"].h3dNode.scale
        )

    def build_sounds(self):
        self.bell_sound = Sound("sounds/bell.wav", intensity=0.3, copies=2)
        self.chalktap_sounds = [
            Sound("sounds/chalktap1.wav", intensity=1.0, copies=2),
            Sound("sounds/chalktap2.wav", intensity=1.0, copies=2),
        ]
        self.eraser_sounds = [
            Sound("sounds/eraser1.wav", intensity=0.5, copies=2),
            Sound("sounds/eraser2.wav", intensity=0.5, copies=2),
            Sound("sounds/eraser3.wav", intensity=0.5, copies=2),
        ]
        self.music_sound = Sound("sounds/music.ogg", intensity=0.3, loop=True)
