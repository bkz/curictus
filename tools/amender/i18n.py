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
import tornado.locale

_log = logging.getLogger('locale')

###########################################################################
# I18n wrapper for Tonardo gettext support.
###########################################################################

# Current system locale.
_lang = tornado.locale.get("en_US")

# Mapping of locale codes => file paths to JSON message catalogs.
_json = {
    "unknown" : {"singular":{}, "plural":{}}
}

def set_locale(code):
    """
    Set the current locale to ``code``, i.e 'en_US' or 'fr_FR'.
    """
    global _lang
    _log.debug("Setting system locale to: %s" % code)
    tornado.locale.set_default_locale(code)
    _lang = tornado.locale.get(code)

    
def get_json_catalog(code=None):
    """
    Retrieve message catalog in JSON format for locale ``code``. If ``code`` is
    None, return a default empty catalog.
    """
    if code is None:
        code = _lang.code
    try:
        return simplejson.loads(open(_json[code], "rt").read().decode("utf-8"))
    except KeyError:
        return _json["unknown"]

    
def load_translations(directory, domain):
    """
    Load GNU gettext and JSON message catalogs for ``domain`` from ``directory``.
    """
    _log.debug("Loading translations from: %s" % directory)
    tornado.locale.load_gettext_translations(directory, domain)
    for langcode in os.listdir(directory):
        json_file = os.path.join(directory, langcode, "LC_MESSAGES/%s.json" % domain)
        if os.path.exists(json_file):
            _json[langcode] = json_file

    
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
    return _lang.translate(message, plural_message, count)


###########################################################################
# The End.
###########################################################################
