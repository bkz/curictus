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

import os, sys
import logging
import time

###########################################################################
# Bootstrap and configure H3D environment.
###########################################################################

def setup(rootdir):
    """
    Attempt to configure environment by locating 'bootstrap.py' in ``rootdir``
    or by searching parent folders relative to ``rootdir``.
    """
    rootdir = os.path.abspath(rootdir)
    if os.path.isfile(os.path.join(rootdir, "bootstrap.py")):
        sys.path.append(rootdir)
        import bootstrap
        bootstrap.setup(rootdir, "hgt.log")
    else:
        head, tail = os.path.split(rootdir)
        if head and tail:
            setup(head)
        else:
            raise RuntimeError("Could not locate bootstrap.py")

setup(os.curdir)

###########################################################################
# Import and launch selected game activity.
###########################################################################

try:
    import hgtgame
    import hgt.controller
    from H3DUtils import time as h3dtime

    hgt.eventlog.write(
        "<info timestamp=\"%d\" name=\"%s\" />\n" % (
            int(h3dtime.getValue()),
            os.path.split(os.path.split(hgtgame.__file__)[0])[1]))
    hgt.controller.start(references, hgtgame.Game())
except:
    logging.exception("Caught unhandled exception")
    sys.exit(1)
