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
import shutil
import string
import subprocess
import sys
import time
import _winreg

from ctypes import *
from ctypes import wintypes

import win32def

_log = logging.getLogger('win32util')

###########################################################################
# Win32 API wrappers.
###########################################################################

AddFontResourceW = windll.gdi32.AddFontResourceW
AddFontResourceW.argtypes = [c_wchar_p]

RemoveFontResourceW = windll.gdi32.RemoveFontResourceW
RemoveFontResourceW.argtypes = [c_wchar_p]

SendMessage = windll.user32.SendMessageW
SendMessage.restype = wintypes.LONG
SendMessage.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM]

SendMessageTimeout = windll.user32.SendMessageTimeoutW
SendMessageTimeout.restype = wintypes.LONG
SendMessageTimeout.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    c_voidp]

PostMessage = windll.user32.PostMessageW
PostMessage.restype = wintypes.BOOL
PostMessage.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM]

GetAsyncKeyState = windll.user32.GetAsyncKeyState
GetAsyncKeyState.restype = wintypes.WORD
GetAsyncKeyState.argtypes = [c_int]

###########################################################################
# Win32 helper DLL wrappers.
###########################################################################

_createshortcut = CDLL("win32util.dll").createshortcut
_createshortcut.restype = c_int
_createshortcut.argtypes = [
    c_wchar_p, # source
    c_wchar_p, # destination
    c_wchar_p, # working_dir
    c_wchar_p, # arguments
    c_wchar_p, # description
    c_wchar_p, # icon
    c_int]     # icon_index

_setdesktopcolor = CDLL("win32util.dll").setdesktopcolor
_setdesktopcolor.restype = c_int
_setdesktopcolor.argtypes = [
    c_int, # R
    c_int, # G
    c_int] # B

_setdesktopimage = CDLL("win32util.dll").setdesktopimage
_setdesktopimage.restype = c_int
_setdesktopimage.argtypes = [
    c_wchar_p] # filepath

_setgamma = CDLL("win32util.dll").setgamma
_setgamma.restype = c_int
_setgamma.argtypes = [
    c_int] # G

_minimizewindows = CDLL("win32util.dll").minimizewindows
_minimizewindows.restype = c_int
_minimizewindows.argtypes = []

_rotatedisplay = CDLL("win32util.dll").rotatedisplay
_rotatedisplay.restype = c_int
_rotatedisplay.argtypes = [
    c_int] # rotate

_isusbdrive = CDLL("win32util.dll").isusbdrive
_isusbdrive.restype = c_int
_isusbdrive.argtypes = [c_char] # drive

_isadmin = CDLL("win32util.dll").isadmin
_isadmin.restype = c_int
_isadmin.argtypes = []

_runasdesktop = CDLL("win32util.dll").runasdesktop
_runasdesktop.restype = c_int
_runasdesktop.argtypes = [
    c_wchar_p, # full path to program
    c_wchar_p, # command line args
    c_wchar_p] # working directory

_checksignal = CDLL("win32util.dll").checksignal
_checksignal.restype = c_int
_checksignal.argtypes = [
    c_wchar_p] # signal (mutex) name

_setsignal = CDLL("win32util.dll").setsignal
_setsignal.restype = c_int
_setsignal.argtypes = [
    c_wchar_p] # signal (mutex) name


###########################################################################
# Utilities.
###########################################################################

def _registerfont(filepath):
    """
    Register ``filepath`` font with Windows registry. Note: ``filepath`` must
    point to a font which has been copied to the %WINDIR%\\Fonts folder.
    """
    fontfile = os.path.split(filepath)[1]
    value_name = os.path.splitext(fontfile)[0] + " (True Type)"
    value_data = fontfile
    fonts = _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts")
    try:
        _winreg.QueryValueEx(fonts, value_name)
    except WindowsError:
        _log.debug("Adding to registry '%s'" % value_name)
        _winreg.SetValueEx(fonts, value_name, 0, _winreg.REG_SZ, value_data)
    finally:
        _winreg.CloseKey(fonts)


def _unregisterfont(filepath):
    """
    Unregister font resource ``filepath`` from Windows registry.
    """
    fontfile = os.path.split(filepath)[1]
    value_name = os.path.splitext(fontfile)[0] + " (True Type)"
    fonts = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts", 0, _winreg.KEY_ALL_ACCESS)
    try:
        _winreg.QueryValueEx(fonts, value_name)
        _log.debug("Deleting from registry '%s'" % value_name)
        _winreg.DeleteValue(fonts, value_name)
    except WindowsError:
        pass
    finally:
        _winreg.CloseKey(fonts)


###########################################################################
# Module public interfance.
###########################################################################

def hidedesktop():
    """
    Hide the Window Desktop for the current user.
    """
    _minimizewindows()
    showdesktop(False)


def showdesktop(show=True):
    """
    Show or hide the Window Desktop for the current user.
    """
    cmd = win32def.SW_SHOW if show else win32def.SW_HIDE
    wndclasses = ["progman", "shell_traywnd", "button"]
    for wndclass in wndclasses:
        hwnd = windll.user32.FindWindowA(c_char_p(wndclass), c_char_p(win32def.NULL))
        windll.user32.ShowWindow(c_int(hwnd), c_int(cmd))


def sharefocus(pid):
    """
    Allow application ``pid`` to steal focus from us. This is used to give away
    the current focus to a different application which has not been launched or
    in away interacted with the user yet as Windows will only focus to flow
    from one process to another under to those circumstances.
    """
    windll.user32.AllowSetForegroundWindow(c_int(pid))


def showcursor():
    """
    Show the mouse cursor and reposition it in the top-left corner.
    """
    windll.user32.ShowCursor(win32def.TRUE)
    w = windll.user32.GetSystemMetrics(c_int(win32def.SM_CXSCREEN))
    h = windll.user32.GetSystemMetrics(c_int(win32def.SM_CYSCREEN))
    windll.user32.SetCursorPos(c_int(w/2), c_int(h/2))


def hidecursor():
    """
    Hide the mouse cursor for the current application.
    """
    w = windll.user32.GetSystemMetrics(c_int(win32def.SM_CXSCREEN))
    h = windll.user32.GetSystemMetrics(c_int(win32def.SM_CYSCREEN))
    windll.user32.SetCursorPos(c_int(w), c_int(h/2))
    while windll.user32.ShowCursor(win32def.FALSE) >= 0:
        pass


def createshortcut(source, destination, workdir=None, args=None, tooltip=None, iconpath=None, iconindex=0):
    """
    Create a shortcut link to launch the executable or script ``source``. The
    shortcut will be saved to ``destination`` which should be a fully qualified
    path to a .lnk file (ex: C:\Users\Default\Desktop\Hello World.lnk). One can
    optionally specify a ``workdir`` and additional ``args`` (whitespace
    delimited string) needed to launch the application. A descriptive
    ``tooltip`` can also be set which the user is shown when he/she hovers over
    the shortcut. Custom icons be assigned using a combination of ``iconpath``
    which points to the .ico file and ``iconindex`` can be set if the .ico
    contains more than one icon. Returns True if short was successfully
    created. (Hint: To create a shortcut to launch a Python script set the
    source to the Python interpreter and pass the script an argument while also
    setting a correct working directory if needed.)
    """
    if not os.path.exists(source):
        raise RuntimeError("Missing source for shortcur link: %s" % source)
    if not destination.endswith(".lnk"):
        raise RuntimeError("Malformed shortcut link: %s" % destination)
    linkpath = os.path.split(destination)[0]
    if not os.path.exists(linkpath):
        os.makedirs(linkpath)
    ret = _createshortcut(source, destination, workdir, args, tooltip, iconpath, iconindex)
    return (ret > 0) and os.path.exists(linkpath)


def createurlshortcut(url, destination, iconpath=None, iconindex=0):
    """
    Create a shortcut link which launch ``url`` using the default browser.  The
    shortcut will be saved to ``destination`` which should be a fully qualified
    path to a .url file (ex: C:\Users\Default\Desktop\Hello World.url). Returns
    True if short was successfully created.
    """
    if not destination.endswith(".url"):
        raise RuntimeError("Malformed shortcut link: %s" % destination)
    linkpath = os.path.split(destination)[0]
    if not os.path.exists(linkpath):
        os.makedirs(linkpath)
    try:
        open(destination, "wt").write("[InternetShortcut]\nURL=%s\n" % url)
        return True
    except IOError, OSError:
        return False


def setgamma(gamma):
    """
    Control display ``gamma`` ramp, a value of 128 is normal brightness, lower
    values equals darker screen (minimum values is 0).
    """
    return _setgamma(gamma)


def setdesktopimage(filepath):
    """
    Set desktop wallpaper of the current user to ``filepath``.
    """
    return _setdesktopimage(filepath)


def setdesktopcolor(r,g,b):
    """
    Disable the desktop wallpaper of the current user and replace it with a
    solid background from the color arguments.
    """
    return _setdesktopcolor(r,b,g)


def rotatedisplay(rotate):
    """
    Attempt to flip screen 180 degress but only if the screen has
    already been rotated in Windows, i.e. we want restore the screen
    rotation to match the physical rotation. (The display on the VRS
    station is mounted upside down and the desktop is rotated in
    Window, when running VRS we want un-rotate the desktop to use the
    mirror and co-location features of the hardware.)
    """
    return _rotatedisplay(rotate)


def installfont(filepath):
    """
    Register a font with the Windows font database.
    """
    fontdir = os.path.join(os.environ["WINDIR"], "Fonts\\")
    fontfile = os.path.join(fontdir, os.path.split(filepath)[1])
    if not os.path.exists(fontfile):
        shutil.copy(filepath, fontfile)
    _registerfont(fontfile)
    ret = AddFontResourceW(fontfile)
    if (ret > 0):
        PostMessage(win32def.HWND_BROADCAST, win32def.WM_FONTCHANGE, 0, 0)
    return (ret > 0)

def removefont(filepath):
    """
    Uninstall a font from the Windows font database.
    """
    fontdir = os.path.join(os.environ["WINDIR"], "Fonts\\")
    fontfile = os.path.join(fontdir, os.path.split(filepath)[1])
    _unregisterfont(fontfile)
    ret = RemoveFontResourceW(fontfile)
    try:
        if os.path.exists(fontfile):
            os.remove(fontfile)
    except WindowsError:
        pass # Ignore access denied errors.
    return (ret > 0)


def findwindow(title):
    """
    Return True if a window with ``title`` is active.
    """
    if windll.user32.FindWindowA(c_char_p(win32def.NULL), c_char_p(title)):
        return True
    else:
        return False

def closewindow(title,timeout=5):
    """
    Attempt to shutdown application which owns the window with
    ``title``. Returns True/False to signal if application was successfully
    shutdown before ``timeout`` seconds.
    """
    hwnd = windll.user32.FindWindowA(c_char_p(win32def.NULL), c_char_p(title))
    if hwnd:
        PostMessage(hwnd, win32def.WM_CLOSE, 0, 0)
    time.sleep(0.5)
    for n in range(timeout):
        if not windll.user32.FindWindowA(c_char_p(win32def.NULL), c_char_p(title)):
            return True
        time.sleep(1)
    return False


def kill(proc):
    """
    Forcefully terminate a subprocess.Popen() instance ``proc`` using
    low-level Win32 API. Note: this method is mainly for for 2.5
    compability, in 2.6+ use Popen.terminate().
    """
    try:
        try:
            return proc.terminate()
        except AttributeError:
            return windll.kernel32.TerminateProcess(int(proc._handle), 1)
    except WindowsError:
        return None # Swallow access denied errors.


def is_hung(title):
    """
    Returns True if a window with ``title`` is detected as unresponsive.
    """
    hwnd = windll.user32.FindWindowA(c_char_p(win32def.NULL), c_char_p(title))
    if hwnd:
        ret = SendMessageTimeout(hwnd, win32def.WM_NULL, 0, 0, win32def.SMTO_ABORTIFHUNG, 10*1000, None)
        return (ret == 0)
    else:
        return False


def safedelete(filepath):
    """
    Safely delete ``filepath``, if file can't be removed right away scheduled
    deletion for reboot/shutdown. Guaranteed to never raise any exception.
    """
    try:
        os.remove(filepath)
    except (OSError, IOError):
        _log.info("Schedule deletion of '%s' on reboot" % filepath)
        windll.kernel32.MoveFileExW(c_wchar_p(filepath), c_voidp(None), win32def.MOVEFILE_DELAY_UNTIL_REBOOT)


def shutdown(timeout=0, restart=False):
    """
    Forcefully shutdown Windows (and optionally ``restart``) without any UI or
    warnings, default ``timeout`` is 0 seconds but can be overriden if needed.
    """
    # Same trick as used in H3DLoader.py to hide the console window.
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
    # shutdown.exe arguments:
    #   /s     = shutdown local computer
    #   /r     = shutdown and restart local computer
    #   /f     = forcefully kill unresponsive processes if needed
    #   /t SEC = timeout limit before shutdown is initiated
    if restart:
        action = "/r"
    else:
        action = "/s"
    args = ["shutdown.exe", action, "/f", "/t", "%d" % timeout]
    subprocess.Popen(args, startupinfo=startupinfo).wait()


def isusbdrive(drive):
    """
    Returns true if ``drive`` (drive letter or path) points to USB storage.
    """
    return _isusbdrive(str(drive[0]))


def list_flashdrives():
    """
    Generate a list of all (removeable) flash drives currently mounted in the
    filesystem. Items are yielded in the following format: 'LETTER:\',
    i.e. 'E:\', 'F:\'.
    """
    for drive_letter in string.ascii_uppercase:
        if _isusbdrive(drive_letter):
            yield ("%s:\\" % drive_letter)


def is_keydown(vk):
    """
    Return True if the key matching the virtual key code ``vk`` (i.e VK_???
    from windef.py) is pressed.
    """
    return GetAsyncKeyState(vk) & 0x8000


def is_admin():
    """
    Returns True if process is running with admin privileges (UAC).
    """
    return _isadmin()


def runasdesktop(program, cmdline, workdir):
    """
    Launch ``program`` with ``cmdline`` in ``workdir`` as a normal non-elevated
    process (needed if parent process is elevated to drop admin-rights).

    NOTE: due to a bug Windows 7/Vista you cannot launch a console process from
    a non-console parent process. Either use an intermediate helper or do
    without stdout/stderr/stdin. See KB960266 on MSDN for more info.
    """
    return _runasdesktop(program, cmdline, workdir)


def checksignal(name):
    """
    Check if a global signal (mutex) ``name`` has been set by a process.
    """
    return _checksignal(name)


def setsignal(name):
    """
    Create a global signal (mutex) identified as ``name``.
    """
    return _setsignal(name)


###########################################################################
# The End.
###########################################################################
