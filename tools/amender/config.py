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
import imp, sys

_log = logging.getLogger('config')

##############################################################################
# ConfigError.
##############################################################################

class ConfigError(RuntimeError):
    pass

class ConfigLoadError(ConfigError):
    pass

class ConfigParseError(ConfigError):
    pass


##############################################################################
# BaseConfig.
##############################################################################
    
class BaseConfig(object):
    """
    Base class to inherit from when creating default configuration class for an
    application:

    class Config(BaseConfig):
        SETTING_VAR_1 = 'Value'
        SETTING_VAR_2 = {'a': 1, 'b': 2}

    The class members variable can be overriden with custom values using a
    local configuration file which is injected using load(). The configuration
    file uses ordinary Python syntax for setting new values as following:

    SETTING_VAR_1 = 1234
    SETTING_VAR_2 = {'a': 100, 'b': 200 }
    SETTING_VAR_3 = False

    After issue load('config.cfg') the class instance of Config() will be
    updated with new values for SETTING_VAR_1 and SETTING_VAR_2 and a new class
    member variable SETTING_VAR_3 will be introduced.
    """
    
    def load(self, filename):
        """
        Load configuration from ``filename`` updates class instance with new
        attributes corresponding to the settings found in the file.
        """
        if not os.path.exists(filename):
            raise ConfigLoadError("Config file %s does not exist" % filename)
        _log.info("Loading file: %s" % filename)
        try:
            mod_name = '__temp_config__'
            mod = imp.new_module(mod_name)
            sys.modules[mod_name] = mod
            exec_namespace = mod.__dict__
            prev_namespace = mod.__dict__.copy()
            config_code = open(filename, 'rt').read()
            exec compile(config_code, filename, 'exec') in exec_namespace
            diff_namespace = dict([(k, v) for (k, v) in exec_namespace.iteritems()
                                   if k not in prev_namespace and k[:2] != '__'])
            for (key, value) in diff_namespace.iteritems():
                if hasattr(self, key):
                    _log.info("Setting: %s = %s (default: %s)" % (
                            key, repr(value), getattr(self, key)))
                else:
                    _log.info("Setting: %s = %s" % (key, repr(value)))
                setattr(self, key, value)                
        except Exception, e:
            _log.exception("Exception while loading config")
            raise ConfigParseError("Failed to load: %s (%s)" % (filename, e))
        finally:
            if mod_name in sys.modules:
                del sys.modules[mod_name]


##############################################################################
# Unit test.
##############################################################################

if __name__ == '__main__':
    import shutil
    import tempfile
    import unittest

    class NullStream(object):
        def write(self, s):
            pass
        def flush(self):
            pass

    import logging.handlers
    logging.getLogger().setLevel(logging.DEBUG)            
    logging.getLogger().addHandler(logging.StreamHandler(NullStream()))
    
    class DefaultConfig(BaseConfig):
        SETTING_A = 'a'
        SETTING_B = None
        SETTING_C = [1, 2, 3]
        SETTING_D = None
        SETTING_E = None
    
    class TestConfig(unittest.TestCase):
        def setUp(self):
            self.tempdir = tempfile.mkdtemp()

        def tearDown(self):
            shutil.rmtree(self.tempdir)

        def test_missing(self):
            config = DefaultConfig()
            self.assertRaises(ConfigLoadError, config.load, "missing.cfg")

        def test_invalid(self):
            filepath = os.path.join(self.tempdir, "invalid.cfg")
            open(filepath, "wt").write("SETTING_D = 1\nSETTING_E = ")
            config = DefaultConfig()
            self.assertRaises(ConfigParseError, config.load, filepath)

        def test_load(self):
            filepath = os.path.join(self.tempdir, "invalid.cfg")
            open(filepath, "wt").write(
                "SETTING_B = True\n" \
                "SETTING_C = [1, 2, 3, 4]\n" \
                "SETTING_D = 'hello'")
            config = DefaultConfig()
            config.load(filepath)
            self.assertEquals(config.SETTING_A, 'a')
            self.assertEquals(config.SETTING_B, True)
            self.assertEquals(config.SETTING_C, [1, 2, 3, 4])
            self.assertEquals(config.SETTING_D, 'hello')
            
    unittest.main()


##############################################################################
# The End.
##############################################################################
