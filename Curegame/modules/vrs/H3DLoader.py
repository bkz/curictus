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

import logging
import os
import subprocess
import sys
import time

import metrics
import resetbutton
import win32util

_log = logging.getLogger('h3dload')

# Game exited normally
EXIT_NORMAL = 0

# Fatal error caused premature exit
EXIT_ERROR  = 1

# User forcefully exited game
EXIT_FORCED = 2

# Title of the H3D viewer main window.
WINDOW_NAME = "H3D"

# Default version which ships as part of H3D API.
DEFAULT_H3DLOAD_EXECUTABLE = "h3dload.exe"

# Release version which runs in fullscreen.
CUSTOM_H3DLOAD_EXECUTABLE = "vrs.exe"

# Development version which runs in windowed mode with a console window.
CUSTOM_H3DLOAD_DEBUG_EXECUTABLE = "vrs_debug.exe"

# Kill of zombie processes after this time limit (i.e. user left station
# without exiting or similar situations).
MAX_SESSION_LENGTH_SECS = 30 * 60

###########################################################################
# BaseH3DLoader
###########################################################################

class BaseH3DLoader(object):
    def __init__(self, exepath, hideconsole=False, env=None):
        self.exepath, self.hideconsole, self.env = exepath, hideconsole, env


    def run(self, x3dfile, fullscreen=True, mirror=True, stereo=True):
        args = [self.exepath]
        if fullscreen:
            args.append("--fullscreen")
        else:
            args.append("--no-fullscreen")
        if mirror:
            args.append("--mirror")
        else:
            args.append("--no-mirror")
        if stereo:
            args.append("--rendermode=QUAD_BUFFERED_STEREO")
        else:
            args.append("--rendermode=MONO")
        args.append(x3dfile)
        try:
            # We need to re-rotate the display since H3D assumes that
            # monitor isn't physically rotated as it is in the VRS
            # hardware setup. What we basically want to end up with is
            # to have start menu rotated so that it is the bottom of
            # the screen. During normal VRS execution we keep the
            # screen un-rotated, i.e. the start menu is at the top of
            # the screen since the monitor is mounted up-side-down.
            if fullscreen and mirror:
                win32util.rotatedisplay(False)
            if fullscreen:
                win32util.hidecursor()

            retcode = self._launch(args, hidemouse=fullscreen)

            if retcode == EXIT_NORMAL:
                metrics.track("h3d", {"exitcode" : "normal"})
            elif retcode == EXIT_FORCED:
                metrics.track("h3d", {"exitcode" : "forced"})
            elif retcode == EXIT_ERROR:
                metrics.track("h3d", {"exitcode" : "error"})

            return retcode
        finally:
            if fullscreen and mirror:
                win32util.rotatedisplay(True)
            if fullscreen:
                win32util.hidecursor()


    def _launch(self, args, hidemouse=False):
        """
        Execute H3D loader process and watch it's exit code to
        determine the status of session. If the global reset button is
        triggered attempt to shutdow the session gracefully and if
        needed forcefully terminate the process. If we are dealing with
        a process which automatically centers the mouse cursor after
        startup, set ``hidemouse`` to forcefully hide the cursor every
        second or so until the process exits. Returns either EXIT_NORMAL,
        EXIT_FORCED or EXIT_ERROR.
        """
        starttime = time.time()
        _log.info("Launching H3D scene: %s" % args)
        # This trick was lifted from runemacs.exe, hide all windows at startup,
        # the process itself will always use ShowWindow() to display it main
        # window. Result? Console window gets hidden, application main window
        # shows up just like expected.
        if self.hideconsole:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        else:
            startupinfo = None
        # This is a workaround for dealing with pythonw.exe or other situation
        # where sys.stdout/stderr has been redirecited to a non file-descriptor
        # based object. On windows an attepmpt to duplicate the handled will be
        # made which for obvious reasons will fail and cause an exception.
        if self._isrealfile(sys.stdout) and self._isrealfile(sys.stderr):
            proc = subprocess.Popen(args, stdout=sys.stdout, stderr=sys.stderr, startupinfo=startupinfo, env=self.env)
        else:
            proc = subprocess.Popen(args, startupinfo=startupinfo, env=self.env)
        # Wait for process to finish but keep an eye out if user wants
        # to forcefully end this session.
        while proc.poll() == None:
            if hidemouse:
                win32util.hidecursor()
            time.sleep(0.5)
            if win32util.is_hung(WINDOW_NAME):
                _log.error("Forcefully terminating unresponsive H3D process")
                win32util.kill(proc)
                _log.info("Exit due to error (1)")
                return EXIT_ERROR
            if (time.time() - starttime) > MAX_SESSION_LENGTH_SECS:
                _log.info("Forcefully terminating long-running H3D process")
                win32util.kill(proc)
                _log.info("Exit due to timeout (1)")
                return EXIT_ERROR
            if resetbutton.is_down():
                _log.info("Got H3D shutdown request via reset button")
                if self._shutdown(proc):
                    _log.info("Manual forced exit via reset button (2)")
                    return EXIT_FORCED
                else:
                    _log.info("Exit due to error (1)")
                    return EXIT_ERROR
        exitcode = proc.returncode
        if exitcode == EXIT_NORMAL:
            _log.info("Normal exit (0)")
        elif exitcode == EXIT_ERROR:
            _log.info("Error exit (1)")
        elif exitcode == EXIT_FORCED:
            _log.info("Manual forced exit (2)")
        else:
            _log.warning("Unknown H3D exitcode (%d)" % exitcode)
            # Fix: sometimes we'll get corrupt exit-codes from H3DLoad even
            # though the session exits cleanly via HGT quit(). This only occurs
            # when we use our custom H3DHapticsDeviceStats node,
            # i.e. assessments so we'll use a temporary work-around and treat
            # errors as normal exits. Corrupt/aborted sessions will be handled
            # by VRS anyhow so we'll be fine until we find the real cause.
            exitcode = EXIT_NORMAL
        return exitcode


    def _isrealfile(self, stream):
        """Check if stream has a valid file handle or not."""
        if not hasattr(stream, 'fileno'):
            return False
        try:
            tmp = os.dup(stream.fileno())
        except:
            return False
        else:
            os.close(tmp)
        return True


    def _shutdown(self, proc):
        """
        Attempt to gracefully shutdown a H3D session or if needed
        forcefully terminate the process.
        """
        win32util.closewindow(WINDOW_NAME)
        for attempt in range(10):
            if proc.poll() == None:
                time.sleep(1)
            else:
                break
        if proc.poll() == None:
            _log.error("Forcefully terminating H3D process")
            win32util.kill(proc)
            return False
        return True


###########################################################################
# DefaultH3DLoader
###########################################################################

class DefaultH3DLoader(BaseH3DLoader):
    def __init__(self, debug=False):
        super(DefaultH3DLoader, self).__init__(DEFAULT_H3DLOAD_EXECUTABLE, hideconsole=(not debug))


###########################################################################
# CustomH3DLoader
###########################################################################

class CustomH3DLoader(BaseH3DLoader):
    def __init__(self, debug=False):
        if debug:
            exepath = CUSTOM_H3DLOAD_DEBUG_EXECUTABLE
        else:
            exepath = CUSTOM_H3DLOAD_EXECUTABLE
        super(CustomH3DLoader, self).__init__(exepath)


###########################################################################
# The End.
###########################################################################
