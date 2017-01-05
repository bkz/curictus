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

import os
import logging
import subprocess

_log = logging.getLogger('h3dconfig')

##############################################################################
# Templates.
##############################################################################

# Source: %H3D_ROOT%/settings/current/deviceinfo.x3d
DEVICEINFO_X3D_TEMPLATE = """<Inline DEF="DEFAULT_DEVICEINFO" url="../display/%(name)s/device/Omni(1to1)" />"""

# Source: %H3D_ROOT%/settings/current/viewpoing.x3d
VIEWPOINT_X3D_TEMPLATE = """<Inline DEF="DEFAULT_VIEWPOINT" url="../display/%(name)s/viewpoint/1to1" />"""

# Source: %H3D_ROOT%/settings/h3dload.init
H3DLOAD_INI_TEMPLATE = """\
[haptics device]
device = Omni(1to1)
stylus = H3D Default.x3d

[graphical]
rendermode = MONO
mirrored = False
viewpoint = 1to1
fullscreen = False

[display]
type = %(name)s

"""

##############################################################################
# H3DConfig.
##############################################################################

class H3DConfig(object):
    def __init__(self, rootdir):
        """
        Bind configurator to H3D installation located at ``rootdir`` which
        should point to same location as the H3D_ROOT environment variable
        which H3D requires in order to function properly (hint: the settings/
        folder should be located at %H3D_ROOT%/settings).
        """
        self.rootdir = rootdir


    def set_display_type(self, name):
        """
        Override H3D configuration to use display type ``name`` (note: will
        overwrite content in %H3D_ROOT%/settings/current/ folder as well as
        `h3load.ini`). Return True/False to signal success.
        """
        if not os.path.isdir(os.path.join(self.rootdir, "settings/display", name)):
            _log.warning("Unknown H3D display type: %s" % name)
            return False
        try:
            filename = os.path.join(self.rootdir, "settings/current/deviceinfo.x3d")
            open(filename, "wt").write(DEVICEINFO_X3D_TEMPLATE % {"name" : name})

            filename = os.path.join(self.rootdir, "settings/current/viewpoint.x3d")
            open(filename, "wt").write(VIEWPOINT_X3D_TEMPLATE % {"name" : name})

            filename = os.path.join(self.rootdir, "settings/h3dload.ini")
            open(filename, "wt").write(H3DLOAD_INI_TEMPLATE % {"name" : name})

            return True
        except IOError:
            return False;


    def set_display_mode(self, mode):
        """
        Configure display mode for attached screen using ``mode`` which is a
        string composed as following:

          <width>x<height>_<rate>Hz_<flipped|landscape>

        Example:
          1680x1050_60Hz_landscape
          1680x1050_120Hz_flipped

        For details on supported modes see ``display.exe``.
        """
        exe = os.path.join(os.environ["CUREGAME_ROOT"], "bin\\display.exe")
        # Launch helper executable by forcing the application to hide all of
        # its window, including the console which we don't to popup.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        return subprocess.call([exe, "/%s" % mode], startupinfo=startupinfo) == 0


##############################################################################
# The End.
##############################################################################
