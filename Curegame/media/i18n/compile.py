#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os
import fnmatch
import logging
import re
import simplejson
import shutil
import sys

logging.getLogger().setLevel(logging.DEBUG)

##############################################################################
# Global configuration.
##############################################################################

# String will only be extracted from files matching this extension.
SCAN_EXT = ["html", "mxml", "as3", "as", "py"]

# NOTE: This list must only contain valid locale names, see tornado.locale.
LANGUAGES = [
    "en_US", 
    "sv_SE", 
]

# GNU gettext domain (POT and messages catalogs are named using this).
DOMAIN = "vrs"

# Unwrap calls to _() embedded in Tornado HTML templates so that xgettext can
# properly parse and extract strings for localization.
# Ex: <tag attr="{{_('html')}}" /> => <tag attr=_('html') />
HTML_RE = re.compile(r"""['"]\s*{{|}}\s*['"]""")

# Unwrap calls to _() embedded in MXML files so that xgettext can properly
# parse and extract strings for localization.
# Ex: <mx:Button label="{_('mxml')}" /> => <mx:Button label=_('mxml') />
MXML_RE = re.compile(r"""['"]\s*{|}\s*['"]""")


##############################################################################
# Utilties.
##############################################################################

def run(cmd):
    logging.debug(cmd)
    os.system(cmd)

    
##############################################################################
# Wrappers for the GNU gettext toolchain.
##############################################################################

def savejson(infile, outfile):
    """
    Parse ``infile`` which is PO/POT file and extract localized singular/plural
    strings and save them to ``outfile`` in JSON format. The strings are
    serialized as a dictionary/hash-table with the following structure:

      output = {
        "singular" : { "Apple"  : "Äpple",  "Orange"  : "Apelsin",   ... }
        "plural"   : { "Apples" : "Äpplen", "Oranges" : "Apelsiner", ... }
      }
    """
    # Decode translated PO/POT and filter out comments.
    lines = (unicode(line.decode("utf-8").strip()) for line in open(infile).readlines())
    lines = [line for line in lines if len(line) > 0 and line[0] != '#']
    # Skip first pair of translation strings which merely act as placeholders.
    assert lines[0] == 'msgid ""'
    assert lines[1] == 'msgstr ""'
    lines = lines[2:]
    # Skip PO/POT header fields until we hit first 'msgid':
    #   "Project-Id-Version: Curictus 1.0\n"
    #   "Report-Msgid-Bugs-To: \n"
    #   "POT-Creation-Date: 2010-05-26 18:55+0200\n"
    #   ...
    for n in range(len(lines)):
        tokens = lines[n].split(' ', 1)
        if tokens[0] in ["msgid", "msgid_plural"]:
            lines = lines[n:]
            break
    else:
        lines = []
    # Join multi-line strings into a single line:
    # before:
    #   msgid ""
    #   "Bottle\n"
    #   "\n"
    #   "Pen\n"
    # after:
    #   msgid "Bottle\n\nPen\n"
    # 
    joined = []
    for line in lines:
        if line[0] == '"':
            token, data = joined[-1].split(' ', 1)
            data = '"' + data.strip('"') + line.strip('"')
            joined[-1] = token + " " + data
        else:
            joined.append(line)
    lines = joined
    # Split each line into two tokens, [msgid|msgstr|...] and the quoted
    # original/translated strings: 'msgid "foo"' => ['msgid', '"foo"']
    data = [line.split(' ', 1) for line in lines]
    singular, plural = {}, {}
    while data:
        # Expected (filtered) POT/POT message format:
        #   singluar:
        #     [1] msgid "original"
        #     [2] msgstr "translated"
        #   plural:
        #     [1] msgid "original1"
        #     [2] msgid_plural "orignal2"
        #     [3] msgstr[0] "translated1"
        #     [4] msgstr[1] "translated2"    
        orig_singular, trans_singular = None, None
        orig_plural, trans_plural = None, None        
        if data[0][0] == u"msgid":
            assert len(data) >= 2
            orig_singular = data[0][1].strip('"')
            if data[1][0] == u"msgid_plural":
                assert len(data) >= 4
                orig_plural = data[1][1].strip('"')
                assert data[2][0] == u"msgstr[0]"
                trans_singular = data[2][1].strip('"')
                assert data[3][0] == u"msgstr[1]"
                trans_plural = data[3][1].strip('"')
                data = data[4:]
                singular[orig_singular] = trans_singular
                plural[orig_plural] = trans_plural
            else:
                assert data[1][0] == u"msgstr"
                trans_singular = data[1][1].strip('"')
                data = data[2:]
                if not orig_singular and not trans_singular:
                    continue
                singular[orig_singular] = trans_singular
        else:
            data = data[1:]
            continue
    package = {u"singular":singular, u"plural":plural}
    open(outfile, "wt").write(simplejson.dumps(package).encode("utf-8"))

    
def enumfiles(rootdir):
    """
    List all files in ``rootdir`` and it's sub-folders matching extensions
    listed in ``SCAN_EXT``.
    """
    for (dirpath, dirnames, filenames) in os.walk(rootdir):
        for filename in filenames:
            if any([fnmatch.fnmatch(filename, "*.%s" % ext) for ext in SCAN_EXT]):
                yield os.path.join(dirpath, filename)


def collect(sources, outfile):
    """
    Collect and filter source code (so that can be parsed by xgettext) from
    ``sources``, which is a list of files or directories, and write merged
    content to ``outfile``.
    """
    output = open(outfile, "wt")
    def filter_file(filepath):
        for line in open(filepath).readlines():
            line = HTML_RE.sub(r"", line)
            line = MXML_RE.sub(r"", line)
            output.write(line)
    for src in sources:
        if os.path.isdir(src):
            for filepath in enumfiles(src):
                filter_file(filepath)
        else:
            filter_file(src)


def fix_package_version(filename):
    """
    Forcefully set the 'Project-Id-Version' header in ``filename`` (PO/POT)
    to get rid of stupid runtime warnings.
    """
    content = open(filename).read().decode('utf-8')
    content = content.replace("Project-Id-Version: PACKAGE VERSION",
                              "Project-Id-Version: Curictus 1.0")
    open(filename, "wt").write(content.encode('utf-8'))
    

def set_catalog_encoding(filename, src_encoding, new_encoding):
    """
    Setup encoding for message catalog ``filename`` which we know is encoded as
    ``src_encoding`` (but not explictely set in the PO/POT file, it defalts to
    charset=CHARSET) by re-encoding it and writing the appropriate header for
    ``new_encoding``.
    """
    assert src_encoding.lower() in ['utf-8', 'iso-8859-1', 'cp1252']
    assert new_encoding.lower() in ['utf-8', 'iso-8859-1', 'cp1252']
    content = open(filename).read().decode(src_encoding.lower())
    content = content.replace("Content-Type: text/plain; charset=CHARSET",
                              "Content-Type: text/plain; charset=%s" % new_encoding.upper())
    open(filename, "wt").write(content.encode(new_encoding.lower()))

    
def encode_catalog(filename, src_encoding, new_encoding):
    """
    Re-encode message catalog ``filename`` encoding from ``src_encoding`` to ``new_encoding``
    (where both are one of UTF-8, ISO-8859-1 or CP1252).
    """
    assert src_encoding.lower() in ['utf-8', 'iso-8859-1', 'cp1252']
    assert new_encoding.lower() in ['utf-8', 'iso-8859-1', 'cp1252']
    content = open(filename).read().decode(src_encoding.lower())
    content = content.replace("Content-Type: text/plain; charset=%s" % src_encoding.upper(),
                              "Content-Type: text/plain; charset=%s" % new_encoding.upper())
    open(filename, "wt").write(content.encode(new_encoding.lower()))

    
def pot_update(sources, domain):
    """
    Update or initialize a project template ``domain`` for source code in
    ``sources``. When finished, a file named $(domain).pot will be available in
    the current directory.
    """
    inputfile = ".msgcache"
    collect(sources, inputfile)
    potfile = domain + ".pot"
    if not os.path.exists(potfile):
        run("xgettext --no-wrap --no-location --from-code=iso-8859-1 --language=Python --keyword=_:1,2 -s --force-po -d %s -o %s %s" % (domain, potfile, inputfile))
        fix_package_version(potfile)
        set_catalog_encoding(potfile, "ISO-8859-1", "UTF-8")
    else:
        tempfile = "changes.po"
        run("xgettext --no-wrap --no-location --from-code=iso-8859-1 --language=Python --keyword=_:1,2 -s --force-po -d %s -o %s %s" % (domain, tempfile, inputfile))
        fix_package_version(tempfile)
        set_catalog_encoding(tempfile, "ISO-8859-1", "UTF-8")
        run("msgmerge --no-wrap -s -N -U %s %s" % (potfile, tempfile))
        os.remove(tempfile)
    os.remove(inputfile)

    
def locale_update(lang, domain):
    """
    Update or initialize a message catalog ``domain`` for the locale ``lang``
    in the directory. When finshed a catalog file and a compiled message file
    will be available in: ./$(lang)/LC_MESSAGES/$(domain).[po|mo]
    """
    po_dir = "./%s/LC_MESSAGES" % lang
    if not os.path.exists(po_dir):
        os.makedirs(po_dir)
    po_file = os.path.join(po_dir, "%s.po" % domain)
    if not os.path.isfile(po_file):
        run("msginit --no-wrap -l %s --no-translator -i %s.pot -o %s" % (lang, domain, po_file))
        fix_package_version(po_file)
        encode_catalog(po_file, "CP1252", "UTF-8")
    run("msgmerge --no-wrap -s -N -U ./%s/LC_MESSAGES/%s.po %s.pot" % (lang, domain, domain))
    run("msgfmt -c -o ./%s/LC_MESSAGES/%s.mo ./%s/LC_MESSAGES/%s.po" % (lang, domain, lang, domain))
    savejson("./%s/LC_MESSAGES/%s.po" % (lang, domain), "./%s/LC_MESSAGES/%s.json" % (lang, domain))

        
##############################################################################
# Unit test.
##############################################################################

TEST_SOURCE = """
  _("Pen"),
  _("Fish", "Fishes", 1),
  _("Bottle\n\nPen\n"),
  _("Multi\nLine\n With\nSpace \n", "Multi\nLines\n  With\n  Spaces \n"),
  _("Cat\nAnd\nDog\n", "Cats\nAnd\nDogs\n", 2),

  <mx:Label text="{_('XPen')}"),
  <mx:Label text="{_('XFish', 'XFishes')}"),
  <mx:Label text="{_('XBottle\n\nXPen\n')}"),
  <mx:Label text="{_('XMulti\nXLine\n XWith\nXSpace \n', 'XMulti\nXLines\n  XWith\n  XSpaces \n')}"),
  <mx:Label text="{_('XCat\nXAnd\nXDog\n', 'XCats\nXAnd\nXDogs\n')}"),
"""

##############################################################################
# Application entry-point.
##############################################################################
        
if __name__ == "__main__":
    sources = sys.argv[1:]
    pot_update(sources, DOMAIN)
    for lang in LANGUAGES:
        locale_update(lang, DOMAIN)

        
##############################################################################
# The End.
##############################################################################
