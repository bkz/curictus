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

from PIL import Image, ImageFont, ImageDraw

FONT_NAME = "Droid Sans.ttf"
FONT_SIZE = 13

##############################################################################
# Image utilities.
##############################################################################

def set_image_caption(message, imagefile, outfile):
    """
    Generate a white on black caption string covering the entire bottom 40
    pixels of ``imagefile`` with the text ``message`` centered. The resulting
    image is saved to ``outfile``. Note: both input and output files assumed to
    be of JPEG format.
    """
    image = Image.open(imagefile)
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_NAME, FONT_SIZE)
    text_w, text_h = draw.textsize(message, font=font)
    draw.rectangle([(0, height-40), (width, height)], fill="#000000")
    draw.text(((width - text_w) / 2, height-20), message, font=font, fill="#DDDDDD")
    image.save(outfile, "JPEG", quality=95)


##############################################################################
# The End.
##############################################################################
