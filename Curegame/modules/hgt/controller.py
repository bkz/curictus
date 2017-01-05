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

"""
Game controller.
"""

from H3DInterface import *
import H3DUtils
import hgt
import sys
from hgt.utils import log_info
from hgt.nodes import H3DWrapNode

# Set to true to enable throttling of updates to games
THROTTLE_FPS = False

# Seconds to wait until forcefully terminating, if distance traversed < IDLE_DISTANCE
IDLE_TIMEOUT = 60.0 * 5 # seconds
IDLE_DISTANCE = 0.5 # meters

class Controller(object):
    def __init__(self, topNode, statsNode, gameinstance):
        #print "Argval:", sys.argv

        self.gameBuilt = False
        self.gameStarted = False

        hgt.world.bind_world(topNode)

        self._game = gameinstance
        self._game.quit2 = self.quit # modifying!

        if statsNode is not None:
            self.stats = H3DWrapNode(statsNode)
        else:
            self.stats = None
        self._game.stats = self.stats

        # Using unmodified H3DLoad (no stats available)
        if self.stats is None:
            sys.stderr.write("Warning: Using H3DLoad without HapticDeviceStats.")
            self.build_game()

        # Using vrs.exe (stats available)
        # Don't start until the stat node has become active.
        else:
            # Check max 10 times. If no omni is connected,
            # this would otherwise be an endless loop.
            # TODO: Cleaner solution.
            self.statsCheckCounter = 10
            self.check_stats()

    def check_stats(self):
        if self.stats.active == True:
            self.build_game()
        elif self.statsCheckCounter == 0:
            sys.stderr.write("Warning: HapticDeviceStats is not active, bypassing. Check if Omni is connected.")
            self.build_game()
        else:
            self.statsCheckCounter -= 1
            hgt.time.add_timeout(0.1, self.check_stats)

    def build_game(self):
        self._game.build()

        # Enable update loop
        self.gameBuilt = True

        hgt.time.add_wait(self.start)

    def keyboard_quit(self, evt):
        self._game.premature_quit()

    def start(self):
        hgt.world.hide_fog()
        hgt.time.add_wait(self.start2)

    def start2(self):
        hgt.world.haptics_on()
        hgt.world.graphics_on()
        self._game.start()
        self.gameStarted = True
        self.initialize_idle_check()

    def initialize_idle_check(self):
        self.start_distance = hgt.assessment.distance
        self.idle_timer = hgt.time.add_timeout(IDLE_TIMEOUT, self.idle_check)

    def idle_check(self):
        d = hgt.assessment.distance
        dd = d - self.start_distance
        self.start_distance = d
        print "\nIdle check, distance delta:", dd

        if dd < IDLE_DISTANCE:
            self._game.premature_quit()
        else:
            self.idle_timer = hgt.time.add_timeout(IDLE_TIMEOUT, self.idle_check)

    def quit(self):
        hgt.assessment.store()

        if hasattr(self._game, "cleanup"):
            self._game.cleanup()

        if self._game.get_result("completed"):
            log_info("Game completed.")
            if "--log-activity" in sys.argv:
                log_info("Completion logged.")
            else:
                log_info("Activity not logged.")
        else:
            log_info("Game not completed.")

        sys.exit(0)

    def update(self):
        if self.gameBuilt:
            hgt.assessment.update()

            if hasattr(self._game, "update") and self.gameStarted:
                self._game.update()

class Updater(AutoUpdate(SFTime)):
    def __init__(self, updatee):
        AutoUpdate(SFTime).__init__(self)
        self._updatee = updatee

        self.accumulated_dt = 0.0
        self.last_dt = 0.0
        self.min_fps = 59.0
        self.max_fps = 60.0

        if THROTTLE_FPS:
            print "FPS throttling enabled"

    def update(self, event):
        hgt.time.update()
        dt = hgt.time.dt
        self.accumulated_dt += dt

        if THROTTLE_FPS:
            if self._updatee.gameStarted and hgt.time.duration > 4.0 and self.last_dt > 1.0 / self.min_fps:
                print "Warning: %.2f seconds - update loop stalling @ %.1f fps (warning level %.1fps)" % (hgt.time.duration, 1.0 / self.last_dt, self.min_fps)
                print hgt.time.fps

            if self.accumulated_dt > 1.0 / self.max_fps:
                self.accumulated_dt = 0.0
                self._updatee.update()
        else:
            self._updatee.update()

        self.last_dt = dt

        return event.getValue()


# NOTE: we need to store the updater field as a global variable in order to
# force to the Python runtime to not GC the object. H3D 2.1.1+ will not keep
# references to routed fields!
updater = None

def start(references, gameinstance):
    refList = references.getValue()
    node = refList[0]

    statsNode = None
    if len(refList) > 1:
        statsNode = refList[1]

    global updater
    ctrl = Controller(node, statsNode, gameinstance)
    updater = Updater(ctrl)
    H3DUtils.time.route(updater)
