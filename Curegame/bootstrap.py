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

import os, sys
import platform
import shutil
import logging
import logging.handlers
import tempfile

_log = logging.getLogger('bootstrap')


###########################################################################
# Detect code modification (for automatic restarts).
###########################################################################

import __builtin__

# NOTE: We will introduce a new builtin called code_changed() which
# points the the function below. Bad pratice? Probably. But simplicity
# always wins over elegant design and more lines of code!

_import  = __builtin__.__import__
_modules = {}

def _addimport(filename):
    """
    Record module import of ``filename`` excluding it if it's from
    Python standard library (including site-packages).
    """
    if filename.endswith('.pyc') or filename.endswith('.pyo'):
        filename = filename[:-1]
    try:
        if "python" not in filename and filename not in _modules:
            _modules[filename] = os.stat(filename).st_mtime
    except OSError:
        pass

def _newimport(name, globals={}, locals={}, fromlist=[], level=-1):
    """
    Replace from the builtin import statement, records (filename,
    mtime) for each loaded module so that we later on can track if the
    module has been modified on disk.
    """
    mod = _import(name, globals, locals, fromlist, level)
    if mod and '__file__' in mod.__dict__:
        try:
            _addimport(mod.__file__)
        except AttributeError:
            pass
    return mod

def _code_changed():
    """
    Iterrate over the monitored modules and check for file
    modifications. To safeguard ourselves from someone else replacing
    or overriden import callback we'll monitor the system modules list
    just in case. Returns True if one of the loaded modules has
    been modified or False if the code is up to date.
    """
    try:
        modules = _modules.copy()
    except:
        modules = {}
    for (filename, prev_mtime) in modules.iteritems():
        try:
            curr_mtime = os.stat(filename).st_mtime
            if curr_mtime != prev_mtime:
                logging.info("Modified: %s" % filename)
                return True
        except OSError:
            continue
    for mod in sys.modules.copy().itervalues():
        try:
            _addimport(mod.__file__)
        except AttributeError:
            pass
    return False


# Detecting code changes dynamically only makes sense to use in a
# developer environment. Since we don't intend to ship code (*.py)
# to customers anyway we'll only use this feature in debug mode.
if os.environ.get("CUREGAME_OPT_DEBUG", None):
  __builtin__.__import__   = _newimport
  __builtin__.code_changed = _code_changed
else:
  __builtin__.code_changed = lambda:False


###########################################################################
# Bootstrap PCMS server system.
###########################################################################

def setup_server(rootdir, logname="server.log"):
    """
    Setup Python runtime environment for running PCMS HTTP/AMF server. It is
    assummed that ``rootdir`` at least contains the 'modules' and 'media'
    folders from the main distribution.
    """
    # Configure Python and setup module search path. Forcefully prepend our
    # path to make sure that existing installation don't take precedence.
    path = os.path.join(rootdir, "modules")
    os.environ["PYTHONPATH"] = path
    sys.path = [path] + sys.path

    # Make VRS intallation rootdir accesable via environment variables.
    os.environ["CUREGAME_ROOT"] = rootdir

    # Setup data storage path, normally we don't care in a real server
    # environment (cwd is perfectly fine) but in standalone mode we need to
    # store everything a single directory hierarchy and/or handle external
    # USB-storage situations etc.
    if platform.system() == "Windows":
        # Include our own custom binaries (Python extensions, etc) on the global
        # search path so that DLL are properly located.
        binpath = os.path.join(rootdir, "bin")
        if os.path.isdir(binpath):
            os.environ["PATH"] += ";" + binpath
        else:
            raise RuntimeError("Could not locate binaries directory")

        # To keep data easily accessable for end-users for backup and restoration
        # purposess we'll default to use the documents folder for storage. In-case
        # of an authenticated USB memory-stick being attached to the computer we'll
        # use that storage instead as the root of a fake documents folder.
        import winpaths, win32util
        for drivepath in win32util.list_flashdrives():
            if os.path.exists(os.path.join(drivepath, "vrs.storage")):
                docdir = drivepath
                break
        else:
            docdir = winpaths.getpath(winpaths.CSIDL_MYDOCUMENTS)

        datadir = os.path.join(docdir, "Curictus\\VRS")
        if not os.path.isdir(datadir): os.makedirs(datadir)
        os.environ["CUREGAME_DATA"] = datadir

        datadir = os.path.join(os.environ["CUREGAME_DATA"], "Temp")
        if not os.path.isdir(datadir): os.makedirs(datadir)
        os.environ["CUREGAME_TEMPPATH"] = datadir

        logpath = os.path.join(os.environ["CUREGAME_DATA"], "Logs\\")
        if not os.path.isdir(logpath): os.makedirs(logpath)
        os.environ["CUREGAME_LOGPATH"] = logpath
    else:
        os.environ["CUREGAME_DATA"] = rootdir
        os.environ["CUREGAME_TEMPPATH"] = rootdir
        os.environ["CUREGAME_LOGPATH"] = rootdir

    # Setup system-wide logging facilities and configure so that log data is
    # saved in reasonable way since the system is designed to be running for
    # long periods.
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    filelogger = logging.handlers.RotatingFileHandler(
        os.path.join(os.environ["CUREGAME_LOGPATH"], logname),
        maxBytes=512*1024, backupCount=10)
    filelogger.setFormatter(logging.Formatter("%(asctime)s : %(message)s"))
    logging.getLogger().addHandler(filelogger)


###########################################################################
# Bootstrap VRS client system.
###########################################################################

def setup(rootdir, logname="vrs.log"):
    """
    Setup a Python + H3D API environment for running Curegame activities. It
    assumed that ``rootdir`` contains both the Python distribution and H3D as
    well the internal 'modules' directory containing support code. Note:
    ``rootdir`` need to be a fully qualified path, relative paths were most
    certainely cause issues! To control how logfiles are named in the
    'CUREGAME_DATA' folder you can optionally use the ``logname`` paratemer and
    provide a custom base name.
    """
    # Configure Python and setup module search path. Forcefully prepend our
    # path to make sure that existing installation don't take precedence.
    pypath = os.path.join(rootdir, "python")
    if os.path.isdir(pypath):
        os.environ["PATH"] =  pypath + ";" + os.environ["PATH"]
    else:
        raise RuntimeError("Could not locate Python binaries directory")

    # Forccefully take over Python environment configuration.
    os.environ["PYTHONHOME"] = pypath
    path = os.path.join(rootdir, "modules")
    os.environ["PYTHONPATH"] = path
    sys.path = [path] + sys.path

    # Include our own custom binaries (Python extensions, etc) on the global
    # search path so that DLL are properly located.
    binpath = os.path.join(rootdir, "bin")
    if os.path.isdir(binpath):
        os.environ["PATH"] += ";" + binpath
    else:
        raise RuntimeError("Could not locate binaries directory")

    # Make sure H3D API binaries are available on the executable search path
    # (H3DLoad.exe as well thirdparty DLL's). H3D also requires a couple of
    # environment variables in order to configure it self which we need to take
    # care of as well.
    h3dbin = os.path.join(rootdir, "h3d\\bin")
    if os.path.isdir(h3dbin):
        os.environ["PATH"] += ";" + h3dbin
    else:
        raise RuntimeError("Could not locate H3DAPI directory")

    h3dbin = os.path.join(rootdir, "h3d\\external\\bin")
    if os.path.isdir(h3dbin):
        os.environ["PATH"] += ";" + h3dbin
    else:
        raise RuntimeError("Could not locate H3DAPI directory")

    # Forcefully take over H3D enviroment variables
    os.environ["H3D_ROOT"] = os.path.join(rootdir, "h3d\\H3DAPI")
    os.environ["H3D_EXTERNAL"] = os.path.join(rootdir, "h3d\\external")

    # Forcefully take over root directory of VRS (curegame) containing 'boostrap.py'.
    os.environ["CUREGAME_ROOT"] = rootdir

    # To keep data easily accessable for end-users for backup and restoration
    # purposess we'll default to use the documents folder for storage. In-case
    # of an authenticated USB memory-stick being attached to the computer we'll
    # use that storage instead as the root of a fake documents folder.
    import winpaths, win32util
    for drivepath in win32util.list_flashdrives():
        if os.path.exists(os.path.join(drivepath, "vrs.storage")):
            docdir = drivepath
            break
    else:
        docdir = winpaths.getpath(winpaths.CSIDL_MYDOCUMENTS)
    datadir = os.path.join(docdir, "Curictus\\VRS")
    if not os.path.isdir(datadir): os.makedirs(datadir)
    os.environ["CUREGAME_DATA"] = datadir

    # In-progress session logs and other temporary data are saved to a single
    # location where they are picked up by a file system monitoring thread.
    if "CUREGAME_TEMPPATH" not in os.environ:
        datadir = os.path.join(os.environ["CUREGAME_DATA"], "Temp")
        if not os.path.isdir(datadir): os.makedirs(datadir)
        os.environ["CUREGAME_TEMPPATH"] = datadir

    # Synced session logs are moved to a backup location where the remain until
    # the user manually removes them. This allow us to keep a second backup of
    # the collected data on the stations themselves incase something goes wrong
    # with the main VRS server.
    if "CUREGAME_SESSIONLOG_PATH" not in os.environ:
        datadir = os.path.join(os.environ["CUREGAME_DATA"], "Session")
        if not os.path.isdir(datadir): os.makedirs(datadir)
        os.environ["CUREGAME_SESSIONLOG_PATH"] = datadir

    # A session log is created by instructing our custom H3D loader to save
    # haptic device data to a XML logfile. The Python side responsible for game
    # logic is also instructed to save it's session events to a special XML
    # logfile as well which is merged with the device data log when the X3D
    # sessions ends (handled by the loader which launches game sessions).
    if "H3D_DEVICELOG_FILENAME" not in os.environ:
        logfile = os.path.join(os.environ["CUREGAME_TEMPPATH"], "session.tmp")
        os.environ["H3D_DEVICELOG_FILENAME"] = logfile

    if "CUREGAME_EVENTLOG_FILENAME" not in os.environ:
        logfile = os.path.join(os.environ["CUREGAME_TEMPPATH"], "gamedata.tmp")
        os.environ["CUREGAME_EVENTLOG_FILENAME"] = logfile

    # HGT config (user) data is passed from the VRS manager by serializing it
    # to a temporary file. We do this make sure that the GPL:ed HGT code and
    # the remaning code-base never touch each other. IPC/RPC mechanism aren't
    # suitable due to the need to be able to run HGT activities standalone
    # without having to launch the entire system.
    if "CUREGAME_HGT_CONFIG_FILENAME" not in os.environ:
        config_file = os.path.join(os.environ["CUREGAME_TEMPPATH"], "hgtgame.cfg")
        os.environ["CUREGAME_HGT_CONFIG_FILENAME"] = config_file

    # Global debug flag which isn't controllable by the end-users but
    # useful to modify during development is handled via the following
    # environment variable.
    if "CUREGAME_OPT_DEBUG" not in os.environ:
        os.environ["CUREGAME_OPT_DEBUG"] = "0"

    # Reset H3D redirection of standard handles.
    sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__

    # Setup system-wide logging facilities and configure so that log data is
    # saved in reasonable way since the system is designed to be running for
    # long periods.
    if "CUREGAME_LOGPATH" not in os.environ:
        logpath = os.path.join(os.environ["CUREGAME_DATA"], "Logs\\")
        os.environ["CUREGAME_LOGPATH"] = logpath
    else:
        logpath = os.environ["CUREGAME_LOGPATH"]
    if not os.path.isdir(logpath):
        os.makedirs(logpath)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler())
    filelogger = logging.handlers.RotatingFileHandler(
        os.path.join(os.environ["CUREGAME_LOGPATH"], logname),
        maxBytes=512*1024, backupCount=10)
    filelogger.setFormatter(logging.Formatter("%(asctime)s : %(message)s"))
    logging.getLogger().addHandler(filelogger)

    # Release builds of our custom H3D Loader (vrs.exe) supports redirection of
    # error messages and writing "minidumps" to a custom folder via the
    # 'DebugTools' library. We'll setup everything so that both the logs and
    # minidumps are saved to the VRS data folder for easy inspection when we
    # have to investigate issues remotely or on site.
    if "H3D_DEBUGTOOLS_FILENAME" not in os.environ:
        os.environ["H3D_DEBUGTOOLS_FILENAME"] = os.path.join(logpath, "h3d.log")
    if "H3D_DEBUGTOOLS_MINIDUMP_PATH" not in os.environ:
        os.environ["H3D_DEBUGTOOLS_MINIDUMP_PATH"] = os.environ["CUREGAME_TEMPPATH"]
    try:
        # Reset H3D log files after they exceed a reasonable file size limit.
        filename = os.environ["H3D_DEBUGTOOLS_FILENAME"]
        if os.path.isfile(filename) and os.path.getsize(filename) > (2*1024*1024):
            os.remove(filename)
    except (IOError, WindowsError, OSError):
        logging.exception("Unhandled exception while checking h3d.log")


###########################################################################
# Install/Uninstall Curegame (VRS) package.
###########################################################################

# Note: The application data folder is only removed when a complete uninstall
# is performed (i.e. uninstall is passed removedata=True). The separation of
# application data and other non-critical modification to the system which can
# easily be reversed (creating shortcuts, etc...) allows for much greater
# flexibility when upgrading to newer versions.

def install():
    import winpaths, win32util
    assert win32util.is_admin()
    rootdir = os.path.abspath(os.getcwd())
    startup = winpaths.getpath(winpaths.CSIDL_COMMON_STARTUP)
    # NOTE: to be able to tell if VRS was launched manually or automatically
    # (scheduled or via the startup folder) we'll pass a simple command-line
    # argument as a kind of metadata which VRS can look for. This is not done
    # for the sake of of cleverness but rather as a work-around since we don't
    # have access to the VRS configuration during the bootstrap phase. Feature
    # flags which for example modify startup behaviour need to know how the
    # system started since their code-paths won't be executed until later on
    # when VRS is fully bootstrapped.
    win32util.createshortcut(
        os.path.join(rootdir, "python\\pythonw.exe"),
        os.path.join(startup, "Curictus VRS.lnk"),
        args=os.path.join(rootdir, "bootstrap.py") + " /autostart",
        tooltip="Launch Curictus VRS",
        workdir=rootdir,
        iconpath=os.path.join(rootdir, "media\\icons\\curegame.ico"))
    desktop = winpaths.getpath(winpaths.CSIDL_DESKTOPDIRECTORY)
    win32util.createshortcut(
        os.path.join(rootdir, "python\\pythonw.exe"),
        os.path.join(desktop, "Curictus VRS.lnk"),
        args=os.path.join(rootdir, "bootstrap.py"),
        tooltip="Launch Curictus VRS",
        workdir=rootdir,
        iconpath=os.path.join(rootdir, "media\\icons\\curegame.ico"))
    win32util.createurlshortcut(
        "http://www.curictus.com",
        os.path.join(desktop, "Curictus PCMS.url"),
        iconpath=os.path.join(rootdir, "media\\icons\\curegame.ico"))
    win32util.createshortcut(
        os.environ["CUREGAME_DATA"],
        os.path.join(desktop, "Curictus VRS Data.lnk"))
    sendto = winpaths.getpath(winpaths.CSIDL_SENDTO)
    win32util.createshortcut(
        os.path.join(rootdir, "bin\\h3dload.bat"),
        os.path.join(sendto, "VRS (H3D).lnk"),
        iconpath=os.path.join(rootdir, "media\\icons\\curegame.ico"))
    win32util.createshortcut(
        os.path.join(rootdir, "bin\\vrs_debug.bat"),
        os.path.join(sendto, "VRS (Debug).lnk"),
        iconpath=os.path.join(rootdir, "media\\icons\\curegame.ico"))
    win32util.createshortcut(
        os.path.join(rootdir, "bin\\vrs.bat"),
        os.path.join(sendto, "VRS (Fullscreen).lnk"),
        iconpath=os.path.join(rootdir, "media\\icons\\curegame.ico"))
    fontdir = os.path.join(rootdir, "media\\fonts")
    for filename in os.listdir(fontdir):
        if (filename.endswith(".ttf") or filename.endswith(".otf")):
            fontfile = os.path.join(fontdir, filename)
            win32util.installfont(fontfile)
    # Disable Flash auto-update (http://kb2.adobe.com/cps/167/16701594.html)
    open("C:\\Windows\\SysWOW64\\mms.cfg", "wt")\
        .write(unicode("AutoUpdateDisable=1").encode("utf-8"))


def uninstall(removedata=False):
    _log.info("Uninstalling Curictus VRS")
    import winpaths, win32util
    assert win32util.is_admin()
    desktop = winpaths.getpath(winpaths.CSIDL_DESKTOPDIRECTORY)
    sendto = winpaths.getpath(winpaths.CSIDL_SENDTO)
    startup = winpaths.getpath(winpaths.CSIDL_COMMON_STARTUP)
    shortcut = os.path.join(startup, "Curictus VRS.lnk")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    shortcut = os.path.join(desktop, "Curictus VRS.lnk")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    shortcut = os.path.join(desktop, "Curictus PCMS.url")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    shortcut = os.path.join(desktop, "Curictus VRS Data.lnk")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    shortcut = os.path.join(sendto, "VRS (H3D).lnk")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    shortcut = os.path.join(sendto, "VRS (Debug).lnk")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    shortcut = os.path.join(sendto, "VRS (Fullscreen).lnk")
    if os.path.exists(shortcut):
        os.remove(shortcut)
    fontdir = os.path.join(rootdir, "media\\fonts")
    for filename in os.listdir(fontdir):
        if (filename.endswith(".ttf") or filename.endswith(".otf")):
            fontfile = os.path.join(fontdir, filename)
            win32util.removefont(fontfile)
    mms_cfg = "C:\\Windows\\SysWOW64\\mms.cfg"
    if os.path.exists(mms_cfg):
        os.remove(mms_cfg)
    if removedata:
        logging.shutdown()
        datadir = os.environ["CUREGAME_DATA"]
        if os.path.exists(datadir):
            shutil.rmtree(datadir)


###########################################################################
# Error reporting in a GUI environment without a console.
###########################################################################

ERROR_MSG = u"""
Sorry, something went very wrong!

An error report has been sent by email to the support team. They will
investigate the matter and contact you to resolve the issue if needed.

Stacktrace:
"""

MB_OK            = 0x00000000
MB_ICONHAND      = 0x00000010
MB_SYSTEMMODAL   = 0x00001000
MB_SETFOREGROUND = 0x00010000

def showerrormsg():
    import traceback
    stacktrace = traceback.format_exc()

    try:
        import win32util
        win32util.rotatedisplay(False)
    except:
        pass

    import ctypes
    ctypes.windll.user32.ShowCursor(1)
    ctypes.windll.user32.MessageBoxW(0,
        ERROR_MSG +  stacktrace,
        u"VRS Fatal Error",
        MB_OK|MB_ICONHAND|MB_SYSTEMMODAL|MB_SETFOREGROUND)


###########################################################################
# VRS entry-point.
###########################################################################

# Release versions of the system will use the pythonw.exe interpreter which
# doesn't have a console attached to it for display output to stdout/stderr
# since we want run the system in fullscreen showing only the graphics output.
noconsole = sys.executable.lower().endswith("pythonw.exe")

if __name__ == '__main__':
    try:
        rootdir = os.path.abspath(sys.path[0])

        os.chdir(rootdir)

        # Parse an optional command verb from command-line which is the first
        # non-slash-prexfied argument, ex: bootstrap.py verb /arg1 /arg2
        if len(sys.argv) > 1 and (sys.argv[1][:1] != '/'):
            command = sys.argv[1]
        else:
            command = None

        # (1) Run standalone PCMS HTTP/AMF server.

        if command == "server":
            setup_server(rootdir, "server.log")
            import vrs.server
            vrs.server.main(rootdir)
            sys.exit(0)

        # (2) Run standalone shell for inspecting server DB.

        if command == "dbshell":
            setup_server(rootdir, "dbshell.log")
            from vrs.server import dbshell
            dbshell.main(rootdir)
            sys.exit(0)


        # (3) Run as part of client VRS installation.

        setup(rootdir, "vrs.log")

        if command:
            if command == "install":
                install()
            elif command == "uninstall":
                uninstall()
            elif command == "sync":
                import vrs.client.sync as vrssync
                vrssync.main()
            elif command == "test_unit":
                import unittest
                suite = unittest.TestSuite([
                        unittest.TestLoader().discover(os.path.join(rootdir, "tests/unit_hgt")),
                        unittest.TestLoader().discover(os.path.join(rootdir, "tests/unit_vrs"))
                        ])
                unittest.TextTestRunner(verbosity=2).run(suite)
            elif command == "test_func":
                import unittest
                suite = unittest.TestSuite([
                        unittest.TestLoader().discover(os.path.join(rootdir, "tests/func_hgt")),
                        unittest.TestLoader().discover(os.path.join(rootdir, "tests/func_vrs"))
                        ])
                unittest.TextTestRunner(verbosity=2).run(suite)
            elif command == "exec":
                execfile(sys.argv[2])
            elif command == "shell":
                try:
                    import code
                    code.interact(local=locals())
                except:
                    pass
            else:
                raise RuntimeError("Unknown bootstrap command: %s" % command)
        else:
            import vrs.client.manager as vrsmanager
            vrsmanager.main()

    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logging.exception("Caught unhandled exception")
        if noconsole:
            showerrormsg()


###########################################################################
# The End.
###########################################################################
