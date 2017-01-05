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
from hgt.gameelements import *
from hgt.listeners import *
from hgt.locale import translate as _
from hgt.nodes import *
from hgt.utils import *
from hgt.widgets.pushbutton import PushButton

from H3DInterface import *

import random
import math
import os

import space

MAX_CARDS = 26

class Game(hgt.game.Game):
    def build(self):
        random.seed()

        # Setup hgt world
        hgt.world.load_stylus('ball')
        hgt.world.stereoInfo.focalDistance = 0.5

        # Load Blender scene
        self.add_child(space.world)

        cfg = self.load_config()
        self.level = cfg.settings["memory_level"]

        if self.level == 1:
            self.cardsUsed = [10, 11, 12, 13, 18, 19, 20, 21]
        elif self.level == 2:
            self.cardsUsed = [
                2, 3, 4, 5,
                10, 11, 12, 13,
                18, 19, 20, 21,
            ]
        elif self.level == 3:
            self.cardsUsed = [
                1, 2, 3, 4, 5, 6,
                9, 10, 11, 12, 13, 14,
                17, 18, 19, 20, 21, 22,
            ]
            #self.cardsUsed = [10, 11, 12, 13, 18, 19, 20, 21]
            #self.cardsUsed = range(26)

        self.build_world()

        self.started = False

        self.showDelay = 2.0
        self.firstCard = None
        self.secondCard = None
        self.bothTurned = False
        self.cardsLeft = len(self.cardsUsed)
        self.moves = 0
        self.mistakes = 0
        self.scoreText.string = ["%02d" % self.moves]
        self.startTime = hgt.time.now

    def start(self):
        self.started = True

    def press_card(self, evt):
        c = evt.card

        if self.cardsLeft <= 0:
            self.noTurnSound.play()

        elif self.bothTurned:
            self.noTurnSound.play()

        elif self.firstCard is c:
            self.noTurnSound.play()

        else:
            c.reveal()
            self.cardTurnSound.play()

            if self.firstCard is None:
                self.firstCard = c
            else:
                self.secondCard = c
                self.bothTurned = True
                if self.firstCard.pairId == self.secondCard.pairId:
                    hgt.time.add_timeout(self.showDelay, self.reset_cards)
                else:
                    hgt.time.add_timeout(self.showDelay, self.reset_cards)

    def reset_cards(self):
        if self.firstCard.pairId == self.secondCard.pairId:
            self.firstCard.disable()
            self.firstCard.remove()
            self.secondCard.disable()
            self.secondCard.remove()
            self.correctPairSound.play()
            self.cardsLeft -= 2
        else:
            self.wrongPairSound.play()
            self.firstCard.hide()
            self.secondCard.hide()
            self.mistakes += 1

        self.firstCard = None
        self.secondCard = None

        self.moves += 1
        self.scoreText.string = ["%02d" % self.moves]

        if self.cardsLeft > 0:
            self.bothTurned = None
        else:
            hgt.time.add_timeout(0.5, self.end)

    def end(self):
        self.finishedSound.play()
        self.log_score(
            level = self.level,
            duration = hgt.time.now - self.startTime,
            moves = self.moves,
            mistakes = self.mistakes,
        )
        hgt.time.add_timeout(4.5, self.quit)

    def build_world(self):
        self.scoreText = space.nodes["Text_SCORE"]
        self.movesText = space.nodes["Text_MOVES"]
        self.movesText.string = [_("MOVES")]
        space.nodes["Text_LevelLabel"].string = [_('LEVEL')]
        space.nodes["Text_Level"].string = [[_('Easy'), _('Medium'), _('Hard')][self.level - 1]]

        self.cardTurnSound = Sound(url = "sounds/flip.wav", copies = 2, intensity = 0.5)
        self.noTurnSound = Sound(url = "sounds/click.wav", copies = 2, intensity = 1.0)
        self.wrongPairSound = Sound(url = "sounds/click.wav", copies = 1, intensity = 1.0)
        self.correctPairSound = Sound(url = "sounds/ding.wav", copies = 1, intensity = 1.0)
        self.finishedSound = Sound(url = "sounds/cheer.wav", copies = 1, intensity = 0.5)

        self.cards = []

        for i in range(MAX_CARDS):
            cardMesh = space.nodes["Mesh_C%d" % (i)]
            cardT = space.nodes["Transform_C%d" % (i)]
            cardAppearance = space.nodes["Appearance_C%d" % (i)]
            toggle = space.nodes["ToggleGroup_C%d" % (i)]

            if i not in self.cardsUsed:
                # Hide unused cards
                toggle.graphicsOn = False
                toggle.hapticsOn = False
            else:
                imageTexture = hgn.ImageTexture(url="textures/cardback.jpg")

                card = Card(
                    backTexture = imageTexture,
                    appearance = cardAppearance,
                    toggle = toggle
                )
                self.cards.append(card)

                event = Event()
                event.card = card

                button = PushButton(
                    transformNode = cardT.h3dNode,
                    geometry = cardMesh.h3dNode,
                    onPress = self.press_card,
                    displacement = Vec3f(0, 0, -0.005),
                    event = event,
                )

        cardfronts = []
        for fn in os.listdir('cardimages'):
            if fn.endswith('.jpg'):
                cardfronts.append('cardimages/' + fn)

        random.shuffle(cardfronts)
        random.shuffle(self.cards)

        for i in range(len(self.cardsUsed) / 2):
            index = i * 2
            cardfront = hgn.ImageTexture(url = cardfronts.pop())
            c1 = self.cards[index]
            c2 = self.cards[index + 1]

            c1.frontTexture = cardfront
            c2.frontTexture = cardfront

            c1.pairId = i
            c2.pairId = i

class Card:
    def __init__(self, backTexture, appearance, toggle):
        self.appearance = appearance
        self.backTexture = backTexture
        self.toggle = toggle

        self.frontTexture = None
        self.pairId = None
        self.enabled = True

        self.appearance.texture = self.backTexture

    def reveal(self):
        self.appearance.texture = self.frontTexture

    def hide(self):
        self.appearance.texture = self.backTexture

    def disable(self):
        self.enabled = False

    def remove(self):
        self.toggle.hapticsOn = False
        self.toggle.graphicsOn = False

