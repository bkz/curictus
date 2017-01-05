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
Time-related stuff.
"""

from hgt.utils import Borg
from hgt.math import MovingAverage
from hgt.timercallback import TimerCallback

import H3DInterface
import H3DUtils

FPS_WINDOW_SIZE = 10
SOON_DELTA = 0.05

#gTimerCallback = H3DUtils.TimerCallback()
gTimerCallback = TimerCallback()

class Time(Borg):
    def __init__(self):
        self.frame = 0
        self.fps = 0
        self.startTime = self.now
        self.lastTime = self.now
        self.dt = self.lastTime - self.startTime 
        
        self.averager = MovingAverage(n = FPS_WINDOW_SIZE)
       
        self._setup_wait()

    def update(self):
        self.frame += 1
        self.newTime = self.now
        self.dt = self.newTime - self.lastTime
        self.lastTime = self.newTime

        if self.dt > 0:
            #self.fps = self.frame / dt
            self.fps = self.averager.get(1.0 / self.dt)

        if self._waiting:
            self._waitCount -= 1
            if self._waitCount == 0:
                self._waiting = False
                self._waitFn()

    def _setup_wait(self):
        self._waitCount = 0
        self._waiting = False
        self._waitFn = None

    def add_wait(self, fn, frames = 10):
        assert not self._waiting
        self._waiting = True
        self._waitCount = frames
        self._waitFn = fn

    def add_timeout(self, t, fun, args = ()):
        cb = gTimerCallback.addCallback(self.now + t, fun, args)
        return cb

    def clear_timeout(self, cb):
        gTimerCallback.removeCallback(cb)

    @property
    def soon(self):
        """Current time + small delta."""
        return self.now + SOON_DELTA
    @property
    def now(self):
        """Current time."""
        return H3DInterface.time.getValue()

    @property
    def duration(self):
        return self.now - self.startTime

time = Time()
