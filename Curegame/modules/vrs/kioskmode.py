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

import time
from ctypes import *
import atexit
import win32util

###########################################################################
# Win32 helper DLL wrappers.
###########################################################################

_showscreen = CDLL("win32util.dll").showscreen
_showscreen.restype = c_int
_showscreen.argtypes = [
    c_wchar_p, # progress icon
    c_wchar_p, # main logo icon
    c_wchar_p, # status message
    c_wchar_p, # version string
    c_int]     # mirror Y

_setmessage = CDLL("win32util.dll").setmessage
_setmessage.restype = c_int
_setmessage.argtypes = [c_wchar_p] # status message

_hidescreen = CDLL("win32util.dll").hidescreen
_hidescreen.restype = c_int
_hidescreen.argtypes = []


###########################################################################
# Python API interface.
###########################################################################

_dirty = False

def enter(wallpaper=None):
    """
    Disable cursor, hide the desktop and start-menu and change wallpaper to a
    solid black background to simulate a fullscreen kioskmode.  Optionally a
    fully qualified filepath to a ``wallpaper`` can be passed which be set when
    the program exists. Normally this used to revert the desktop back to a
    default wallpaper with the company logo etc.
    """
    global _dirty
    _dirty = True
    win32util.setdesktopcolor(0,0,0)
    win32util.hidedesktop()
    win32util.rotatedisplay(True)
    win32util.hidecursor()
    atexit.register(restore, wallpaper)



def restore(wallpaper=None):
    """
    Leave kioskmode and reset the desktop on exit.
    """
    if _dirty:
        win32util.showcursor()
        win32util.setdesktopcolor(0,0,0)
        win32util.rotatedisplay(False)
        win32util.showdesktop()
        if wallpaper:
            win32util.setdesktopimage(wallpaper)


def showloader(progressIcon, logoIcon, message, version, mirror=True):
    """
    Display fullscreen progress information screen where ``progressIcon`` is a
    image which can be animated by rotating it 45 degrees each frame to render
    a Apple style progress indicator, ``logoIcon`` is drawn in the middle of
    the screen, ``message`` text is drawn at the bottom of the screen and
    ``version`` text in tiny font in the lower-right corner of the screen. If
    ``mirror`` is true the screen is flipped on it's Y-axis to make the end
    result suitable for display on a co-location setup where the user is shown
    output via a mirror. All of the image and text parameters are optional and
    if an empty value is passed that part of the progress screen is basically
    disabled.
    """
    return _showscreen(progressIcon, logoIcon, message, version, mirror)


def setmessage(s):
    """
    Update showloader() status message with new string ``s``.
    """
    return _setmessage(s)


def hideloader():
    """
    Hide (and destroy) the fullscreen progress display screen.
    """
    return _hidescreen()

###########################################################################
# The End.
###########################################################################
