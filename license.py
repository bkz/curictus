import os

###########################################################################
# Global configuration (see PATCH_DIRS below to setup source-code paths).
###########################################################################

COMPANY   = "Curictus AB"
COPYRIGHT = "Copyright (c) 2006-2011 %s." % COMPANY
PRODUCT   = "Curictus VRS"


###########################################################################
# GPL template.
###########################################################################

GPL_HEADER ="""\
# %(copyright)s
#
# This file part of %(product)s.
#
# %(product)s is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# %(product)s is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# %(product)s; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
""" % { "copyright" : COPYRIGHT, "product" : PRODUCT }


###########################################################################
# BSD template.
###########################################################################

BSD_HEADER ="""\
# %(copyright)s
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
""" % { "copyright" : COPYRIGHT }


###########################################################################
# Langauge specific formatting of license headers.
###########################################################################

BSD_HEADER_PY = (78 * '#') + "\n#\n" + BSD_HEADER + "#\n" + (78 * '#') + "\n\n"
GPL_HEADER_PY = (78 * '#') + "\n#\n" + GPL_HEADER + "#\n" + (78 * '#') + "\n\n"

BSD_HEADER_AS3 = (78 * '/') + "\n//\n" + BSD_HEADER.replace("#", "//") + "//\n" + (78 * '/') + "\n\n"
GPL_HEADER_AS3 = (78 * '/') + "\n//\n" + GPL_HEADER.replace("#", "//") + "//\n" + (78 * '/') + "\n\n"

BSD_HEADER_CPP = (78 * '/') + "\n//\n" + BSD_HEADER.replace("#", "//") + "//\n" + (78 * '/') + "\n\n"
GPL_HEADER_CPP = (78 * '/') + "\n//\n" + GPL_HEADER.replace("#", "//") + "//\n" + (78 * '/') + "\n\n"


###########################################################################
# License header patching.
###########################################################################

# Minimum length of the first commented line part of a license header.
HEADER_FIRST_LINE_MIN_CHARS = 50

# Minimum size of comment block for us to assume it's as license header.
HEADER_MIN_LINE_COUNT = 15

# Preserve these lines at the beginning of source files.
KEEP_MAGIC_LINES_STARTS_WITH = [
    "#!",
    "# coding=",
    "# -*- coding:",
    "# vim:",
]

def patch_license(filename, header):
    """
    Append or replace comment (license) ``header`` in ``filename`` while
    preserving any magic lines at the begining. Note: the first character from
    ``header`` is assumed to be comment character for the file type!
    """
    comment_char = header[0]
    content = open(filename, "rt").read()
    # Chop off magic lines in the beginning (#!/bin/sh, or encoding) and keep
    # them separate from the content we intend to parse. The patched file
    # always have these line in the beginning independent if we replace or
    # append a license header.
    magic_lines = ""
    for line_prefix in KEEP_MAGIC_LINES_STARTS_WITH:
        if content.startswith(line_prefix):
            offset = content.index("\n")
            magic_lines += content[:offset+1] # Keep newline.
            content = content[offset+1:]      # Skip newline.
    if magic_lines:
        magic_lines += "\n"
    # Skip empty lines until we hit the code/comments.
    while content[:1] in [' ', '\r', '\n', '\t']:
        content = content[1:]
    # Try to determine if there already exist a header by looking for a
    # continous stream of commented lines at the beginning of the file. If the
    # block is large enough we asume that we can safely replace it.
    if content.startswith(comment_char * HEADER_FIRST_LINE_MIN_CHARS):
        offset, count = 0, 0
        while content[offset] == comment_char:
            k = content.find("\n", offset)
            if k == -1:
                break
            else:
                offset = k+1
                count += 1
        if count > HEADER_MIN_LINE_COUNT:
            content = content[offset:]
    # Skip empty lines until we hit the code, the header will include a
    # newline delimter at the end which is all we need.
    while content[:1] in [' ', '\r', '\n', '\t']:
        content = content[1:]
    content = magic_lines + header + content
    open(filename, "wt").write(content)


def sanitize_path(s):
    """
    Return cleaned path from ``s`` without any mixed path separators.
    """
    return os.path.abspath(os.path.normpath(s))


def enum_files(rootdir, ext=[], skip_paths=[], recursive=True, ignore_dirs=[".svn"]):
    """
    Enumerate (yeld) files recursively in `rootdir` matching extensions list
    ``ext`` (include dots like .py) ignoring ``skip_paths``. If ``recursive``
    is False we'll only lists files in the root directory. Optionally include
    folder names in ``ignore_dirs`` to ignore git/svn folders etc.

    Ex:
      enum_files("/var/log", ext=[".log"], skip_paths=["/var/log/mysql"])
        -> ['/var/log/foo.log', '/var/log/bar.log', ...]
    """
    ext = [e.lower() for e in ext]
    rootdir = sanitize_path(rootdir)
    skip_paths = [sanitize_path(p) for p in skip_paths]
    for (dirpath, dirnames, filenames) in os.walk(rootdir):
        if dirpath in skip_paths:
            dirnames[:] = []
            continue
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() in ext:
                yield os.path.join(dirpath, filename)
        if recursive:
            for ignore in ignore_dirs:
                if ignore in dirnames:
                    dirnames.remove(ignore)
        else:
            break


###########################################################################
# Program entry-point.
###########################################################################

PATCH_CONFIG = [
    # root folder             file-exts       license header   recursive?    skip paths
    # -----------             ---------       --------------   ----------    ----------
    ("./Curegame",            [".py"],        BSD_HEADER_PY,   False,        []),
    ("./Curegame/activities", [".py"],        GPL_HEADER_PY,   True,         []),
    ("./Curegame/dashboard",  [".py"],        GPL_HEADER_PY,   True,         []),
    ("./Curegame/modules",    [".py"],        BSD_HEADER_PY,   True,         []),
    ("./Curegame/test",       [".py"],        BSD_HEADER_PY,   True,         []),
    ("./flex",                [".as"],        BSD_HEADER_AS3,  True,         ["./flex/lib/com",
                                                                              "./flex/PCMS/src/gs",
                                                                              "./flex/PCMS/src/nl",
                                                                              "./flex/PCMS/src/org"]),
    ("./media",               [".py"],        BSD_HEADER_PY,   True,         []),
    ("./tools/amender",       [".py"],        BSD_HEADER_PY,   True,         []),
    ("./tools/amender",       [".py"],        BSD_HEADER_PY,   True,         []),
    ("./tools/audio_monitor", [".py"],        BSD_HEADER_PY,   True,         []),

    ("./tools/blender-2.57b/2.57/scripts/addons/io_scene_hgt",
                              [".py"],        GPL_HEADER_PY,   False,        []),

    ("./tools/cup",           [".py"],        BSD_HEADER_PY,   True,         []),
    ("./tools/display",       [".cpp", ".h"], BSD_HEADER_CPP,  True,         []),
    ("./tools/h3dload",       [".cpp", ".h"], GPL_HEADER_CPP,  True,         ["./tools/h3dload/debugtools/dbghelp"]),
    ("./tools/hardwareid",    [".py"],        BSD_HEADER_PY,   True,         []),
    ("./tools/phantominfo",   [".cpp", ".h"], BSD_HEADER_CPP,  True,         ["./tools/phantominfo/include",
                                                                              "./tools/phantominfo/src/HDU"]),
    ("./tools/win32util",     [".cpp", ".h"], BSD_HEADER_CPP,  True,         []),
    ("./tools/vrscalib",      [".py"],        GPL_HEADER_PY,   True,         []),
]

def main():
    for (rootdir, ext, header, recursive, skip_paths) in PATCH_CONFIG:
        for filename in enum_files(rootdir, ext, skip_paths, recursive=recursive):
            print "Patching:", filename
            patch_license(filename, header)


if __name__ == '__main__':
    main()


###########################################################################
# The End.
###########################################################################
