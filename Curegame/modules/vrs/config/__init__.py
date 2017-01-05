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

# coding: utf-8

import os, sys, imp
import platform
import inspect
import logging
import subprocess

###########################################################################
# Introduction (read this first!)
###########################################################################

#
# The config class below represents the default (shared) system configuration
# for client and server components. To override and/or add settings create a
# custom config file with key/value pairs using normal Python syntax:
#
# SYSTEM_LOCALE = 'en_US'
# UPLOAD_ADDR   = "upload.vrshowroom.com"
# UPLOAD_PORT   = 80
#
# Pass the full path to the config file to Config() and the class instance
# will be updated with the custom settings in the file.
#
# NOTE: You have to override all settings which are set to None!
#

###########################################################################
# Utilities.
###########################################################################

def get_build_info():
    """
    Try locate build string from a 'version.txt' file recursively in parent
    directories. Return a string identifier or placeholder on failure.
    """
    version = "?"
    try:
        rootdir = os.path.abspath(os.path.dirname(sys.executable))
        while True:
            filepath = os.path.join(rootdir, "version.txt")
            if os.path.isfile(filepath):
                version = open(filepath, "rt").read().strip()
                break
            else:
                parent = os.path.split(rootdir)[0]
                if rootdir == parent:
                    break
                else:
                    rootdir = parent
    except Exception, e:
        pass
    finally:
        return version


def get_hardware_guid():
    """
    Return (unique) identifier for computer compused of the manufacturer and
    the serial, ex: LENOVO-L3AET9M, or an empty string on failure.
    """
    if platform.system() != "Windows":
        return ""
    try:
        # Hide console window by requiring that child processes call
        # ShowWindow() which command-line application normallt don't do.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
        # Query result are returned as two lines, key followed by the value.
        manufacturer = subprocess.Popen(
            "wmic bios get Manufacturer", startupinfo=startupinfo,
            stdout=subprocess.PIPE).communicate()[0].strip().split('\n')[1]
        serial = subprocess.Popen(
            "wmic bios get SerialNumber", startupinfo=startupinfo,
            stdout=subprocess.PIPE).communicate()[0].strip().split('\n')[1]
        return "%s-%s" % (''.join([c for c in manufacturer.replace(" ", "-")
                                   if c.isalnum() or c == '-']).upper(),
                          ''.join([c for c in serial.replace(" ", "-")
                                   if c.isalnum() or c == '-']).upper())
    except Exception:
        _log.exception("Exception while retrieving BIOS hardware data")
        return ""


###########################################################################
# FeatureFlags.
###########################################################################

# NOTE: This class is duplicated in ``hgt.ActivityConfig`` due to licensing
# issues (HGT is GPL, the rest of the code is not open-source). If you make any
# changes or fixes make sure to apply them there as well!

class FeatureFlags(dict):
    """
    Dictionary like object where keys can be accessed as attributes,
    i.e. obj["key"] => obj.key access the same thing. Missing keys will
    automatically default to boolean False.

    Example:
      f = FeatureFlags(enable_clouds=False, enable_rainbow=False)

      if f.enable_clouds and f["enable_rainbow"]:
        print "Render clouds and/or rainbows!"

    """
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            if name[:1] == "_":
                raise AttributeError(name)
            else:
                _log.error("Missing feature flag: %s" % name)
                return False

    def __missing__(self, key):
        return self.__getattr__(key)

    def __setattr__(self, name, value):
        self[name] = value


###########################################################################
# Base configuration.
###########################################################################

_log = logging.getLogger('config')

class BaseConfig(object):

    FEATURES = FeatureFlags()

    def __init__(self, filename=None):
        """
        Initialize config and load overriden settings from ``filename``. Will
        raise an exception if ``filename`` is missing or if it's corrupt and/or
        incomplete (i.e. missing important settings, see comments above).
        """
        self.DEFAULT_FEATURES = self.FEATURES.copy()
        if filename:
            self.load(filename)


    def load(self, filename):
        """
        Load configuration from ``filename`` updates class instance with new
        attributes corresponding to the settings found in the file. Will raise
        an exception if ``filename`` is missing or is corrupt/invalid.
        """
        if not os.path.exists(filename):
            raise ImportError("Configuration file %s does not exist" % filename)
        _log.info("Loading config file: %s" % filename)
        try:
            # The code below basically creates an in-memory module where we
            # dynamically execute code loaded from the file. By diffing the
            # namespace of the module we can figure out which (global)
            # variables were introduced and update the config (class) instance
            # variables with new values.
            mod_name = '__temp_config__'
            mod = imp.new_module(mod_name)
            mod.__dict__['FeatureFlags'] = FeatureFlags # Inject helper class.
            sys.modules[mod_name] = mod
            exec_namespace = mod.__dict__
            prev_namespace = mod.__dict__.copy()
            config_code = open(filename, 'rt').read()
            filename = filename.encode(sys.getfilesystemencoding())
            exec compile(config_code, filename, 'exec') in exec_namespace
            diff_namespace = dict([(k, v) for (k,v) in exec_namespace.iteritems()
                                   if k not in prev_namespace and k[:2] != '__'])
            for (key, value) in diff_namespace.iteritems():
                if hasattr(self, key):
                    _log.info("Setting: %s = %s (default: %s)" % (key, repr(value), repr(getattr(self, key))))
                else:
                    _log.info("Setting: %s = %s" % (key, repr(value)))
                setattr(self, key, value)
            # Feature flags which haven't been overriden revert to their
            # default values, invalid/misspelled flags are ignored.
            for (key, value) in self.DEFAULT_FEATURES.iteritems():
                if key not in self.FEATURES:
                    self.FEATURES[key] = value
                    _log.info("Feature: %s = %s" % (key, repr(value)))
                else:
                    _log.info("Feature: %s = %s (default: %s)" % (key, repr(self.FEATURES[key]), repr(value)))
            for key in self.FEATURES:
                if key not in self.DEFAULT_FEATURES:
                    _log.warning("Unknown feature flag: %s" % (key))
            if not self._validate():
                raise ImportError("Configuration file %s is invalid" % filename)
        except Exception, e:
            _log.error("Exception while loading config")
            raise
        finally:
            if mod_name in sys.modules:
                del sys.modules[mod_name]


    def _validate(self):
        """
        Validate (overridden) settings and return True/False to signal success.
        """
        ok = True
        for (k,v) in self.__getstate__().iteritems():
            if v is None:
                _log.error("Setting: %s is missing value" % k)
                ok = False
        return ok


    def __getstate__(self):
        """
        The pickle module doesn't serialize class data members which means that
        we have manually generate a fake self.__dict__ since we use class
        fields exlusively for the configration options.
        """
        return dict((key, value) for (key, value) in inspect.getmembers(self)
                    if not callable(value) and not key.startswith('__'))


###########################################################################
# VRS default configuration.
###########################################################################

class Config(BaseConfig):
    HARDWARE_GUID  = get_hardware_guid()

    ZONE_GUID      = None # UUID4: "142f40f0-ddaf-11de-a779-002186a2bf30"
    STATION_GUID   = None # UUID4: "1d0621cf-ddaf-11de-aebc-002186a2bf30"
    STATION_ALIAS  = None # Alphanumeric (\w+) with no spaces: "client1"

    LOCAL_ADDR     = "127.0.0.1"
    LOCAL_PORT     = 8000

    REMOTE_HOST    = "stable.curictus.se"
    REMOTE_ADDR    = "stable.curictus.se"
    REMOTE_PORT    = 80

    SYSTEM_BUILD   = get_build_info()
    SYSTEM_VERSION = "1.0"
    SYSTEM_LOCALE  = "sv_SE"

    SESSION_SECRET = '' # Set to a non-empty password to encrypt all session logs.

    S3_UPLOAD_DIR  = '.upload'

    POSTGRES_DB    = ''
    POSTGRES_USER  = ''
    POSTGRES_PASS  = ''
    POSTGRES_PORT  = 5432

    H3D_DISPLAY    = "1680x1050_120Hz_flipped"
    H3D_FULLSCREEN = True
    H3D_MIRROR     = True
    H3D_STEREO     = True

    CUSTOMER_ZONES = {
        u"81f438b7-faaf-41a5-9ee9-2affd18061e8" : (u"Curictus", "2319", "stable.curictus.se"),
    }

    FEATURES       = \
        FeatureFlags(enable_phantom_calibration=True,      # Display calibration screens on startup?
                     enable_tilted_frame=True,             # Enabled VRS 2.0 ergonomic tilted frame?
                     enable_hgt_levels=True,               # Activate difficulty levels in HGT?
                     enable_windows_shutdown=True,         # Should VRS exit result in Windows shutdown?
                     enable_data_sync=True,                # Enable ping and DB syncing with server?
                     enable_demo_mode=False,               # Auto-login as guest to bypass login altogether?
                     enable_standalone_mode=False,         # Run VRS server locally together with client?
                     enable_force_usb_storage=False,       # Make sure $CUREGAME_DATA points to a USB drive?
                     enable_allow_autostart=True,          # Should VRS to launch on Windows login?
                     enable_force_pincode_selection=False) # Force users to manually select pincode when creating profiles?



###########################################################################
# CUP configrations.
###########################################################################

class UpdateConfig(BaseConfig):
    HARDWARE_GUID    = get_hardware_guid()

    UPDATE_CHANNEL   = None # String: dev|beta|stable
    UPDATE_INTERVAL  = 30   # Minutes

    AWS_BUCKET       = 'update.curictus.se'
    PUBKEYFILE       = 'curictus.pubkey'

    LOCK_CUP_VERSION = "" # Set to non-empty (i.e. '2139') to override server.
    LOCK_VRS_VERSION = "" # Set to non-empty (i.e. '0.6.1748') to override server.


class BuildConfig(BaseConfig):
    HARDWARE_GUID   = get_hardware_guid()
    UPDATE_CHANNEL  = None # String: dev|beta|stable

    AWS_BUCKET      = 'update.curictus.se'
    AWS_ACCESS_KEY  = None
    AWS_SECRET_KEY  = None

    PRIVKEYFILE     = 'curictus.key'
    PUBKEYFILE      = 'curictus.pubkey'


###########################################################################
# The End.
###########################################################################
