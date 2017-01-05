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
import subprocess
import logging
import logging.handlers
import tempfile

_log = logging.getLogger('encode')

FFMPEG_BINARY = "../../tools/ffmpeg/bin/ffmpeg.exe"
FFMPEG_PRESET = "../../tools/ffmpeg/presets/libx264-slow.ffpreset"

RESOLUTION = "480x320"
FRAMERATE  = "20"

###########################################################################
# Compress and encode raw AVI as H.264 in a FLV container.
###########################################################################

#
# Encoding details:
#
#   1. Manually flip the video vertically (mirrored stereo rendering)
#
#   2. Encode audio as 44.1hz MP3 at 96 kbps since AAC is no longer included in
#      FFMPEG and their experimental own encoder seams to mess up Flash video.
#
#   3. Encode as H.264 using x246 video coded using CRF (constant rate factor)
#      and a default 'slow' preset to ensure high quality output. We'll also
#      match the video framerate with the key frame rate meaning that we'll get
#      a seekable video granualarity of 1 sec.
# 
#   4. We'll advise FFMPEG to match the number of threads to the amount of
#      available cores to mazimize encoding performance.
#
#  NOTE: Using a MP4 container seems to break Flash video seeking, the only
#  truly stable format seems to be MP3 + H.264 muxed into a FLV container.
#

ENCODE_OPTS = """\
-i %(infile)s -vf vflip -acodec libmp3lame -ar 44100 -ab 96k -vcodec libx264 -fpre %(preset)s -crf 22 -s %(resolution)s -r %(framerate)s -g %(framerate)s -threads 0 -y %(outfile)s
"""

def encode(infile, outfile):
    """
    Scale, compress and encode ``infile`` to ``outfile``.
    format using it.
    """
    assert os.path.splitext(infile)[1] == ".avi"
    assert os.path.splitext(outfile)[1] == ".flv"
    opts = ENCODE_OPTS % {
        "infile"     : infile,
        "preset"     : FFMPEG_PRESET,
        "resolution" : RESOLUTION,
        "framerate"  : FRAMERATE,
        "outfile"    : outfile,
        }
    _log.info("%s %s" % (FFMPEG_BINARY, opts))
    (stdout, stderr) = subprocess.Popen([FFMPEG_BINARY] + opts.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    _log.debug(stdout)
    _log.debug(stderr)

    
###########################################################################
# Extract single frame from video stream.
###########################################################################

#
# Extract frame details:
#
#   1. Fast forward trough video stream while flipping frames vertically to
#      compensate for the stream which we've recorded from a mirrored stereo
#      rendering.
#
#   2. Extract a single video frame from the selected offset and save it as an
#      image file using a codec determined from the output filename extension.
#
    
EXTRACT_OPTS = """\
-ss 00:00:%(offset)02d -i %(infile)s -vf vflip -vframes 1 -s %(resolution)s -y %(outfile)s
"""

def screenshot(offset, infile, outfile):
    assert offset >= 0 and offset <= 59
    assert os.path.splitext(infile)[1] == ".avi"
    assert os.path.splitext(outfile)[1] in [".jpg", ".png"]
    opts = EXTRACT_OPTS % {
        "offset"     : offset,
        "infile"     : infile,
        "resolution" : RESOLUTION,
        "outfile"    : outfile,
        }
    _log.info("%s %s" % (FFMPEG_BINARY, opts))
    (stdout, stderr) = subprocess.Popen([FFMPEG_BINARY] + opts.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    _log.debug(stdout)
    _log.debug(stderr)

    
###########################################################################
# Application entry-point.
###########################################################################

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    filelogger = logging.handlers.RotatingFileHandler('encode.log')
    filelogger.setFormatter(logging.Formatter("%(asctime)s : %(message)s"))
    logging.getLogger().addHandler(filelogger)

    for filename in os.listdir("./avi"):
        avi = os.path.join("./avi", filename)
        if not os.path.isfile(avi):
            continue

        flv = os.path.join("./flv", os.path.splitext(filename)[0] + ".flv")
        encode(avi, flv)

        jpg = os.path.join("./jpg", os.path.splitext(filename)[0] + ".jpg")
        screenshot(1, avi, jpg)

        
###########################################################################
# Detect code modification (for automatic restarts).
###########################################################################
