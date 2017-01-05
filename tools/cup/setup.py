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
import compileall
import shutil
import subprocess
import tarfile
import re

from distutils.core import setup
import py2exe

sys.argv.append('py2exe')

###########################################################################
# Global configuration.
###########################################################################

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

SVN_BIN  = os.path.abspath("../svn-win32-1.6.15/bin/")

NSIS_BIN = os.path.abspath("../nsis-2.46/")

CUP_SVN_PATH = ROOT_DIR

VRS_SVN_PATH = os.path.join(ROOT_DIR, "../../Curegame")

VRS_EXPORT_DIR = "VRS"

VRS_EXPORT_PATH = os.path.join(ROOT_DIR, VRS_EXPORT_DIR)

CUP_CFG = os.path.join(ROOT_DIR, "cup.cfg")

BUILD_CFG = os.path.join(ROOT_DIR, "build.cfg")

sys.path.append(os.path.join(VRS_SVN_PATH, "modules"))
from vrs.util.path import rmtree, mkdir

###########################################################################
# Load configuration.
###########################################################################

# Load private configuration for building and uploding installer/archive
# (AWS API keys, private DSA keys, etc and other information which shouldn't
# leave the build machine goes here).
from vrs.config import BuildConfig
config = BuildConfig(BUILD_CFG)

# Public configuration which is packaged along the CUP installer (release
# channel, public DSA keys, etc and other information which CUP needs to be
# able to update a client goes here). We'll load it to make sure it's valid.
from vrs.config import UpdateConfig
ignore = UpdateConfig(CUP_CFG)

###########################################################################
# Retrieve SVN revisions.
###########################################################################

# Parse revision data via `svnversion` output (ex:'358:362MS'). Note: we'll use
# -c flag to retrieve the highest commited revision for a folder instead of the
# global repository revision number.

def get_svnrev(path):
    return subprocess.Popen("%s/svnversion -n -c %s" % (SVN_BIN, path),
                            stdout=subprocess.PIPE).communicate()[0]\
                            .strip().split(':')[-1].rstrip('MS')

CUP_SVN_REV = get_svnrev(CUP_SVN_PATH)
VRS_SVN_REV = get_svnrev(VRS_SVN_PATH)

###########################################################################
# CUP installer configuration.
###########################################################################

AUTHOR_EMAIL       = "support@curictus.se"
AUTHOR_NAME        = "Curictus"
AUTHOR_URL         = "http://www.curictus.se/"
COPYRIGHT          = "Copyright (C) 2011 Curictus"
DEST_BASE          = "cup"
DIST_DIR           = "dist"
ICON_FILE          = "setup.ico"
INSTALLER_SCRIPT   = "setup.nsi"
INSTALLER_EXE      = "cup.exe"
INSTALLER_SIGNFILE = "cup.exe.sign"
MAIN_SCRIPT        = "main.py"
PRODUCT_NAME       = "Curictus Update"
VERSION            = CUP_SVN_REV
VERSIONSTRING      = "%s %s" % (PRODUCT_NAME, VERSION)
VERSIONFILE        = "version.txt"

###########################################################################
# VRS archive configuration.
###########################################################################

from vrs.config import Config

VRS_ARCHIVE     = "vrs.tar.bz2"
VRS_VERSION     = "%s.%s" % (Config.SYSTEM_VERSION, VRS_SVN_REV)
VRS_VERSIONFILE = os.path.join(VRS_EXPORT_PATH, "version.txt")
VRS_SKIPEXT     = (".tif", ".psd", ".blend", ".log")
VRS_PRECOMPILE  = ()
VRS_SIGNFILE    = "vrs.tar.bz2.sign"

###########################################################################
# Prepare clean build envrionment.
###########################################################################
        
if os.path.exists(DIST_DIR):
    rmtree(DIST_DIR)
    mkdir(DIST_DIR)

if os.path.exists(VRS_EXPORT_PATH):
    rmtree(VRS_EXPORT_PATH)

CLEANUP_FILES = [
    INSTALLER_SCRIPT,
    INSTALLER_EXE,
    INSTALLER_SIGNFILE,
    VRS_ARCHIVE,
    VRS_SIGNFILE,
]

for filename in CLEANUP_FILES:
    if os.path.exists(filename):
        os.remove(filename)

###########################################################################
# Generate standalone CUP executable using Py2exe.
###########################################################################

# Write out version information to be packaged in installer.
open(VERSIONFILE, "wt").write(VERSION)

# Manually copy helper DLL dependency to build folder.
shutil.copyfile(os.path.join(VRS_SVN_PATH, "bin", "win32util.dll"), "win32util.dll")

setup(
    windows = [{
        "dest_base"       : DEST_BASE,
        "script"          : MAIN_SCRIPT,
        "other_resources" : [(u"VERSIONTAG", 1, VERSIONSTRING)],
        "icon_resources"  : [(1, ICON_FILE)],
        "copyright"       : COPYRIGHT,
    }],

    zipfile = None,

    data_files = [
        ("", [ICON_FILE, "win32util.dll", "splash_logo.png", "splash_ticker.png", CUP_CFG, config.PUBKEYFILE, VERSIONFILE]),
    ],

    options = {
        "py2exe" : {
            "packages"     : ["amfast", "simplejson", "tornado", "sqlalchemy", "email", "xml", "xml.dom"],
            "excludes"     : ["Tkconstants", "Tkinter", "tcl", "psycopg2"],
            "compressed"   : False,
            "bundle_files" : 2,
            "dll_excludes" : ["w9xpopen.exe"],
            "dist_dir"     : DIST_DIR,
        }
    },

    name         = PRODUCT_NAME,
    version      = VERSION,
    author       = AUTHOR_NAME,
    author_email = AUTHOR_EMAIL,
    url          = AUTHOR_URL
)
    
###########################################################################
# Build silent installer for CUP using NSIS.
###########################################################################

NSIS_SCRIPT = """\
!define DistDir '%(DIST_DIR)s'
!define PythonExe '%(DEST_BASE)s.exe'

OutFile ${PythonExe}

Name '%(AUTHOR_NAME)s'
Icon '%(ICON_FILE)s'
RequestExecutionLevel admin
SetCompressor 'lzma' ; Off
SilentInstall silent

Section
    InitPluginsDir
    SetOutPath 'D:\CUP\%(VERSION)s'
    File /r '${DistDir}\*.*'
    Exec '"D:\CUP\%(VERSION)s\${PythonExe}"'
SectionEnd
"""

open(INSTALLER_SCRIPT, "wt").write(
    NSIS_SCRIPT % {
        "DIST_DIR"    : DIST_DIR,
        "DEST_BASE"   : DEST_BASE,
        "AUTHOR_NAME" : AUTHOR_NAME,
        "ICON_FILE"   : ICON_FILE,
        "VERSION"     : VERSION,
        })

subprocess.call("%s/makensis.exe setup.nsi" % NSIS_BIN)

os.rename(DEST_BASE + ".exe", INSTALLER_EXE)

###########################################################################
# Package VRS build.
###########################################################################

def filter_ext(tarinfo):
    """
    Stop unwanted files from being added to archive.
    """
    if os.path.splitext(tarinfo.name)[1].lower() in VRS_SKIPEXT:
        print "-", tarinfo.name
        return None
    elif tarinfo.isdir() and os.path.split(tarinfo.name)[1][:1] == ".":
        print "-", tarinfo.name
        return None        
    else:
        print "+", tarinfo.name
        return tarinfo

    
def compressdir_bz2(path, archive):
    """
    Generate .tar.b2 at ``archive`` for all files in ``path`.
    """
    tar = tarfile.open(archive, "w:bz2")
    tar.add(path, recursive=True, filter=filter_ext)
    tar.close()

    
def precompile(path):
    """
    Precompile and delete all *.py files recursively in ``path`` so that we
    only end up with *.pyc files.
    """
    compileall.compile_dir(path, rx=re.compile('/[.]svn'), force=True, quiet=True)
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            if os.path.splitext(filename)[1].lower() == ".py":
                filepath = os.path.join(dirpath, filename) 
                print "-", filepath
                os.remove(filepath)

# 1. Export clean copy from SVN to be preprocessed and packaged.                
print subprocess.Popen("%s/svn export %s %s" % (SVN_BIN, VRS_SVN_PATH, VRS_EXPORT_PATH),
                       stdout=subprocess.PIPE).communicate()[0]

# 2. Write out version information to be packaged in archive.
open(VRS_VERSIONFILE, "wt").write(VRS_VERSION)

# 3. Precompile selected parts for security and copy-protection purposes.
for dirname in VRS_PRECOMPILE:
    precompile(os.path.join(VRS_EXPORT_PATH, dirname))

# 4. Generate archive of VRS distribution.
cwd = os.getcwd()
try:
    os.chdir(ROOT_DIR)
    compressdir_bz2(VRS_EXPORT_DIR, VRS_ARCHIVE)
finally:
    os.chdir(cwd)

###########################################################################
# Sign CUP installer and VRS package using private key.
###########################################################################

from vrs.util import crypto

open(INSTALLER_SIGNFILE, "wt").write(
    crypto.sign(config.PRIVKEYFILE,
                open(INSTALLER_EXE, "rb").read()))

open(VRS_SIGNFILE, "wt").write(
    crypto.sign(config.PRIVKEYFILE,
                open(VRS_ARCHIVE, "rb").read()))

assert crypto.verify(config.PUBKEYFILE,
                     open(INSTALLER_EXE, "rb").read(),
                     open(INSTALLER_SIGNFILE, "rt").read())

assert crypto.verify(config.PUBKEYFILE,
                     open(VRS_ARCHIVE, "rb").read(),
                     open(VRS_SIGNFILE, "rt").read())

###########################################################################
# Upload CUP installer and VRS archive to S3.
###########################################################################

from boto.s3.connection import S3Connection
from boto.s3.key import Key

c = S3Connection(config.AWS_ACCESS_KEY, config.AWS_SECRET_KEY)
b = c.get_bucket(config.AWS_BUCKET)

def upload(key, filename):
    print "Uploading", filename, "to", key
    k = Key(b)
    k.key = key
    k.set_contents_from_filename(filename, reduced_redundancy=True)
    k.make_public()

# CUP installer.

# 1. Make new installer avilable first.
upload("/%s/cup/%s/%s" % (config.UPDATE_CHANNEL, VERSION, INSTALLER_EXE),      INSTALLER_EXE)
upload("/%s/cup/%s/%s" % (config.UPDATE_CHANNEL, VERSION, INSTALLER_SIGNFILE), INSTALLER_SIGNFILE)
upload("/%s/cup/%s/%s" % (config.UPDATE_CHANNEL, VERSION, VERSIONFILE),        VERSIONFILE)

# 2. Switch version check to point to new installer.
if config.UPDATE_CHANNEL == 'dev':
    upload("/%s/cup/%s" % (config.UPDATE_CHANNEL, VERSIONFILE), VERSIONFILE)

# 3. Lastly expose the new installer to new stations.
upload("/%s/cup/latest/%s" % (config.UPDATE_CHANNEL, INSTALLER_EXE),      INSTALLER_EXE)
upload("/%s/cup/latest/%s" % (config.UPDATE_CHANNEL, INSTALLER_SIGNFILE), INSTALLER_SIGNFILE)

# VRS archive.

# 1. Make new archive avilable first.
upload("/%s/vrs/%s/%s" % (config.UPDATE_CHANNEL, VRS_VERSION, VRS_ARCHIVE),  VRS_ARCHIVE)
upload("/%s/vrs/%s/%s" % (config.UPDATE_CHANNEL, VRS_VERSION, VRS_SIGNFILE), VRS_SIGNFILE)
upload("/%s/vrs/%s/%s" % (config.UPDATE_CHANNEL, VRS_VERSION, os.path.split(VRS_VERSIONFILE)[1]), VRS_VERSIONFILE)

# 2. Switch version check to point to new archive.
if config.UPDATE_CHANNEL == 'dev':
    upload("/%s/vrs/%s" % (config.UPDATE_CHANNEL, os.path.split(VRS_VERSIONFILE)[1]), VRS_VERSIONFILE)

###########################################################################
# Post cleanup.
###########################################################################

if os.path.exists("build"):
    rmtree("build")
    
###########################################################################
# The End.
###########################################################################
