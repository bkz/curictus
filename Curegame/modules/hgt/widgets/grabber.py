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

import hgt
import copy
import math
from hgt.gamemath import DEG2RAD
from H3DUtils import *

###########################################################################
# Grabber: pick up and release objects.
###########################################################################

class Grabber:
    def __init__(self):
        self.grab_objects = {}
        self.tilt_matrix = Rotation(1, 0, 0, 0)
        self.grabbing = False
        self.grab_object = None

    # Correct for world tilt
    def correct_tilt(self, tilt):
        self.tilt_matrix = Rotation(1, 0, 0, tilt * DEG2RAD)

    def update(self):
        if self.grabbing:
            self.grab_object.transform.translation = \
                    self.tilt_matrix * hgt.haptics.proxyPosition

    def register(self, transform, toggle):
        go = GrabObject(transform=transform, toggle=toggle)
        self.grab_objects[go] = go
        return go

    def grab(self, grabObject):
        if not self.grabbing:
            grabObject.toggle.hapticsOn = False
            self.grabbing = True
            self.grab_object = grabObject
            self.update()

    def release(self, enableToggle=False):
        if self.grabbing:
            if enableToggle:
                self.grab_object.toggle.hapticsOn = True
            self.grab_object = None
            self.grabbing = False
            self.update()

class GrabObject:
    def __init__(self, transform, toggle):
        self.transform = transform
        self.toggle = toggle

        self.set_default_transform()

    def set_default_transform(self):
        self.original_translation = self.transform.translation
        self.original_rotation = self.transform.rotation

    def reset_transform(self):
        self.transform.translation = self.original_translation
        self.transform.rotation = self.original_rotation
