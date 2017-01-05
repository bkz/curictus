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
from hgt.gamemath import DEG2RAD
from hgt.locale import translate as _
from hgt.listeners import BoolListener, MFBoolListener
from hgt.nodes import hgn
from hgt.widgets.pushbutton import PushButton

import math
import random
import space

from H3DUtils import *

SPACE_TILT = 70.0
RELEASE_DISTANCE = 0.23

MAX_AIMLEN = 0.23
MAX_ARROW_SPEED = 6.0

###########################################################################
# Archery2 FIXME: Very much cut'n'paste between all new games. Refactor.
###########################################################################

class Game(hgt.game.Game):
    def build(self):
        random.seed()
        hgt.world.tilt(-SPACE_TILT)
        self.tilt_matrix = Rotation(1, 0, 0, SPACE_TILT * DEG2RAD)

        cfg = self.load_config()
        self.level = cfg.settings["archery2_level"]

        # Setup hgt world
        hgt.world.stereoInfo.focalDistance = 0.5
        hgt.world.stereoInfo.interocularDistance = 0.005
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        self.build_final_score_grower()
        self.build_world()
        self.build_sounds()
        self.build_feedback_label()
        self.build_arrow_fader()

    def start(self):
        self.start_time = hgt.time.now
        self.reset()

    def reset(self):
        self.music_sound.play()
        self.reset_bow_strings()
        self.aiming = False
        self.firing = False
        self.score = 0
        self.increment_score(0)
        self.arrow_travel_distance = 0.0
        self.arrows_left = 20
        self.update_arrow_counter()
        self.game_is_ending = False
        self.hit_arrow_info = None

        self.target_list = [
            space.nodes["Transform_Target.000"],
            space.nodes["Transform_Target.001"],
            space.nodes["Transform_Target.002"],
        ]

        space.nodes["Text_ScoreLabel"].string = [_("Score")]
        space.nodes["Text_ArrowLabel"].string = [_("Arrows")]
        space.nodes["ToggleGroup_FinalScore"].graphicsOn = False

    def update(self):
        # FIXME: crappy music fader
        if self.game_is_ending:
            intensity = self.music_sound.sounds[0].intensity
            self.music_sound.sounds[0].intensity = intensity * 0.97
        else:
            if self.aiming:
                self.update_bow()
            if self.firing:
                self.update_arrow()

        self.update_guide_arrow()

        if self.level > 1:
            self.update_targets()

    def update_targets(self):
        if self.level == 2:
            speed = 0.5
        elif self.level == 3:
            speed = 1.0

        for (target, i) in zip(self.target_list, range(len(self.target_list))):
            t = target.translation
            offset = i * math.pi * 2 / 3.0
            scale = 0.15
            zfoo = (math.sin((hgt.time.now * speed) + offset)) * scale
            zbar = -0.17217 + zfoo - scale
            target.translation = Vec3f(t.x, t.y, zbar)
            if self.hit_arrow_info is not None:
                if self.hit_arrow_info['target'] == target:
                    to = self.hit_arrow_info['position']
                    if 'firstoffset' not in self.hit_arrow_info:
                        self.hit_arrow_info['firstoffset'] = zbar - to.z
                    fo = self.hit_arrow_info['firstoffset']

                    space.nodes["Transform_FlyingArrow"].translation = Vec3f(to.x, to.y, zbar - fo)

    def update_guide_arrow(self):
        v = Vec3f(0, 0, 0.005 * math.cos(hgt.time.now * 3))
        space.nodes["Transform_GuideArrow"].translation = v

    def update_bow(self):
        pp = space.nodes['Transform_PullPoint']
        mp = space.nodes['Transform_MidPoint']

        self.aimlen = aimlen = (pp.translation - mp.translation).length()
        aimvec = (pp.translation - mp.translation).normalize()

        space.nodes['Transform_Arrow'].translation = Vec3f(0, -aimlen, 0)

        aimrot = Rotation(self.orig_pp_translation.normalize(), aimvec)
        space.nodes['Transform_Aim'].rotation = aimrot

        pp.translation = self.tilt_matrix * hgt.haptics.trackerPosition

        self.set_bow_strings(pp.translation)

    def fire_arrow(self):
        self.hit_arrow_info = None

        self.whizz_sound.play()
        self.spring_effect.startDistance = 0.0
        self.spring_effect.escapeDistance = 0.0
        space.nodes["ToggleGroup_Arrow"].graphicsOn = False
        self.reset_bow_strings()

        self.aiming = False
        self.firing = True

        space.nodes["ToggleGroup_FlyingArrow"].graphicsOn = True
        space.nodes["Transform_FlyingArrow"].translation = space.nodes['Transform_PullPoint'].translation
        aimrot = space.nodes['Transform_Aim'].rotation
        space.nodes["Transform_FlyingArrow"].rotation = aimrot
        self.aim_rotation = aimrot

        self.arrow_travel_distance = 0.0
        self.checked_hit = False

    def update_arrow(self):
        arrow_speed = MAX_ARROW_SPEED * (self.aimlen / MAX_AIMLEN) # m/s
        v = self.aim_rotation * Vec3f(0, arrow_speed * hgt.time.dt, 0)
        space.nodes["Transform_FlyingArrow"].translation += v

        self.arrow_travel_distance += v.length()
        #print self.arrow_travel_distance

        r = Rotation(1, 0, 0, -hgt.time.dt * 0.5) # 0.5 rad/s
        self.aim_rotation = r * self.aim_rotation
        space.nodes["Transform_FlyingArrow"].rotation = self.aim_rotation

        # FIXME BELOW: Stressed, refactor
        # Check hits
        target_plane_y = 2.05
        t = space.nodes["Transform_FlyingArrow"].translation

        if self.arrow_travel_distance > 4.0:
            space.nodes["ToggleGroup_FlyingArrow"].graphicsOn = False
            self.initiate_reload()

        elif t.y > target_plane_y and not self.checked_hit:
            space.nodes["Transform_FlyingArrow"].translation = Vec3f(t.x, target_plane_y, t.z)
            self.checked_hit = True

            for target in self.target_list:
                self.check_target_hit(target)

    def check_target_hit(self, target):
        t = space.nodes["Transform_FlyingArrow"].translation
        t2 = target.translation
        arrow_tip_position = t + Vec3f(0, 0, 0)
        target_center_position = t2 + Vec3f(0, 0, 0)
        target_center_position.y = arrow_tip_position.y
        arrow_target_vector = arrow_tip_position - target_center_position
        arrow_target_vector.y = 0
        arrow_target_distance = arrow_target_vector.length()

        foo = 0.18
        if arrow_target_distance < foo:
            # hit target
            self.impact_sound.play()

            print arrow_target_distance

            score_percentage = (foo - arrow_target_distance) / foo
            score = int(math.floor(5 * score_percentage) * 5) + 5
            score = score * 10

            if score == 50:
                self.squeak_sound.play()
            elif score == 250:
                score = 500
                self.cheers_sound.play()
            self.increment_score(score)
            self.show_feedback("+%d" % score, target.translation + Vec3f(0, -0.1, 0))

            self.hit_arrow_info = {
                "target": target,
                "position": arrow_tip_position,
            }

            self.initiate_reload()

    def initiate_reload(self):
        self.firing = False
        if self.arrows_left > 0:
            space.nodes["ToggleGroup_ReloadArrow"].graphicsOn = True
            space.nodes["ToggleGroup_ReloadArrow"].hapticsOn = True
            space.nodes["ToggleGroup_GuideArrow"].graphicsOn = True
            self.arrow_fader.startTime = hgt.time.now
        else:
            self.game_is_ending = True
            hgt.time.add_timeout(2, self.end_game)

    def set_bow_strings(self, mid):
        tp = space.nodes['Transform_TopPoint']
        bp = space.nodes['Transform_BottomPoint']
        tp_ti = space.nodes['TransformInfo_TopPoint']
        bp_ti = space.nodes['TransformInfo_BottomPoint']
        top = self.tilt_matrix * (tp_ti.accForwardMatrix * tp.translation)
        bottom = self.tilt_matrix * (bp_ti.accForwardMatrix * bp.translation)
        self.top_line.set_points(top, mid)
        self.bottom_line.set_points(mid, bottom)

    def reset_bow_strings(self):
        sp = space.nodes['Transform_StringPoint']
        sp_ti = space.nodes['TransformInfo_StringPoint']
        self.set_bow_strings(
            self.tilt_matrix * (sp_ti.accForwardMatrix * sp.translation)
        )

    def increment_score(self, inc):
        self.score += inc
        space.nodes["Text_Score"].string = [str(self.score)]

    def update_arrow_counter(self):
        space.nodes["Text_ArrowCounter"].string = ["%d" % (self.arrows_left)]

    def end_game(self):
        self.ping_sound.play()
        space.nodes["Text_FinalScore"].string = [_("Score") + ':', str(self.score)]
        space.nodes["ToggleGroup_FinalScore"].graphicsOn = True
        self.final_score_grower.startTime = hgt.time.now
        hgt.time.add_timeout(5.0, self.end_game2)

    def end_game2(self):
        self.log_score(
            level = self.level,
            score = self.score,
            duration = hgt.time.now - self.start_time,
        )
        self.quit()

    # Interactivity
    def touch_reloader(self):
        if not self.game_is_ending:
            if not self.aiming and not self.firing:

                self.aiming = True
                self.firing = False

                self.arrows_left -= 1
                self.update_arrow_counter()

                self.spring_effect.startDistance = 0.2
                self.spring_effect.escapeDistance = 0.5
                space.nodes["ToggleGroup_Arrow"].graphicsOn = True

                space.nodes["ToggleGroup_ReloadArrow"].graphicsOn = False
                space.nodes["ToggleGroup_ReloadArrow"].hapticsOn = False

                space.nodes["Material_GuideArrow"].transparency = 1.0
                space.nodes["ToggleGroup_GuideArrow"].graphicsOn = False

    def press_stylus_button(self):
        if self.spring_effect.active:
            self.fire_arrow()

    def show_feedback(self, msg_str, pos):
        space.nodes["Transform_FeedbackLabel"].translation = pos
        space.nodes["Text_FeedbackLabel"].string = [msg_str]
        self.feedback_fader.startTime = hgt.time.now

    # Build
    def build_world(self):
        # Bow string represented by two straight lines.
        self.top_line = LineShape(width=3)
        self.add_child(self.top_line.node)
        self.bottom_line = LineShape(width=3)
        self.add_child(self.bottom_line.node)

        # Markers and debug stuff
        """
        self.line_marker = LineShape(width=5)
        self.line_marker.material.emissiveColor = RGB(1, 0, 0)
        self.line_marker.material.diffuseColor = RGB(1, 0, 0)
        self.add_child(self.line_marker.node)
        """

        space.nodes["ToggleGroup_Marker1"].graphicsOn = False
        space.nodes["ToggleGroup_Marker2"].graphicsOn = False

        # Save original pullpoint
        self.orig_pp_translation = space.nodes['Transform_PullPoint'].translation

        # Spring effect off when game starts
        self.spring_effect = hgn.SpringEffect(
            startDistance = 0.0,
            escapeDistance = 0.001,
            springConstant = 10,
        )

        space.nodes['Transform_StringPoint'].add_child(self.spring_effect)

        # Sky motion - off
        #space.nodes['DynamicTransform_Sky'].momentum = Vec3f(0.005, 0, 0)

        # Reloader
        bl = MFBoolListener(
            onTrue=self.touch_reloader,
        )
        space.nodes["Mesh_Quiver"].h3dNode.isTouched.routeNoEvent(bl)
        space.nodes["Mesh_ArrowFeathers"].h3dNode.isTouched.routeNoEvent(bl)
        space.nodes["Mesh_ArrowStick"].h3dNode.isTouched.routeNoEvent(bl)

        # Firing mechanism (Either omni button)
        bl = BoolListener(
            onTrue=self.press_stylus_button,
        )
        hgt.haptics.hdev.mainButton.routeNoEvent(bl)
        hgt.haptics.hdev.secondaryButton.routeNoEvent(bl)

    def build_sounds(self):
        self.whizz_sound = Sound(url="sounds/whizz.wav", intensity=1.0)
        self.impact_sound = Sound(url="sounds/impact.wav", intensity=1.0)
        self.squeak_sound = Sound(url="sounds/squeak.wav", intensity=0.5)
        self.ping_sound = Sound(url="sounds/ping.wav", intensity=0.5)
        self.cheers_sound = Sound(url="sounds/cheers.wav", copies=2, intensity=0.5)
        self.fairy_sound = Sound(url="sounds/fairy.wav", intensity=0.5)
        #self.forest_sound = Sound(url="sounds/forest.ogg", intensity=1.0)
        if self.level < 3:
            self.music_sound = Sound(url="sounds/william1.ogg", intensity=0.5, loop=True)
        else:
            self.music_sound = Sound(url="sounds/william2.ogg", intensity=0.5, loop=True)

    def build_arrow_fader(self):
        self.arrow_fader = ts = hgn.TimeSensor(
            cycleInterval = 1.5,
            loop = False
        )

        si = hgn.ScalarInterpolator(
            key = [0, 0.5, 1],
            keyValue = [1, 1, 0],
        )

        self.add_child(ts)
        self.add_child(si)

        ts.h3dNode.fraction_changed.route(
            si.h3dNode.set_fraction
        )
        si.h3dNode.value_changed.routeNoEvent(
            space.nodes["Material_GuideArrow"].h3dNode.transparency
        )

    def build_feedback_label(self):
        # "Hide" feedback label
        space.nodes["Text_FeedbackLabel"].string = [""]

        # Build fading interpolator
        self.feedback_fader = ts = hgn.TimeSensor(
            cycleInterval = 1.0,
            loop = False
        )

        si = hgn.ScalarInterpolator(
            key = [0, 0.1, 0.9, 1],
            keyValue = [1, 0, 0, 1],
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
            space.nodes["Material_FeedbackLabel"].h3dNode.transparency
        )

        ts.h3dNode.fraction_changed.route(
            pi.h3dNode.set_fraction
        )
        pi.h3dNode.value_changed.routeNoEvent(
            space.nodes["Transform_FeedbackLabel"].h3dNode.scale
        )

    def build_final_score_grower(self):
        # Build fading interpolator
        self.final_score_grower = ts = hgn.TimeSensor(
            cycleInterval = 2.0,
            loop = False
        )

        ei = hgn.EaseInEaseOut(
            key = [0, 1],
            easeInEaseOut = [0.1, 0.9, 0.5, 0.5],
        )

        pi = hgn.PositionInterpolator(
            key = [0, 1],
            keyValue = [
                Vec3f(1, 1, 1),
                Vec3f(1, 1, 1) * 1.3,
            ],
        )

        for n in [ts, ei, pi]:
            self.add_child(n)

        ts.h3dNode.fraction_changed.route(
            ei.h3dNode.set_fraction
        )
        ei.h3dNode.modifiedFraction_changed.route(
            pi.h3dNode.set_fraction
        )
        pi.h3dNode.value_changed.routeNoEvent(
            space.nodes["Transform_FinalScore"].h3dNode.scale
        )


