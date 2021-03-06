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
from hgt.utils import unique
from hgt.widgets.grabber import Grabber
from hgt.widgets.pushbutton import PushButton

import math
import random
import space # space.py generated by Blender exporter

from H3DUtils import *

SPACE_TILT = 90.0
COIN_THICKNESS = 0.0026
ROT_CORR = 0.0

###########################################################################
# SlotMachine (replaces Slots, which was modeled for the old exporter).
###########################################################################

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        cfg = self.load_config()

        # hgt world
        hgt.world.stereoInfo.focalDistance = 0.6
        hgt.world.tilt(-SPACE_TILT)
        hgt.world.load_stylus('ball')

        # Load Blender scene
        self.add_child(space.world)

        # Grabber
        self.grabber = Grabber()
        self.grabber.correct_tilt(tilt = SPACE_TILT)

        # Build
        self.build_sounds()
        self.build_world()

        # FIXME: states only used partially
        self.states = Enum('betting', 'spinning')
        self.state = StateManager(self.states, self.states.betting)
        self.state.add(self.states.betting, self.states.spinning)
        self.state.add(self.states.spinning, self.states.betting)

    # Initialization
    def start(self):
        self.start_time = hgt.time.now
        self.ambience_sound.play()

        self.credits = 0
        self.coinstack = 10

        self.cylinder_dts = []
        for i in range(3):
            self.cylinder_dts.append(
                space.nodes["DynamicTransform_Cylinder%d" % i]
            )

        self.reset()

    def reset(self):
        self.state = self.states.betting

        self.winner_paid = 0
        self.coins_bet = 0

        self.payout = False
        self.braking_cylinder = None

        self.reset_cylinders()

        self.update_display()

        self.enable_button(self.button_infos['exit'])

        if self.credits > 0:
            self.enable_button(self.button_infos['bet_one'])

     # Updates
    def update(self):
        self.grabber.update()
        if self.braking_cylinder is not None:
            c = self.braking_cylinder
            a = c.angularMomentum
            if a.x > 1.0:
                c.angularMomentum -= Vec3f(0.01, 0, 0)
            if abs(self.target_angle - c.orientation.angle) < 0.05:
                c.angularMomentum = Vec3f(0, 0, 0)
                c.orientation = Rotation(1, 0, 0, self.target_angle)
                self.spinstop_sound.play()
                self.braking_cylinder = None
                hgt.time.add_timeout(0.3 + random.random(), self.brake_cylinders)

        if self.payout:
            if self.winner_paid == 0:
                self.payout = False
                self.reset()
            else:
                self.winner_paid -= 1
                self.credits += 1
                self.update_display()
                self.blip_sound.play()

    def update_display(self):
        space.nodes["Text_Credits"].string = ["%03d" % self.credits]
        space.nodes["Text_CoinsBet"].string = ["%03d" % self.coins_bet]
        space.nodes["Text_Pay"].string = ["%03d" % self.winner_paid]

    # Visuals
    def disable_button(self, bi):
        bi['enabled'] = False
        bi['material'].transparency = 0.5

    def enable_button(self, bi):
        bi['enabled'] = True
        bi['material'].transparency = 0.0

    def disable_all_buttons(self):
        for bi in self.button_infos.values():
            self.disable_button(bi)

    # Interactivity
    def press_button(self, evt):
        bi = evt.info
        if bi['enabled']:
            self.disable_all_buttons()

            if bi['id'] == 'exit':
                self.end_game()

            elif bi['id'] == 'bet_one':
                self.bet_one()
                #self.enable_button(self.button_infos['exit'])

            elif bi['id'] == 'spin_reels':
                self.state = self.states.spinning
                self.spin_start()

    def bet_one(self):
        self.enable_button(self.button_infos['spin_reels'])

        self.credits -= 1
        self.coins_bet += 1
        self.update_display()

        if self.coins_bet < 3 and self.credits > 0:
            self.enable_button(self.button_infos['bet_one'])

    def reset_cylinders(self):
        self.cylinder_index = 0
        self.reels = []
        for i in range(3):
            self.reels.append(random.randint(0, 9))

    def spin_start(self):
        self.spinstart_sound.play()

        for c in self.cylinder_dts:
            c.angularMomentum = Vec3f(10, 0, 0)

        hgt.time.add_timeout(1.0 + random.random(), self.stop_cylinders)

    def stop_cylinders(self):
        self.plunger_sound.play()
        hgt.time.add_timeout(1.0, self.brake_cylinders)

    def brake_cylinders(self):
        if self.cylinder_index < len(self.cylinder_dts):
            c = self.cylinder_dts[self.cylinder_index]
            self.braking_cylinder = c

            self.target_angle = ((math.pi * 2) / 10.0) * self.reels[self.cylinder_index] + ROT_CORR
            if self.target_angle < 0:
                self.target_angle += math.pi * 2

            self.cylinder_index += 1
        else:
            self.calc_winnings()

    def calc_winnings(self):
        self.winner_paid = 0

        a = self.reels
        b = unique(a)
        c = len(b)

        # All reels equal
        if c == 1:
            self.winner_paid = 50 + 50 * a[0]

        # First two reels equal
        elif a[0] == a[1]:
            self.winner_paid = 25 + 5 * a[0]

        # First reel is symbol 0
        elif a[0] == 0:
            self.winner_paid = 10

        self.winner_paid *= self.coins_bet

        self.update_display()

        if self.winner_paid > 0:
            self.ping_sound.play()

        hgt.time.add_timeout(2, self.pay)

    def pay(self):
        self.payout = True

    def touch_coin(self, evt):
        coinInfo = evt.info
        if not self.grabber.grabbing:
            self.coin_sound.play()
            self.grabber.grab(coinInfo['grabObject'])

    def touch_coin_slot(self):
        if self.grabber.grabbing:
            self.coin_insert_sound.play()
            grab_object = self.grabber.grab_object
            grab_object.reset_transform()
            self.grabber.release(enableToggle=True)
            self.credits += 1
            self.coinstack -= 1
            self.update_display()

            if self.state == self.states.betting and self.coins_bet < 3:
                self.enable_button(self.button_infos['bet_one'])

            # Move coin and coinstack down after release
            coin_displacement = Vec3f(0, 0, -COIN_THICKNESS)
            space.nodes["Transform_Coinstack"].translation += coin_displacement
            space.nodes["Transform_TopCoin"].translation += coin_displacement
            grab_object.set_default_transform()

    def end_game(self):
        hgt.time.add_timeout(1.0, self.end_game2)

    def end_game2(self):
        if self.credits > 0:
            self.coindrop_sound.play()
        space.nodes["Text_Credits"].string = ["000"]
        hgt.time.add_timeout(2.0, self.end_game3)

    def end_game3(self):
        self.log_score(
            duration = hgt.time.now - self.start_time,
            score = self.credits + self.coinstack,
        )
        self.quit()

    # Build
    def build_world(self):
        # Slot machine buttons
        self.button_infos = {
            'spin_reels': {
                'name': 'SpinButton',
                'title': _('SPIN'),
                'id': 'spin_reels',
                'label': space.nodes["Text_SpinButtonLabel"],
                'material': space.nodes["Material_SpinButton"],
            },
            'bet_one': {
                'name': 'BetButton',
                'title': _('BET'),
                'id': 'bet_one',
                'label': space.nodes["Text_BetButtonLabel"],
                'material': space.nodes["Material_BetButton"],
            },
            'exit': {
                'name': 'ExitButton',
                'title': _('EXIT'),
                'id': 'exit',
                'label': space.nodes["Text_ExitButtonLabel"],
                'material': space.nodes["Material_ExitButton"],
            },

        }

        for i in range(3):
            bid = "hold%d" % i
            self.button_infos[bid] = {
                'name': 'HoldButton.%03d' % i,
                'title': _('HOLD'),
                'id': 'hold0',
                'label': space.nodes["Text_HoldButtonLabel.%03d" % i],
                'material': space.nodes["Material_HoldButton.%03d" % i],
            }

        for bi in self.button_infos.values():
            # Set label
            bi['label'].string = [bi['title']]

            e = Event()
            e.info = bi
            pushButton = PushButton(
                transformNode = space.nodes["Transform_%s" % bi['name']].h3dNode,
                geometry = space.nodes["Mesh_%s" % bi['name']].h3dNode,
                displacement = Vec3f(0, 0.005, 0), # push down 5 mm in negative z dir
                onPress = self.press_button,
                pressSound = self.button_up_sound,
                releaseSound = self.button_down_sound,
                event = e,
            )

            self.disable_button(bi)

        # Coin
        transform = space.nodes["Transform_TopCoin"]
        grabObject = self.grabber.register(
            transform=transform,
            toggle=space.nodes["ToggleGroup_TopCoin"],
        )
        evt = Event()
        evt.info = {
            'transform': transform,
            'grabObject': grabObject,
            'originalTranslation': transform.translation,
            'originalRotation': transform.rotation,
        }
        bl = MFBoolListener(
            onTrue=self.touch_coin,
            callbackObject = evt,
        )
        space.nodes["Mesh_TopCoin"].h3dNode.isTouched.routeNoEvent(bl)

        # Coin slot
        bl = MFBoolListener(
            onTrue=self.touch_coin_slot,
        )
        space.nodes["Mesh_CoinSlot"].h3dNode.isTouched.routeNoEvent(bl)

    def build_sounds(self):
        self.ambience_sound = Sound("sounds/ambience.ogg", intensity=0.4, loop=True)
        self.coin_insert_sound = Sound("sounds/coininsert.wav", intensity=0.5)
        self.coin_sound = Sound("sounds/coin.wav", intensity=0.5)
        self.ping_sound = Sound("sounds/ping.wav", intensity=0.5)
        self.button_down_sound = Sound("sounds/click.wav")
        self.button_up_sound = Sound("sounds/click.wav", intensity = 0.3)
        self.spinstop_sound = Sound("sounds/spinstop.wav", intensity = 0.5)
        self.spinstart_sound = Sound("sounds/spinstart.wav", intensity = 0.5)
        self.blip_sound = Sound("sounds/blip.wav", intensity = 0.5, copies = 4)
        self.plunger_sound = Sound("sounds/plunger.wav", intensity = 0.5)
        self.coindrop_sound = Sound("sounds/coindrop.wav", intensity = 0.5)
