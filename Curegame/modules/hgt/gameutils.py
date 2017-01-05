##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

#############################################################################
# Enum (bitfield flags) type.
#############################################################################

class Enum(dict):
    """
    Enum like object which maps keys to a sequence of bits (2^N) values which
    can combined to together etc. The flags (enum keys) can be accessed as
    ordinary attributes of a 'Enum' instance.

    Note: enum values/flags have to begin with a capitalized letter!

    Example:
      # 1. Use case: standard enumeration.
      Color = Enum('Black', 'White')

      background = Color.White

      if background != Color.Black:
        print "Background isn't black!"

      # 2. Use case: flags combined for storage in bitfield.
      UserRole = Enum('Admin', 'Support', 'Moderator', 'Guest')

      role = UserRole.Admin | UserRole.Moderator

      if role & UserRole.Moderator:
        print "User has moderation rights!"

      if (role & UserRole.Support) == 0:
        print "User isn't in a support role!"

    Note: enums are essentially a dict with predeterminied key values, using
    the standard dict methods to explore the contents of an instance.
    """

    def __init__(self, *args):
        self.__dict__.__init__()
        for (n, key) in enumerate(args):
            assert(type(key) in [str, unicode])
            self[key] = 2**n

    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise KeyError("Enum has no indentifier '%s'" % name)

    def __missing__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, name, value):
        self[name] = value

    def __repr__(self):
        return "Enum(%s)" % ",".join([repr(k) for k in self])

    @staticmethod
    def get_name(enum_type, value):
        for (k,v) in enum_type.iteritems():
            if v == value:
                return k
        else:
            return value # Unknown enum value.

#############################################################################
# State Manager
#############################################################################

"""
# Example:

Game = Enum("Start", "Idle", "HitFish", "DropFish", "End")

state = StateManager(Game, Game.Start)

state.add(Game.Start, Game.Idle)
state.add(Game.Idle, Game.End)

state.add(Game.Idle, Game.HitFish)
state.add(Game.HitFish, Game.DropFish)
state.add(Game.DropFish, Game.Idle)

if state == Game.Start:
    print "Game start"

state.change(Game.Idle)

try:
    state.change(Game.DropFish)
except Exception, e:
    print e

state.change(Game.HitFish)
state.change(Game.DropFish)
state.change(Game.Idle)
state.change(Game.End)

assert state == Game.End
"""

from collections import defaultdict

class StateManager(Enum):
    def __init__(self, enum, initial):
        self.enum = enum
        self.state = initial
        self.trans = defaultdict(list) # Map state -> [allowed transition states]

    def add(self, state, *transition):
        self.trans[state].extend(transition)

    def change(self, next):
        allowed = self.trans[self.state]
        if allowed and next not in allowed:
            raise RuntimeError("Transition from %s to %s not in allowed [%s]" % (
                    Enum.get_name(self.enum, self.state),
                    Enum.get_name(self.enum, next),
                    ','.join([Enum.get_name(self.enum, s) for s in allowed])))
        else:
            self.state = next

    def __cmp__(self, other):
        return self.state == other

    def __eq__(self, other):
        return self.state == other

    def __repr__(self):
        return "StateManager(%s)" % Enum.get_name(self.enum, self.state)

###########################################################################
# Collision detection and other useful functions.
###########################################################################

def inside_box(point, transform):
    """ Check if point is inside a default non-rotated box. """
    s = transform.scale
    t = transform.translation

    min_x = t.x - s.x
    max_x = t.x + s.x
    xo = point.x > min_x and point.x < max_x

    min_y = t.y - s.y
    max_y = t.y + s.y
    yo = point.y > min_y and point.y < max_y

    min_z = t.z - s.z
    max_z = t.z + s.z
    zo = point.z > min_z and point.z < max_z

    if xo and yo and zo:
        return True
    return False
