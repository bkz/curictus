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

import itertools

###########################################################################
# VRS activities master configuration.
###########################################################################

# NOTE: If you modify a game/test (i.e. bump the version) you have to copy the
# exiting row and put it into ``DELETED_HGT_GAMES`` or ``DELETED_HGT_TEST`` and
# replace the older GUID with a new one. Use the uuid.uuid4() library function
# to generate new GUIDs.

HGT_TESTS = {
    "neglecttest"   : (r"activities\games\Neglecttest",        "Neglecttest.x3d", "1.0", "test", "26efc26c-8288-4f23-9bff-0dd3d9c978dc"),
    "point"         : (r"activities\games\Pointtest",          "Pointtest.x3d",   "1.0", "test", "319f68f0-db79-11de-a2f3-002186a2bf30"),
    "precision_h"   : (r"activities\games\Precision-H",        "Precision-H.x3d", "1.0", "test", "0a2ed219-fe59-422a-8aeb-3c4145107a3c"),
    "precision_v"   : (r"activities\games\Precision-V",        "Precision-V.x3d", "1.0", "test", "aa64d5b2-4489-438c-9850-2a0f41560152"),
    "tmt_a"         : (r"activities\games\TMT-A",              "TMT-A.x3d",       "1.0", "test", "6eb84faa-60b3-437d-9b2a-219569ebe524"),
    "tmt_b"         : (r"activities\games\TMT-B",              "TMT-B.x3d",       "1.0", "test", "2f973955-9626-4bca-8b28-30eb470b0d5c"),
}

HGT_GAMES = {
    "archery2"      : (r"activities\games\Archery2",            "Archery2.x3d",    "1.0", "game", "78148a3a-9542-4c4f-82bc-c0c3fe47c70e"),
    "bandit"        : (r"activities\games\Bandit",              "Bandit.x3d",      "1.0", "game", "31a18bd0-db79-11de-976f-002186a2bf30"),
    "bingo2"        : (r"activities\games\Bingo2",              "Bingo2.x3d",      "1.0", "game", "73c48fd9-c0fe-489d-9c84-c5925d60f558"),
    "codebreak"     : (r"activities\games\CodeBreak",           "CodeBreak.x3d",   "1.0", "game", "e9f35a11-2659-4351-97e4-64cfd40ad7e7"),
    "colors"        : (r"activities\games\Colors",              "Colors.x3d",      "1.0", "game", "31a18bd1-db79-11de-b060-002186a2bf30"),
    "fishtank2"     : (r"activities\games\FishTank2",           "Fishtank2.x3d",   "1.0", "game", "5c808c95-8db3-428c-b6ad-415f0ad77fff"),
    "intro"         : (r"activities\games\Intro",               "Intro.x3d",       "1.0", "game", "0636e26e-0a2e-4f9b-b36a-c793eea71e3e"),
    "math2"         : (r"activities\games\Math2",               "Math2.x3d",       "1.0", "game", "367ca141-89cc-443f-a140-f0e34e67322b"),
    "memory"        : (r"activities\games\Memory",              "Memory.x3d",      "1.0", "game", "0c4a17f4-6cd3-4d84-9a6c-8bef6ae31cdc"),
    "pong"          : (r"activities\games\Pong",                "Pong.x3d",        "1.0", "game", "31a18bd2-db79-11de-80d2-002186a2bf30"),
    "racer"         : (r"activities\games\Racer",               "Racer.x3d",       "1.0", "game", "31a1b2de-db79-11de-b7c8-002186a2bf30"),
    "simon2"        : (r"activities\games\Simon2",              "Simon2.x3d",      "1.0", "game", "7c212227-d448-47fd-b2c0-3ede53b5acea"),
    "slotmachine"   : (r"activities\games\SlotMachine",         "SlotMachine.x3d", "1.0", "game", "41360f3d-5f58-4144-bb92-3c27d4e1de55"),
}

# NOTE: "deleted" in this context actually means "deactivated", if you upgrade
# an activity or even remove one we'll still want to keep them around to
# reference existing data in the DB via PCMS etc.

DELETED_HGT_TESTS = {
    "tmt"           : (r"activities\games\TMT",                  "TMT.x3d",      "1.0", "test", "31a18bcf-db79-11de-a27b-002186a2bf30"),
}

DELETED_HGT_GAMES = {
    "slots"         : (r"activities\games\Slots",                "Slots.x3d",    "1.0", "game", "31a1b2df-db79-11de-a51c-002186a2bf30"),
    "intro"         : (r"activities\games\Intro",                "Intro.x3d",    "0.1", "game", "c4862373-efac-4630-87f1-72866ed24230"),
}

DELETED_LEGACY_GAMES = {
    "archery"       : (r"legacy\activities\ArcheryLegacy",       "Game.x3d",    "1.0", "game", "31a1b2e0-db79-11de-8d23-002186a2bf30"),
    "fishtank"      : (r"legacy\activities\FishtankLegacy",      "Game.x3d",    "1.0", "game", "31a1b2e2-db79-11de-adaa-002186a2bf30"),
    "mugmastermind" : (r"legacy\activities\MugMasterMindLegacy", "Game.x3d",    "1.0", "game", "31a1b2e6-db79-11de-aa09-002186a2bf30"),
    "bingo"         : (r"legacy\activities\BingoLegacy",         "Game.x3d",    "1.0", "game", "31a1b2e1-db79-11de-aa22-002186a2bf30"),
    "math"          : (r"legacy\activities\MathLegacy",          "Game.x3d",    "1.0", "game", "31a1b2e4-db79-11de-b5e3-002186a2bf30"),
    "memory"        : (r"legacy\activities\MemoryLegacy",        "Game.x3d",    "1.0", "game", "31a1b2e5-db79-11de-a11d-002186a2bf30"),
    "simon"         : (r"legacy\activities\SimonLegacy",         "Game.x3d",    "1.0", "game", "31a1b2e7-db79-11de-92b6-002186a2bf30"),
}


###########################################################################
# HGT activity difficulty levels.
###########################################################################

DIFFICULTY_LEVELS = {
    "archery2"      : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "bandit"        : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "bingo2"        : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "codebreak"     : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "colors"        : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "fishtank2"     : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "math2"         : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "memory"        : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "pong"          : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "racer"         : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
    "simon2"        : {"easy" : 1, "medium" : 2, "hard" : 3, "max" : 5 },
}

###########################################################################
# Highscore sorting helpers.
###########################################################################

def sort_match(a, b):
    """
    Order session scores ``a`` and ``b`` using match/versus rules:

     (1) Wins rank higher than losses.

     (2) Wins rank higher than other wins if gap to opponent score is higher,
         i.e winning by 5-1 is better than 5-4.

     (3) Losses rank higher thank other losses if player score is higher,
         i.e. loosing by 5-3 is better than 5-1.

    """
    if a["win"]:
        if b["win"]:
            if a["opponent_score"] < b["opponent_score"]:
                return -1       # (2)
            else:
                return 1        # (2)
        else:
            return -1           # (1)
    else:
        if b["win"]:
            return 1            # (1)
        else:
            if a["player_score"] > b["player_score"]:
                return -1       # (3)
            else:
                return 1        # (3)


def sort_moves(a, b):
    """
    Order session scores ``a`` and ``b`` using least moves rules:

      (1) Less moves rank higher.

      (2) Equal move count but less time spent rank higher.

    """
    if a["moves"] == b["moves"]:
        if a["duration"] < b["duration"]:
            return -1           # (2)
        else:
            return 1            # (2)
    else:
        if a["moves"] < b["moves"]:
            return -1           # (1)
        else:
            return 1            # (1)


def sort_mistakes(a, b):
    """
    Order session scores ``a`` and ``b`` using least mistakes rules:

     (1) Fewer mistakes rank higher.

     (2) Equal mistakes count but less time spent ranks higher.

    """
    if a["mistakes"] == b["mistakes"]:
        if a["duration"] < b["duration"]:
            return -1           # (2)
        else:
            return 1            # (2)
    else:
        if a["mistakes"] < b["mistakes"]:
            return -1           # (1)
        else:
            return 1            # (1)


def sort_score(a, b):
    """
    Order session scores ``a`` and ``b`` using highest score rules:

      (1) Larger score ranks higher.

      (2) Equal scores but less time spent ranks higher.

    """
    if a["score"] == b["score"]:
        if a["duration"] < b["duration"]:
            return -1           # (2)
        else:
            return 1            # (2)
    else:
        if a["score"] > b["score"]:
            return -1           # (1)
        else:
            return 1            # (1)

def sort_lrscore(a, b):
    """
    Order session left/right scores ``a`` and ``b`` using highest score sum rules:

      (1) Larger score sum ranks higher.

      (2) Equal score sums but less time spent ranks higher.

    """
    if a["left_score"] + a["right_score"] == b["left_score"] + b["right_score"]:
        if a["duration"] < b["duration"]:
            return -1           # (2)
        else:
            return 1            # (2)
    else:
        if a["left_score"] + a["right_score"] > b["left_score"] + b["right_score"]:
            return -1           # (1)
        else:
            return 1            # (1)

def sort_duration(a, b):
    """
    Order session scores ``a`` and ``b`` by least duration first.
    """
    if a["duration"] < b["duration"]:
        return -1
    else:
        return 1


SCORE_FILTERS = {
    # HGT tests.
    "neglecttest"   : lambda s: s["left_score"] > 0 and s["right_score"] > 0,
    "point"         : lambda s: s["duration"] > 0,
    "precision_h"   : lambda s: s["duration"] > 0,
    "precision_v"   : lambda s: s["duration"] > 0,
    "tmt_a"         : lambda s: s["duration"] > 0,
    "tmt_b"         : lambda s: s["duration"] > 0,

    # HGT games.
    "archery2"      : lambda s: s["score"] > 0,
    "bandit"        : lambda s: s["score"] > 0,
    "bingo2"        : lambda s: s["score"] > 0,
    "codebreak"     : lambda s: s["duration"] > 0 and s["win"] == True,
    "colors"        : lambda s: s["moves"] > 0,
    "fishtank2"     : lambda s: s["score"] > 0,
    "intro"         : lambda s: s["score"] > 0,
    "math2"         : lambda s: s["score"] > 0,
    "memory"        : lambda s: s["duration"] > 0,
    "pong"          : lambda s: s["player_score"] > 0 or s["opponent_score"] > 0,
    "racer"         : lambda s: s["duration"] > 20,
    "simon2"        : lambda s: s["score"] > 0,
    "slotmachine"   : lambda s: s["score"] > 0,

    # Deleted legacy games.
    "archery"       : lambda s: s["score"] > 0,
    "fishtank"      : lambda s: s["score"] > 0,
    "mugmastermind" : lambda s: s["duration"] > 20 and s["win"] == True,
    "bingo"         : lambda s: s["moves"] > 0,
    "math"          : lambda s: s["duration"] > 20,
    "simon"         : lambda s: s["duration"] > 20,
}



SCORE_SORTERS = {
    # HGT tests.
    "neglecttest"   : sort_lrscore,
    "point"         : sort_duration,
    "precision_h"   : sort_duration,
    "precision_v"   : sort_duration,
    "tmt_a"         : sort_mistakes,
    "tmt_b"         : sort_mistakes,

    # HGT games.
    "archery2"      : sort_score,
    "bandit"        : sort_score,
    "bingo2"        : sort_score,
    "codebreak"     : sort_duration,
    "colors"        : sort_moves,
    "fishtank2"     : sort_score,
    "intro"         : sort_score,
    "math2"         : sort_score,
    "memory"        : sort_duration,
    "pong"          : sort_match,
    "racer"         : sort_duration,
    "simon2"        : sort_score,
    "slotmachine"   : sort_score,

    # Deleted legacy games.
    "archery"       : sort_score,
    "fishtank"      : sort_score,
    "mugmastermind" : sort_duration,
    "bingo"         : sort_score,
    "math"          : sort_mistakes,
    "simon"         : sort_duration,
}


###########################################################################
# Sanity checks.
###########################################################################

entries = HGT_TESTS.items() + HGT_GAMES.items()

guids = set(guid for (alias, (path, x3d, version, kind, guid)) in entries)

# Simple self-check to make sure we've assigned unique UUIDs.
assert len(entries) == len(guids)

# Simple self-check to make sure all activties are present and valid.
for (alias, (path, x3d, version, kind, guid)) in entries:
    assert alias in SCORE_FILTERS
    assert alias in SCORE_SORTERS


###########################################################################
# Utilities.
###########################################################################

def get_default_level(activity):
    """
    Return default difficulty level for ``activity`` (easy...hard).
    """
    return DIFFICULTY_LEVELS[activity]["easy"]


def get_level_xrange(activity):
    """
    Returns xrange of valid levels values for ``activity`` (0...N).
    """
    level = DIFFICULTY_LEVELS[activity]
    assert level["easy"] < level["medium"] < level["hard"] < level["max"]
    return xrange(level["easy"], level["max"])


###########################################################################
# Standalone build-mode.
###########################################################################

#  Output AS3 i18n strings table for /flex/lib/vrs/util/activitydata.as
if __name__ == '__main__':
    for (comment, activities) in (("HGT Tests", HGT_TESTS),
                                  ("HGT Games", HGT_GAMES),
                                  ("Deleted HGT Tests", DELETED_HGT_TESTS),
                                  ("Deleted HGT Games", DELETED_HGT_GAMES),
                                  ("Deleted Legacy Games", DELETED_LEGACY_GAMES)):
        print "//", comment
        for alias in sorted(activities.keys()):
            print """'%s' : [_('$activity_%s_name'), _('$activity_%s_summary'), _('$activity_%s_desc'), _('$activity_%s_video_xml'), _('$activity_%s_level_desc')],""" % tuple([alias] * 6)


###########################################################################
# The End.
###########################################################################

