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

import Queue
import gzip
import logging
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import winsound
import uuid

import win32util

from vrs import kioskmode
from vrs import imageutils
from vrs import phantominfo
from vrs import resetbutton
from vrs.util import singleinstance

from vrs import H3DLoader
from vrs import SessionLog

import vrs.client.sync as vrssync
from vrs.update import have_software_update


_log = logging.getLogger('vrs-manager')

DEBUG = (os.environ["CUREGAME_OPT_DEBUG"] == "1")

###########################################################################
# Dashboard HTTP service (HTTP/AMF server).
###########################################################################

import vrs.client

def start_http(config, jobqueue, db):
    vrs.client.start(config, jobqueue, db)

def stop_http():
    vrs.client.stop()


###########################################################################
# Background sync thread (data uploader).
###########################################################################

def start_dbsync(config, jobqueue, db):
    if config.FEATURES["enable_data_sync"]:
        vrssync.start(config, jobqueue, db)

def stop_dbsync():
    vrssync.stop()


###########################################################################
# Standalone client-server mode (run server in background).
###########################################################################

class ServerThread(threading.Thread):
    """
    Thread for running a (stoppable) VRS server process.
    """

    def __init__(self, rootdir):
        self.rootdir = rootdir
        self.stopevent = threading.Event()
        self.started = threading.Event()
        self.error = None
        super(ServerThread, self).__init__()


    def run(self):
        proc = None
        try:
            self.started.set()
            # Hide console window by requiring that child processes call
            # ShowWindow() which command-line application normallt don't do.
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            python_bin = os.path.join(self.rootdir, "python/python.exe")
            proc = subprocess.Popen([python_bin, "bootstrap.py", "server"],
                                 # stdout=subprocess.PIPE,
                                 # stderr=subprocess.PIPE,
                                 startupinfo=startupinfo)
            while proc.poll() == None:
                time.sleep(0.1)
                if self.stopevent.isSet():
                    win32util.kill(proc)
            _log.debug("Server process exit code: %s" % proc.returncode)
        except Exception, e:
            _log.exception("Unhandled exception")
            self.error = e
            self.started.set()
        finally:
            if proc and proc.poll() == None:
                _log.error("Forcefully killing server process (due to exception?)")
                win32util.kill(proc)


    def stop(self, timeout=None):
        self.stopevent.set()
        threading.Thread.join(self, timeout)


server_thread = None


def start_server(rootdir):
    """
    Start background VRS server process thread.
    """
    global server_thread
    server_thread = ServerThread(rootdir)
    server_thread.start()
    server_thread.started.wait()
    if server_thread.error:
        _log.warning("Caught exception in server process thread during startup")
        raise server_thread.error


def stop_server():
    """
    Stop background VRS server process thread.
    """
    global server_thread
    if server_thread:
        _log.info("Stopping server process thread")
        server_thread.stop()
        if server_thread.error:
            _log.warning("Caught exception in server process thread during shutdown")



###########################################################################
# Precache resources to improve loading times.
###########################################################################

import mmap
import threading

def force_precache(filename):
    """
    Force OS VM manager to cache ``filename`` by memory mapping and
    touching of all it's contents.
    """
    try:
        f = open(filename, "r+b")
        m = mmap.mmap(f.fileno(), 0)
        d = m.read(m.size())
        m.close()
        f.close()
    except (IOError, OSError), e:
        pass


def background_precache(datadirs, exts=[".jpg", ".png", ".wav", ".x3d", ".flv", ".dll"]):
    """
    Recursively traverse ``datadirs`` folder list and read in all files with
    matching ``exts`` to force the OS VM manager to cache the files. Doing so
    minimizes the chance of stuttering and other annoyances as resource access
    results in blocked I/O requests.
    """
    def worker():
        start = time.time()
        count = 0
        for datadir in datadirs:
            for (dirpath, dirnames, filenames) in os.walk(datadir):
                for filename in filenames:
                    if os.path.splitext(filename)[1] in exts:
                        force_precache(os.path.join(dirpath, filename))
                        count += 1
                        time.sleep(0)
        _log.info("Precached %d resources in %2.2f secs" % (count, time.time() - start))
    threading.Thread(target=worker).start()


###########################################################################
# Splashscreen and calibration/usage instructions.
###########################################################################

from vrs.locale import translate as _

def show_checkusbstorage(config):
    """
    Make sure $CUREGAME_DATA points to USB drive location, otherwise show a
    splashscreen informing user to connect a valid storage device and restart
    the computer after one is plugged in.

    NOTE: for on-site diagnostics the resetbutton will bypass restarting the
    computer and only result in a VRS shutdown.
    """
    if not win32util.isusbdrive(os.environ["CUREGAME_DATA"]):
        skip_restart = False
        kioskmode.enter()
        kioskmode.showloader(
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\ticker.png"),
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\usbdrive_connect.png"),
            _("Please turn on and connect the supplied USB flash drive."),
            "VRS %s" % config.SYSTEM_VERSION,
            config.H3D_MIRROR);
        try:
            while True:
                time.sleep(1)
                usb_drives = list(win32util.list_flashdrives())
                if usb_drives:
                    break
                if resetbutton.is_down():
                    skip_restart=True
                    break
        finally:
            winsound.PlaySound(os.path.join(os.environ["CUREGAME_ROOT"], "media\\sounds\\blop.wav"), winsound.SND_FILENAME)
            kioskmode.hideloader()
            kioskmode.restore()
            if not skip_restart:
                win32util.shutdown(restart=True)
            sys.exit(0)


def show_checkphantom(config, timeout=60):
    """
    Make sure Phantom is connected, if not show a help screen with instructions
    on how to re-attach cables etc. After ``timeout`` secs we will have no
    other choice but to raise an exception and force a system shutdown.
    """
    if not phantominfo.isConnected():
        kioskmode.showloader(
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\ticker.png"),
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\phantom_connect.png"),
            _("Please turn off computer and verify that cables are plugged in properly."),
            "VRS %s" % config.SYSTEM_VERSION,
            config.H3D_MIRROR);
        max_wait_timestamp = time.time() + timeout
        try:
            while not phantominfo.isConnected():
                time.sleep(1)
                if resetbutton.is_down():
                    break
                if time.time() > max_wait_timestamp:
                    raise RuntimeError("Phantom Omni not connected!")
        finally:
            winsound.PlaySound(os.path.join(os.environ["CUREGAME_ROOT"], "media\\sounds\\blop.wav"), winsound.SND_FILENAME)
            kioskmode.hideloader()


def show_recalibrate(config, abort_callback=None):
    """
    Force the user to insert haptic pen into into inkwell to
    re-calibrate the haptic device.

    An optional ``abort_callback`` with the signature f() -> bool can be
    passed. It is called once every second to check if we should abort the
    device polling loop and exit.

    If the calibration check was aborted we'll return False otherwise True
    which signals success.
    """
    if phantominfo.isConnected() and (not phantominfo.getInkwellState()):
        kioskmode.showloader(
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\ticker.png"),
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\phantom.png"),
            _("Please insert haptic pen into inkwell..."),
            "VRS %s" % config.SYSTEM_VERSION,
            config.H3D_MIRROR);
        try:
            while not phantominfo.getInkwellState():
                time.sleep(1)
                if abort_callback and abort_callback():
                    return False
                if resetbutton.is_down():
                    return False
        finally:
            winsound.PlaySound(os.path.join(os.environ["CUREGAME_ROOT"], "media\\sounds\\blop.wav"), winsound.SND_FILENAME)
            kioskmode.hideloader()
    return True


def show_instructions(config, abort_callback=None):
    """
    Instruct the user to lift the haptic pen from the inkwell and turn on the
    3D glasses.

    An optional ``abort_callback`` with the signature f() -> bool can be
    passed. It is called once every second to check if we should abort the
    device polling loop and exit.

    If the instructions screen was aborted we'll return False otherwise True
    which signals success.
    """
    if phantominfo.isConnected() and phantominfo.getInkwellState():
        kioskmode.showloader(
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\ticker.png"),
            os.path.join(os.environ["CUREGAME_ROOT"], "media\\loader\\instructions.png"),
            _("Turn on 3D glasses and lift pen from inkwell..."),
            "VRS %s" % config.SYSTEM_VERSION,
            config.H3D_MIRROR);
        try:
            while phantominfo.getInkwellState():
                time.sleep(1)
                if abort_callback and abort_callback():
                    return False
                if resetbutton.is_down():
                    return False
        finally:
            winsound.PlaySound(os.path.join(os.environ["CUREGAME_ROOT"], "media\\sounds\\blop.wav"), winsound.SND_FILENAME)
            kioskmode.hideloader()
    return True


###########################################################################
# Launch HGT training games and assessments.
###########################################################################

from vrs.config.activities import HGT_TESTS, HGT_GAMES

def get_kinematicslog():
    try:
        eventlog = os.environ["H3D_DEVICELOG_FILENAME"]
        data = open(eventlog, "rt").read()
        os.remove(eventlog)
        return data
    except IOError:
        return None

def get_activitylog():
    try:
        eventlog = os.environ["CUREGAME_EVENTLOG_FILENAME"]
        data = open(eventlog, "rt").read()
        os.remove(eventlog)
        return data
    except IOError:
        return None


def save_sessionlog(config, patient_alias, patient_guid, timestamp, duration, \
                        activity_name, activity_kind, activity_version, activity_guid):
    """
    Generate a XML session log for a test or training activity which
    optionally includes a activity log (CUREGAME_EVENTLOG_FILENAME)
    and a kinematics log (H3D_DEVICELOG_FILENAME). See docs for the
    SessionLog class for details on the XML format.

    NOTE: currently we only save kinematics logs for assessment!
    """
    session = SessionLog.SessionLog(config, patient_alias, patient_guid, timestamp, duration)
    session.set_hardware(phantominfo.getVersionInfo())

    activity_log = get_activitylog()
    session.set_activitylog(activity_name, activity_kind, activity_version, activity_guid, activity_log)
    if not activity_log:
        _log.warning("No activity log for '%s'" % activity_name)

    kinematics_log = get_kinematicslog()
    session.set_kinematicslog(kinematics_log)
    if not kinematics_log:
        _log.warning("No kinematics log for '%s'" % activity_name)

    filename = os.path.join(os.environ["CUREGAME_TEMPPATH"], "%s.xml.gz" % session.guid)
    _log.info("Writing session log: %s" % filename)
    session.write(filename, password=config.SESSION_SECRET)
    _log.info("Importing session log: %s" % filename)
    vrssync.import_sessionlog(filename)


def load_hgt(x3dfile, fullscreen=True, mirror=True, stereo=True, use_custom=True):
    """
    Render X3D scene at ``x3dfile`` using H3D, if ``use_custom`` is
    set to True we'll use our internal custom version which supports
    kinematics data logging (to H3D_DEVICELOG_FILENAME) otherwise the
    standard H3D loader is used. Returns True if the scene exited
    normally or False if the user manually exited the scene. (Exits
    due to errors are masked as forced exits to keep the system from
    treating such session as normal ones).
    """
    if use_custom:
        retcode = H3DLoader.CustomH3DLoader(debug=DEBUG).run(x3dfile, fullscreen, mirror, stereo)
    else:
        retcode = H3DLoader.DefaultH3DLoader(debug=DEBUG).run(x3dfile, fullscreen, mirror, stereo)
    return (retcode == H3DLoader.EXIT_NORMAL)


def runtest(config, testname, patient_alias, patient_guid, test_cfg):
    """
    Run assessment activity and generate a session log by combining the
    contents of the activity eventlog and the kinematics (H3D device) log
    (CUREGAME_EVENTLOG_FILENAME + H3D_DEVICELOG_FILENAME). Returns True if
    session was completed or False if it was manually aborted or some
    oher error occured.
    """
    if testname in HGT_TESTS:
        (path, x3d, version, kind, guid) = HGT_TESTS[testname]
    else:
        _log.error("Unknown assessment '%s'" % testname)
        return False

    path = os.path.join(os.environ["CUREGAME_ROOT"], path)
    os.chdir(path)
    x3d = os.path.join(path, x3d)

    # Pass config data to HGT via via a temporary file resource.
    test_cfg.write(os.environ["CUREGAME_HGT_CONFIG_FILENAME"])

    timestamp = time.time()
    if not load_hgt(x3d, config.H3D_FULLSCREEN, config.H3D_MIRROR, config.H3D_STEREO):
        _log.warning("Not saving session log due to manual exit")
        return False
    duration = time.time() - timestamp
    save_sessionlog(config, patient_alias, patient_guid, timestamp, \
                        duration, testname, kind, version, guid)
    return True


def rungame(config, gamename, patient_alias, patient_guid, game_cfg):
    """
    Run training activity and generate a session log by combining the
    contents of the activity eventlog (CUREGAME_EVENTLOG_FILENAME), if
    available, and other more general information. Returns True if
    session was completed or False if it was manually aborted or some
    oher error occured.
    """
    if gamename not in HGT_GAMES:
        _log.error("Unknown activity '%s'" % gamename)
        return False

    (path, x3d, version, kind, guid) = HGT_GAMES[gamename]

    path = os.path.join(os.environ["CUREGAME_ROOT"], path)
    os.chdir(path)
    x3d = os.path.join(path, x3d)

    # Pass config data to HGT via via a temporary file resource.
    game_cfg.write(os.environ["CUREGAME_HGT_CONFIG_FILENAME"])

    timestamp = time.time()
    if not load_hgt(x3d, config.H3D_FULLSCREEN, config.H3D_MIRROR, config.H3D_STEREO):
        _log.warning("Not saving session log due to manual exit")
        return False
    duration = time.time() - timestamp
    save_sessionlog(config, patient_alias, patient_guid, timestamp, \
                        duration, gamename, kind, version, guid)
    return True


def rundashboard(config):
    """
    Launch dashboard menu, returns True/False to signal if dashboard launched
    exited in normal fashion.
    """
    path = os.path.join(os.environ["CUREGAME_ROOT"], "dashboard/")
    os.chdir(path)
    if config.FEATURES["enable_tilted_frame"]:
        x3d = os.path.join(path, "dashboard_tilted.x3d")
    else:
        x3d = os.path.join(path, "dashboard.x3d")
    return load_hgt(x3d, config.H3D_FULLSCREEN, config.H3D_MIRROR, config.H3D_STEREO)


###########################################################################
# VRS controller entry-point.
###########################################################################

def main():
    try:
        if not singleinstance.lock("vrs-manager"):
            _log.warning("An instance of VRS manager is already running")
            return

        from vrs.config import Config
        config = Config(os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"))

        if (not DEBUG) and (not config.FEATURES["enable_allow_autostart"]):
            # See bootstrap.py install() for details about this work-around.
            if "/autostart" in sys.argv:
                _log.info("Forcefully aborting an automated VRS launch")
                return

        if (not DEBUG) and config.FEATURES["enable_force_usb_storage"]:
            show_checkusbstorage(config)

        if config.FEATURES["enable_standalone_mode"]:
            start_server(os.path.join(os.environ["CUREGAME_ROOT"]))

        background_precache([
                os.path.join(os.environ["CUREGAME_ROOT"], datadir)
                for datadir in ["activities",
                                "h3d",
                                "media"]])

        from vrs.H3DConfig import H3DConfig
        h3dconfig = H3DConfig(os.environ["H3D_ROOT"])
        h3dconfig.set_display_mode(config.H3D_DISPLAY)
        if config.FEATURES["enable_tilted_frame"]:
            h3dconfig.set_display_type("Curictus VRS Tilted")
        else:
            h3dconfig.set_display_type("Curictus VRS")

        import vrs.locale
        i18n_path = os.path.join(os.environ["CUREGAME_ROOT"], "media/i18n")
        vrs.locale.load_translations(i18n_path, "vrs")
        vrs.locale.set_locale(config.SYSTEM_LOCALE)

        import vrs.client
        db_http = vrs.client.connect_db(config, on_commit=vrssync.trigger)
        db_sync = vrs.client.connect_db(config, on_commit=vrssync.trigger)

        jobqueue = Queue.Queue()

        start_http(config, jobqueue, db_http)
        start_dbsync(config, jobqueue, db_sync)

        _log.info("VRS %s client is running at http://%s:%s" % (
                config.SYSTEM_VERSION, config.LOCAL_ADDR, config.LOCAL_PORT))

        if not DEBUG:
            template = os.path.join(os.environ["CUREGAME_ROOT"], "media\\wallpapers\\wallpaper.jpg")
            wallpaper = os.path.join(os.environ["CUREGAME_TEMPPATH"], "wallpaper.jpg")
            caption = "VRS %s | %s" % (config.SYSTEM_VERSION, config.STATION_ALIAS)
            imageutils.set_image_caption(caption, template, wallpaper)
            kioskmode.enter(wallpaper)

        # Enter the main system loop by prepping the jobqueue with a 'init'
        # command which has the exact same semantics as the user initiated
        # 'logout' command - they both reset the system to a clean state.
        jobqueue.put(("init", []))

        while True:
            try:
                (cmd, args) = jobqueue.get(True, 1)
                _log.info("Got system '%s' command with args: %s" % (cmd, args))
                if cmd == "start_game":
                    (gamename, patient_alias, patient_guid, game_cfg) = args
                    rungame(config, gamename, patient_alias, patient_guid, game_cfg)
                elif cmd == "start_test":
                    (testname, patient_alias, patient_guid, test_cfg) = args
                    runtest(config, testname, patient_alias, patient_guid, test_cfg)
                elif cmd == "init" or cmd == "reset":
                    if (not DEBUG) and config.FEATURES["enable_phantom_calibration"]:
                        # Temporarily turn down brightness (gamma) to match the
                        # expected brightness the user will experience when the
                        # 3D shutter glasses are active (running a H3D scene).
                        win32util.setgamma(0)
                        # Note: system will halt with a fatal error if a
                        # Phantom Omni is not detected properly.
                        show_checkphantom(config)
                        # Check if CUP is signaling that a software update is
                        # ready. On the very first run (init = system boot) we
                        # want to at least give the user a chance to train with
                        # the system should CUP signal that a software is ready
                        # right away. On subsequent runs which will occur when
                        # users either manually or automatically are logged out
                        # we don't care and will happily abort the calibration
                        # sequence in order to exit and let CUP run the update.
                        MIN_WAIT_SEC_BEFORE_ALLOW_UPDATE_ON_INIT = 5 * 60
                        checkpoint = time.time()
                        def software_update_ready():
                            elapsed = time.time() - checkpoint
                            return have_software_update() and \
                                (cmd == "reset" or elapsed > MIN_WAIT_SEC_BEFORE_ALLOW_UPDATE_ON_INIT)
                        aborted = True
                        if show_recalibrate(config, abort_callback=software_update_ready):
                            if show_instructions(config, abort_callback=software_update_ready):
                                aborted = False
                        if aborted and software_update_ready():
                            _log.info("VRS client exiting to apply software update")
                            break
                        # Restore brightness/gamma back to maximum since we're
                        # going to run H3D scenes with active shutter glasses.
                        win32util.setgamma(128)
                elif cmd == "terminate":
                    break
                elif cmd == "shutdown":
                    if config.FEATURES["enable_windows_shutdown"]:
                        win32util.shutdown()
                    break
                else:
                    _log.error("Unknown system command '%s' with args: %s" % (cmd, args))
            except Queue.Empty:
                pass

            if not DEBUG:
                rundashboard(config)

            if DEBUG and code_changed():
                _log.info("VRS client exiting to reload modified code")
                break

    except KeyboardInterrupt:
        _log.info("Server manual exit")
    except:
        if not DEBUG:
            kioskmode.restore()
            from vrs.debug import email_crashreport
            email_crashreport(
                os.path.join(os.environ["CUREGAME_ROOT"], "config.cfg"),
                os.environ["CUREGAME_LOGPATH"])
        raise # Bubble up to top-level exception handler.
    finally:
        if not DEBUG:
            kioskmode.restore()
        stop_dbsync()
        stop_http()
        stop_server()


###########################################################################
# The End.
###########################################################################
