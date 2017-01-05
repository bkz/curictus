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
import simplejson

_log = logging.getLogger('locale')

###########################################################################
# Utilities.
###########################################################################

def safe_encode(s):
    """
    Try to encode ``s`` to a iso8859-1 (exnteded ASCII) and fallback a
    "cleaned" version of the string when not possible.
    """
    try:
        return s.encode("iso8859-1")
    except UnicodeError:
        return s.encode("iso8859-1", errors='ignore')

    
###########################################################################
# Support for usings VRS i18N JSON catalogs.
###########################################################################

_translations = {"singular":{}, "plural":{}}

def load_catalog(filename):
    """
    Load JSON message catalog from ``filename`` which is UTF-8 encoded, returns
    True/False depending on success.
    """
    _log.info("Loading JSON message catalog from: %s" % filename)
    return load_translations(open(filename, "rt").read())


def load_translations(json):
    """
    Load JSON message catalog (dict) from ``json`` which is a UTF-8 encoded
    string, returns True/False depending on success.
    """
    global _translations
    try:
        _translations = simplejson.loads(json.decode("utf-8"))
        # Note: we have to forcefully encode strings to an ASCII (single
        # character) format since H3D doesn't support unicode natively (i.e C++
        # UCS2, wchar_t or similar) or raw UTF-8. Since UTF-8 is a safe format
        # (no null bytes) we'll use it as fallback for strings with non-ASCII
        # compatible unicode characters.
        for (key, value) in _translations["singular"].iteritems():
            _translations["singular"][key] = safe_encode(value)
        for (key, value) in _translations["plural"].iteritems():
            _translations["plural"][key] = safe_encode(value)
        return True
    except IOError:
        return False

    
def translate(message, plural_message=None, count=None):
    """
    Returns the translation for the given message for this locale. 
    If plural_message is given, you must also provide count. We return
    plural_message when count != 1, and we return the singular form
    for the given message when count == 1.

    Example:

      translate('%(count)s reported dead', '%(count)s reported deaths', \
          len(victims)) % {'count' : len(victims)}

    """
    if plural_message and count != 1:
        if plural_message in _translations["plural"]:
            # Special case: an empty translated string signals that we should
            # use the key (i.e. the source string).
            return _translations["plural"][plural_message] or plural_message
        else:
            return plural_message + "(!)"
    else:
        if message in _translations["singular"]:
            # Special case: an empty translated string signals that we should
            # use the key (i.e. the source string).
            return _translations["singular"][message] or message
        else:
            return message + "(!)"

###########################################################################
# Unit-test.
###########################################################################

import unittest

class TestTranslation(unittest.TestCase):
    def test_translate(self):
        self.assertTrue(
            load_translations("""{"plural": {"EN Plural %(num)s formatting %(missing)s works!\\n": "SV Plural %(num)s formattering %(missing)s fungerar!\\n", "apples": ""}, "singular": {"EN Singular %(num)s formatting %(missing)s works!\\n": "SV Singular %(num)s formattering %(missing)s fungerar!\\n", "apple" : ""}}"""))

        self.assertEqual(
            translate("apple", "apples", count=1), "apple")

        self.assertEqual(
            translate("apple", "apples", count=2), "apples")
        
        self.assertEqual(
            translate("orange", "oranges", count=1), "orange(!)")

        self.assertEqual(
            translate("orange", "oranges", count=2), "oranges(!)")

        self.assertEqual(
            translate(
                "EN Singular %(num)s formatting %(missing)s works!\n",
                "EN Plural %(num)s formatting %(missing)s works!\n",
                count=1) % {"num" : 1, "missing" : "abc"},
            "SV Singular 1 formattering abc fungerar!\n")


        self.assertEqual(
            translate(
                "EN Singular %(num)s formatting %(missing)s works!\n",
                "EN Plural %(num)s formatting %(missing)s works!\n",
                count=2) % {"num" : 2, "missing" : "abc"},
            "SV Plural 2 formattering abc fungerar!\n")


if __name__ == '__main__':
    unittest.main()

    
###########################################################################
# The End.
###########################################################################
