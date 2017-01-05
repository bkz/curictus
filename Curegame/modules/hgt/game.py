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
Game superclass.
"""

import os

import hgt
import hgt.locale
from hgt.ActivityConfig import ActivityConfig
from activitylog import ActivityLog

# FIXME: No __init__ defined, so self.node and self._activityLog
# defined dynamically.
#
# Furthermore, _gameData depends on the subclass calling add_child at
# some time (which all do, but still...)

# TODO: s/self\.add_node/self\.add_child/ in all games, deprecate
# add_node.

# TODO: rework _gameData logging according to whiteboard discussions.

# FIXME: what if a subclass overrides one of these methods
# inadvertantly?

class Game(object):
    def add_node(self, n):
        self.add_child(n)

    def add_child(self, n):
        try:
            self.node
        except AttributeError:
            self.node = hgt.world.node

        self.node.add(n)

        self._gameData = {
            'completed': False,
            'result': 0.0,
            'goal_result': 0.0,
            'min_result': 0.0,
            'max_result': 0.0,
            'result_type': '',
            'duration': 0.0,
        }

        
    def load_config(self):
        """
        Load HGT config (feature flags and patient settings) passed from the
        VRS manager, setup i18N and return an ``ActivityConfig`` instance.
        """
        cfg = ActivityConfig(os.environ["CUREGAME_HGT_CONFIG_FILENAME"])
        if cfg.i18n_catalog:
            hgt.locale.load_catalog(cfg.i18n_catalog)
        return cfg

        
    def log_event(self, event_id, description, **kwargs):
        try:
            self._activityLog
        except AttributeError:
            self._activityLog = ActivityLog(hgt.eventlog, self.stats)
        self._activityLog.log_event(event_id, description, **kwargs)

    def log_info(self, event_id, description, **kwargs):
        try:
            self._activityLog
        except AttributeError:
            self._activityLog = ActivityLog(hgt.eventlog, self.stats)
        self._activityLog.log_info(event_id, description, **kwargs)

    def log_score(self, **kwargs):
        try:
            self._activityLog
        except AttributeError:
            self._activityLog = ActivityLog(hgt.eventlog, self.stats)
        self._activityLog.log_score(**kwargs)

    def add_nodes(self, ns):
        for n in ns:
            self.add_node(n)
   
    def erase_node(self, n):
        self.node.erase(n)

    # self.quit2 is added by controller.py
    def quit(self):
        self.log_info("quit_type", "Quit normal", forced=False)        
        self.set_result('completed', True)        
        hgt.world.show_fog()
        hgt.time.add_timeout(0.5, self.quit2)

    def premature_quit(self):
        self.log_info("quit_type", "Quit forced", forced=True)
        self.set_result('completed', False)        
        hgt.world.show_fog()
        hgt.time.add_timeout(0.5, self.quit2)

    def set_result(self, key, val):
        self._gameData[key] = val

    def get_result(self, key):
        return self._gameData[key]

