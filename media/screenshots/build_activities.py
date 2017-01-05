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
import sys

rootdir = os.path.abspath("..\..\Curegame")
pypath = os.path.join(rootdir, "python")
if os.path.isdir(pypath):
    os.environ["PATH"] =  pypath + ";" + os.environ["PATH"]
else:
    raise RuntimeError("Could not locate Python binaries directory")

os.environ["CUREGAME_ROOT"] = rootdir

# Forccefully take over Python environment configuration.
os.environ["PYTHONHOME"] = pypath
path = os.path.join(rootdir, "modules")
os.environ["PYTHONPATH"] = path
sys.path = [path] + sys.path

# Get activities from VRS configuration
from vrs.config.activities import HGT_GAMES, HGT_TESTS, DELETED_HGT_GAMES, DELETED_HGT_TESTS, DELETED_LEGACY_GAMES
gameinfo = {}
for d in [HGT_GAMES, HGT_TESTS, DELETED_HGT_GAMES, DELETED_HGT_TESTS, DELETED_LEGACY_GAMES]:
    gameinfo.update(d)

screenshot_dir = './input/screenshots'
output_dir = os.path.join(rootdir, 'media', 'screenshots')
convert_cmd = 'convert.exe -sharpen 1.5' #-filter Lanczos'
convert_variants = [
    ('-resize 840x525', 'large'),
    ('-resize 504x315', 'medium'),
    ('-resize 300x188', 'small'),
    ('-resize 168x105 -gravity Center -crop 100x100+0+0 +repage', 'square_100'),
    ('-resize 77x48 -gravity Center -crop 48x48+0+0 +repage', 'square_48'),
]

warnings = 0

if not os.path.isdir(output_dir):
    print "Something went horribly wrong. There was no output directory."
    print "I was expecting to write to", output_dir
    sys.exit(0)

for root, dirs, files in os.walk(screenshot_dir):
    for name in files:
        path = os.path.join(root, name)

        if path.endswith('.jpg') or path.endswith('.png'):
            activity_id = name[:-4].lower()

            if activity_id in gameinfo.keys():
                print "\n%s" % activity_id
                for v in convert_variants:
                    output_file = os.path.join(output_dir, activity_id + '_%s.jpg' % v[1])
                    cmd = "%s %s %s %s" % (convert_cmd, v[0], path, output_file)
                    print cmd
                    os.system(cmd)
            else:
                print "Skipping unregistered activity %s" % name
                warnings +=1

print "\nFinished with %d warning(s)" % warnings
