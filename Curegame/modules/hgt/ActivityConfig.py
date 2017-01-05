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

import simplejson
import logging

_log = logging.getLogger('config')

###########################################################################
# FeatureFlags.
###########################################################################

# NOTE: This class is duplicated in ``vrs.config`` due to licensing issues (HGT
# is GPL, the rest of the code is not open-source). If you make any changes or
# fixes make sure to apply them there as well!

class FeatureFlags(dict):
    """
    Dictionary like object where keys can be accessed as attributes,
    i.e. obj["key"] => obj.key access the same thing. Missing keys will
    automatically default to boolean False.

    Example:
      f = FeatureFlags(enable_clouds=False, enable_rainbow=False)

      if f.enable_clouds and f["enable_rainbow"]: 
        print "Render clouds and/or rainbows!"

    """
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            if name[:1] == "_":
                raise AttributeError(name)
            else:
                _log.error("Missing feature flag: %s" % name)
                return False

    def __missing__(self, key):
        return self.__getattr__(key)
    
    def __setattr__(self, name, value):
        self[name] = value

        
###########################################################################
# ActivityConfig.
###########################################################################
        
class ActivityConfig(object):
    def __init__(self, filename):
        try:
            config = simplejson.loads(
                open(filename, "rt").read().decode("utf-8"))
        except IOError:
            config = {}

        self.i18n_catalog = config.get("i18n_catalog", None)
        self.features = FeatureFlags(config.get("features", {}))
        self.settings = config.get("settings", {})

                                    
###########################################################################
# The End.
###########################################################################
