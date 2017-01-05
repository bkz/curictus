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
import hashlib
import subprocess
import tarfile
import tempfile
import time
import socket

import logging
import logging.handlers

import win32def
import win32util

from vrs import kioskmode
from vrs.debug import email_crashreport
from vrs.update import UPDATE_SIGNAL

from vrs.util import crypto
from vrs.util import httputil
from vrs.util import download
from vrs.util import singleinstance
from vrs.util import retry
from vrs.util.path import rmfile, rmtree

_log = logging.getLogger('bootstrap')

###########################################################################
# Global configuration.
###########################################################################

DOWNLOAD_DIR        = ".download"

CUP_KEY             = "/%(channel)s/cup/latest/cup.exe"
CUP_SIGN_KEY        = "/%(channel)s/cup/latest/cup.exe.sign"
CUP_VERSION_KEY     = "/%(channel)s/cup/version.txt"
CUP_INSTALL_DIR     = "D:\\CUP"

VRS_KEY             = "/%(channel)s/vrs/%(version)s/vrs.tar.bz2"
VRS_SIGN_KEY        = "/%(channel)s/vrs/%(version)s/vrs.tar.bz2.sign"
VRS_VERSION_KEY     = "/%(channel)s/vrs/version.txt"
VRS_CONFIG_KEY      = "/%(channel)s/config/%(hardware)s/config.cfg"
VRS_INSTALL_DIR     = "D:\\VRS"
VRS_EXTRACT_DIR     = "D:\\"

##############################################################################
# Utilities.
##############################################################################

@retry(5, delay=1, exponential_backoff=True)
def download_s3(rootdir, config, key, sign_key, filepath):
    """
    Download S3 object ``key``, verifying it using a DSA signature stored under
    ``sign_key`` and save the resulting file to ``filepath``.
    """
    url = "http://" + config.AWS_BUCKET + key
    if not download.saveurl(url, filepath):
        # Clean up after us for next retry attempt, the error might have been a
        # failure to resume a previous download.
        if os.path.exists(filepath):
            rmfile(filepath)
        raise RuntimeError("Failed to download S3 object %s/%s" % (config.AWS_BUCKET, key))
    sign = httputil.get(config.AWS_BUCKET, sign_key)
    if not sign:
        raise RuntimeError("Failed to download digital signature %s" % sign_key)
    pubkey = os.path.join(rootdir, config.PUBKEYFILE)
    if not crypto.verify(pubkey, open(filepath, "rb").read(), sign):
        rmfile(filepath)
        raise RuntimeError("Download corrupt, dignal signature %s does not match %s" % (sign_key, key))


@retry(5, delay=1, exponential_backoff=True)
def s3_get(config, key):
    """
    Retrieve value for `key` for S3 bucket as configured in ``config``. Returns
    raw string or raises an exception on failure.
    """
    response = httputil.get(config.AWS_BUCKET, key)
    if not response:
        raise RuntimeError("GET failed: %s/%s" % (config.AWS_BUCKET, key))
    return response


def try_lock_instance(appname, retry=10, wait=1):
    """
    Attemp to accquire global lock for ``appname`` alias, retrying at most
    ``retry`` counts sleeping ``wait`` seconds between each attempt.
    """
    for n in range(retry):
        if singleinstance.lock(appname):
            return True
        time.sleep(wait)
    return False


def extract_bzip2(destpath, archive):
    """
    Unarchive contents of ``archive`` to ``destpath``.
    """
    tar = tarfile.open(archive, "r:bz2")
    tar.extractall(destpath)
    tar.close()


def signal_software_update():
    """
    Signal to VRS using a global (mutex) signal that we have software updates
    downloaded and ready for installation.
    """
    win32util.setsignal(UPDATE_SIGNAL)



def register_scheduled_task(rootdir, interval):
    """
    Register CUP in ``rootdir`` as a scheduled task to be run ``interval``
    minutes as an elevated process (highest privileges).
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen('''schtasks /f /create /rl HIGHEST /sc minute /mo %s /tn "cup" /tr "%s/cup.exe"''' % (interval, rootdir),
                     startupinfo=startupinfo)


def run_bat(filepath):
    """
    Execute .bat file at ``filepath`` and hiding the resulting console window.
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
    subprocess.call(filepath, shell=True, startupinfo=startupinfo)


def restart():
    """
    Forcefully restart computer.
    """
    win32util.shutdown(restart=True)


def have_network_access():
    """
    Returns True/False to signal if we have working access to the internet.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.se', 80))
        s.close()
        return True
    except Exception, e:
        return False


##############################################################################
# Simple install state recorder (detect crashes, powerloss, restarts, etc).
##############################################################################

STATE_FILE = ".state"

STATE_INSTALL_CLEAN = 0
STATE_INSTALL_CUP   = 1
STATE_INSTALL_VRS   = 2


def set_state(rootdir, state):
    """
    Set current state for application in ``rootdir`` to ``state``.
    """
    f = open(os.path.join(rootdir, STATE_FILE), "wt")
    f.write("%s" % state)
    f.flush()
    f.close()


def get_state(rootdir):
    """
    Retrieve current state for application ``rootdir``.
    """
    try:
        return int(open(os.path.join(rootdir, STATE_FILE), "rt").read().strip())
    except (IOError, WindowsError, ValueError):
        pass
    return STATE_INSTALL_CLEAN


##############################################################################
# VRS update.
##############################################################################

def get_current_vrs_version():
    """
    Returns string version id for current VRS installation or None if VRS isn't
    installed or is corrupt.
    """
    try:
        versionfile = os.path.join(VRS_INSTALL_DIR, "version.txt")
        return open(versionfile, "rt").read().strip()
    except (IOError, WindowsError):
        return None


def get_latest_vrs_version(config):
    """
    Retrieve latest VRS version string available on the update server.
    """
    response = s3_get(config, VRS_VERSION_KEY % {"channel" : config.UPDATE_CHANNEL})
    return response.strip()


def lock_vrs():
    """
    Accquire global instance lock for VRS components to make sure they don't
    start while we're updating.
    """
    if not try_lock_instance("vrs-manager", retry=60, wait=1):
        _log.info("Failed to accquires VRS manager lock")
        return False
    if not try_lock_instance("vrs-sync", retry=10, wait=1):
        _log.info("Failed to accquires VRS sync lock")
        return False
    return True


def launch_vrs():
    """
    Launch VRS after successful software update.
    """
    pythonw_bin = os.path.join(VRS_INSTALL_DIR, "python/pythonw.exe")
    bootstrap_script = os.path.join(VRS_INSTALL_DIR, "bootstrap.py")
    win32util.runasdesktop(pythonw_bin, bootstrap_script, VRS_INSTALL_DIR)


def update_vrs(rootdir, version, config):
    """
    Update or re-install VRS to latest ``version`` using ``config``.
    """
    key = VRS_KEY % {"channel" : config.UPDATE_CHANNEL, "version" : version}
    sign_key = VRS_SIGN_KEY % {"channel" : config.UPDATE_CHANNEL, "version" : version}
    tempdir = os.path.join(rootdir, DOWNLOAD_DIR)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    archive = os.path.split(key)[1]
    filepath = os.path.join(tempdir, "%s-%s" % (version, archive))
    download_s3(rootdir, config, key, sign_key, filepath)
    signal_software_update()
    if not lock_vrs():
        return False
    try:
        win32util.rotatedisplay(True)
        kioskmode.showloader(
            os.path.join(rootdir, "splash_ticker.png"),
            os.path.join(rootdir, "splash_logo.png"),
            "Updating VRS Software...",
            version);

        uninstall_bat = os.path.join(VRS_INSTALL_DIR, "uninstall.bat")
        if os.path.exists(uninstall_bat):
            _log.info("Executing uninstall.bat")
            run_bat(uninstall_bat)
        if os.path.exists(VRS_INSTALL_DIR):
            _log.info("Deleting previous VRS installation")
            rmtree(VRS_INSTALL_DIR)

        _log.info("Extracing VRS archive")
        extract_bzip2(VRS_EXTRACT_DIR, filepath)

        winsetup_bat = os.path.join(VRS_INSTALL_DIR, "winsetup.bat")
        _log.info("Executing winsetup.bat")
        run_bat(winsetup_bat)

        install_bat = os.path.join(VRS_INSTALL_DIR, "install.bat")
        _log.info("Executing install.bat")
        run_bat(install_bat)

        return True
    finally:
        kioskmode.hideloader()
        win32util.rotatedisplay(False)


def update_vrs_config(rootdir, config, needlock=True):
    """
    Update config.cfg in VRS installation directory if a newer version is
    available. Normally we'll try to accquire the global intances lock for VRS,
    set ``needlock`` to False if you've already done so.
    """
    key = VRS_CONFIG_KEY % {"channel" : config.UPDATE_CHANNEL, "hardware" : config.HARDWARE_GUID}
    data = s3_get(config, key)
    if not data:
        raise RuntimeError("Could not download VRS config for %s" % config.HARDWARE_GUID)
    target = os.path.join(VRS_INSTALL_DIR, os.path.split(key)[1])
    if os.path.exists(target):
        current = hashlib.md5(open(target, "rt").read()).hexdigest()
    else:
        current = None
    latest = hashlib.md5(data).hexdigest()
    if (current is None) or current != latest:
        if needlock:
            signal_software_update()
            if not lock_vrs():
                return False
        _log.info("Updating VRS with new config")
        open(target, "wt").write(data)
        return True
    else:
        return False


##############################################################################
# CUP update.
##############################################################################

def get_current_cup_version(rootdir):
    """
    Get version string for CUP installation in ``rootdir``.
    """
    return open(os.path.join(rootdir, 'version.txt'), "rt").read().strip()


def get_latest_cup_version(config):
    """
    Retrieve latest version string for CUP available on the update server.
    """
    response = s3_get(config, CUP_VERSION_KEY % {"channel" : config.UPDATE_CHANNEL})
    return response.strip()


def cleanup(installdir, current_version):
    """
    Remove previous (left-over) versions in ``installdir`` which don't match
    our ``current_version``, i.e. the latest version.
    """
    try:
        for dirname in os.listdir(installdir):
            path = os.path.join(installdir, dirname)
            if os.path.isdir(path) and dirname != current_version:
                _log.info("Uninstalling previous version: %s" % dirname)
                rmtree(path)
    except (WindowsError, IOError):
        pass


def update_cup(rootdir, config):
    """
    Downloaded and execute new CUP installer from update server in ``config``.
    """
    key = CUP_KEY % {"channel" : config.UPDATE_CHANNEL}
    sign_key = CUP_SIGN_KEY % {"channel" : config.UPDATE_CHANNEL}
    tempdir = os.path.join(rootdir, DOWNLOAD_DIR)
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    exe = os.path.split(key)[1]
    filepath = os.path.join(tempdir, exe)
    download_s3(rootdir, config, key, sign_key, filepath)
    for n in range(5):
        try:
            _log.info("Attempt %d, launching %s" % (n, filepath))
            os.startfile(filepath)
            break
        except IOError:
            _log.exception("Unhandled exception while launching software update")
            time.sleep(1)
    else:
        raise RuntimeError("Failed to launch software update")


##############################################################################
# VRS software update entry-point.
##############################################################################

def setup_log(rootdir, logname):
    logging.getLogger().setLevel(logging.DEBUG)
    filelogger = logging.handlers.RotatingFileHandler(
        os.path.join(rootdir, logname), maxBytes=128*1024)
    filelogger.setFormatter(logging.Formatter("%(asctime)s : %(message)s"))
    logging.getLogger().addHandler(filelogger)


def main(is_frozen, rootdir):
    try:
        setup_log(rootdir, 'cup.log')

        if not win32util.is_admin():
            _log.error("Curictus Update requires admin rights!")
            sys.exit(1)

        if not try_lock_instance("cup"):
            _log.warning("Another instance is already running, exiting.")
            sys.exit(1)

        from vrs.config import UpdateConfig
        config = UpdateConfig(os.path.join(rootdir, 'cup.cfg'))

        if is_frozen:
            register_scheduled_task(rootdir, config.UPDATE_INTERVAL)

        if not have_network_access():
            _log.warning("No network access available")
            return

        state = get_state(rootdir)
        if (state != STATE_INSTALL_CLEAN):
            _log.info("Recovering state: %s" % state)
        current = get_current_cup_version(rootdir)
        latest  = config.LOCK_CUP_VERSION or get_latest_cup_version(config)
        if (state == STATE_INSTALL_CUP) or (current != latest):
            _log.info("Updating CUP from version %s to %s" % (current, latest))
            set_state(rootdir, STATE_INSTALL_CUP)
            update_cup(rootdir, config)
            set_state(rootdir, STATE_INSTALL_CLEAN)
            sys.exit(0)
        else:
            cleanup(CUP_INSTALL_DIR, current)

        current = get_current_vrs_version()
        latest  = config.LOCK_VRS_VERSION or get_latest_vrs_version(config)
        if (state == STATE_INSTALL_VRS) or (current != latest):
            _log.info("Updating VRS from version %s to %s" % (current, latest))
            set_state(rootdir, STATE_INSTALL_VRS)
            if update_vrs(rootdir, latest, config):
                if update_vrs_config(rootdir, config, needlock=False):
                    set_state(rootdir, STATE_INSTALL_CLEAN)
                    restart()
        else:
            if update_vrs_config(rootdir, config):
                launch_vrs()

    except KeyboardInterrupt:
        pass
    except Exception, e:
        _log.exception("Unhandled exception")
        if is_frozen:
            email_crashreport(os.path.join(rootdir, 'cup.cfg'), rootdir, classpath='vrs.config.UpdateConfig')


##############################################################################
# The End.
##############################################################################
