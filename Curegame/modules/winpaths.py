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

from ctypes import windll, wintypes, c_int

# These constants were imported from shlobj.h

CSIDL_APPDATA                  = 0x1a   # C:\Users\%USERNAME%\AppData\Roaming
CSIDL_COMMON_APPDATA           = 0x23   # C:\ProgramData
CSIDL_COMMON_DESKTOPDIRECTORY  = 0x19   # C:\Users\Public\Desktop
CSIDL_COMMON_DOCUMENTS         = 0x2e   # C:\Users\Public\Documents
CSIDL_COMMON_FAVORITES         = 0x1f   # C:\Users\%USERNAME%\Favorites
CSIDL_COMMON_MUSIC             = 0x35   # C:\Users\Public\Music
CSIDL_COMMON_PICTURES          = 0x36   # C:\Users\Public\Pictures
CSIDL_COMMON_PROGRAMS          = 0x17   # C:\ProgramData\Microsoft\Windows\Start Menu\Programs
CSIDL_COMMON_STARTMENU         = 0x16   # C:\ProgramData\Microsoft\Windows\Start Menu
CSIDL_COMMON_STARTUP           = 0x18   # C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup
CSIDL_COMMON_VIDEO             = 0x37   # C:\Users\Public\Videos
CSIDL_COOKIES                  = 0x21   # C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Cookies
CSIDL_DESKTOPDIRECTORY         = 0x10   # C:\Users\%USERNAME%\Desktop
CSIDL_FAVORITES                = 0x6    # C:\Users\%USERNAME%\Favorites
CSIDL_FONTS                    = 0x14   # C:\Windows\Fonts
CSIDL_HISTORY                  = 0x22   # C:\Users\%USERNAME%\AppData\Local\Microsoft\Windows\History
CSIDL_INTERNET_CACHE           = 0x20   # C:\Users\%USERNAME%\AppData\Local\Microsoft\Windows\Temporary Internet Files
CSIDL_LOCAL_APPDATA            = 0x1c   # C:\Users\%USERNAME%\AppData\Local
CSIDL_MYDOCUMENTS              = 0x5    # C:\Users\%USERNAME%\Documents
CSIDL_MYMUSIC                  = 0xd    # C:\Users\%USERNAME%\Music
CSIDL_MYPICTURES               = 0x27   # C:\Users\%USERNAME%\Pictures
CSIDL_MYVIDEO                  = 0xe    # C:\Users\%USERNAME%\Videos
CSIDL_PERSONAL                 = 0x5    # C:\Users\%USERNAME%\Documents
CSIDL_PROFILE                  = 0x28   # C:\Users\%USERNAME%
CSIDL_PROGRAM_FILES            = 0x26   # C:\Program Files (x86)
CSIDL_PROGRAM_FILESX86         = 0x2a   # C:\Program Files (x86)
CSIDL_PROGRAM_FILES_COMMON     = 0x2b   # C:\Program Files (x86)\Common Files
CSIDL_PROGRAM_FILES_COMMONX86  = 0x2c   # C:\Program Files (x86)\Common Files
CSIDL_SENDTO                   = 0x09   # C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\SendTo
CSIDL_SYSTEM                   = 0x25   # C:\Windows\system32
CSIDL_SYSTEMX86                = 0x29   # C:\Windows\SysWOW64
CSIDL_WINDOWS                  = 0x24   # C:\Windows

SHGetFolderPath = windll.shell32.SHGetFolderPathW
SHGetFolderPath.argtypes = [
    wintypes.HWND,
    c_int,
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPCWSTR]

def getpath(csidl):
    path = wintypes.create_unicode_buffer(wintypes.MAX_PATH)
    result = SHGetFolderPath(0, csidl, 0, 0, path)
    return path.value
