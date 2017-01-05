//////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2006-2011 Curictus AB.
//
// This file part of Curictus VRS.
//
// Curictus VRS is free software; you can redistribute it and/or modify it under
// the terms of the GNU General Public License as published by the Free Software
// Foundation; either version 2 of the License, or (at your option) any later
// version.
//
// Curictus VRS is distributed in the hope that it will be useful, but WITHOUT ANY
// WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
// PARTICULAR PURPOSE.  See the GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License along with
// Curictus VRS; if not, write to the Free Software Foundation, Inc., 59 Temple
// Place, Suite 330, Boston, MA 02111-1307 USA
//
//////////////////////////////////////////////////////////////////////////////

#ifndef CURICTUS_COMMON_PRECOMPILED_H
#define CURICTUS_COMMON_PRECOMPILED_H

///////////////////////////////////////////////////////////////////////////////////////////////////
// Configure 32/64bit helper macros.
///////////////////////////////////////////////////////////////////////////////////////////////////

#ifdef PLATFORM_X86
#undef PLATFORM_X86
#endif

#ifdef PLATFORM_X64
#undef PLATFORM_X64
#endif

#if defined(_M_AMD64) || defined(WIN64) || defined(_WIN64)
#pragma message("Configuring target platform as x86-64 Win64")
#define PLATFORM_X64
#else
#pragma message("Configuring target platform as x86 Win32")
#define PLATFORM_X86
#endif

///////////////////////////////////////////////////////////////////////////////////////////////////
// Fixes to generate manifests which allow for deployment of debug builds.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// This section is required to ensure that the manifests are correctly
// generated for deployment of the product onto non development machines.
// They must be defined first. They are particularly important for debug
// deployments. They must be set in all linked-to targets as well as the
// present one.For targets that do not use pre-compiled headers, they must
// be specified at the top of every code module.
//

#ifdef _BIND_TO_CURRENT_MFC_VERSION
#undef _BIND_TO_CURRENT_MFC_VERSION
#endif

#ifdef _BIND_TO_CURRENT_CRT_VERSION
#undef _BIND_TO_CURRENT_CRT_VERSION
#endif

#define _BIND_TO_CURRENT_MFC_VERSION 1
#define _BIND_TO_CURRENT_CRT_VERSION 1

__declspec(selectany)       int _forceCRTManifestRTM;
__declspec(selectany)       int _forceMFCManifestRTM;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Configure Platform SDK.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// 32 bit support is from Win2k and above.
//

#ifdef PLATFORM_X86

#ifndef WINVER
#define WINVER _WIN32_WINNT_WIN2K
#endif

#ifndef _WIN32_WINNT
#define _WIN32_WINNT _WIN32_WINNT_WIN2K
#endif

#ifndef _WIN32_WINDOWS
#define _WIN32_WINDOWS _WIN32_WINNT_WIN2K
#endif

#endif // PLATFORM_X86

//
// 64 bit support is from WinXP and above.
//

#ifdef PLATFORM_X64

#ifndef WINVER
#define WINVER _WIN32_WINNT_WINXP
#endif

#ifndef _WIN32_WINNT
#define _WIN32_WINNT _WIN32_WINNT_WINXP
#endif

#ifndef _WIN32_WINDOWS
#define _WIN32_WINDOWS _WIN32_WINNT_WINXP
#endif

#endif // PLATFORM_X64

//
// Forcefully enable Unicode if necessary.
//

#ifndef UNICODE
#define UNICODE
#endif

#ifndef _UNICODE
#define _UNICODE
#endif

#define WIN32_LEAN_AND_MEAN
#pragma warning(push, 3)
#include <crtdbg.h>
#include <errno.h>
#include <windows.h>
#include <process.h>
#include <tchar.h>
#include <shlwapi.h>
#include <comdef.h>
#pragma warning(pop)

///////////////////////////////////////////////////////////////////////////////////////////////////
// Disable unwanted warnings (level 4).
///////////////////////////////////////////////////////////////////////////////////////////////////

#pragma warning(disable:4355) // 'this' : used in base member initializer list

///////////////////////////////////////////////////////////////////////////////////////////////////
// Include STL/TR1 headers.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include <stdexcept>
#include <memory>
#include <type_traits>
#include <algorithm>

#include <string>
#include <sstream>

#include <list>
#include <vector>
#include <deque>

#include <set>
#include <map>

#include <unordered_map>
#include <unordered_set>

#include <array>

///////////////////////////////////////////////////////////////////////////////////////////////////
// Common "documentation" macros.
///////////////////////////////////////////////////////////////////////////////////////////////////

#ifdef FORBID_DEFAULT_CTOR
#undef FORBID_DEFAULT_CTOR
#endif

#ifdef FORBID_COPY_CTOR
#undef FORBID_COPY_CTOR
#endif

#ifdef FORBID_ASSIGNMENT
#undef FORBID_ASSIGNMENT
#endif

#ifdef UNREFERENCED_PARAMETER
#undef UNREFERENCED_PARAMETER
#endif

// Disallows the compiler defined default ctor.
#define FORBID_DEFAULT_CTOR(x) x();

// Disallows the compiler defined copy ctor.
#define FORBID_COPY_CTOR(x)    x(const x&);

// Disallows the compiler defined assignment operator.
#define FORBID_ASSIGNMENT(x)   void operator=(const x&);

// Remove warnings about unused arguments.
#define UNREFERENCED_PARAMETER(arg) (void)(arg);

///////////////////////////////////////////////////////////////////////////////////////////////////
// Include common headers shared in all projects.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include "DebugTools.h"

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_COMMON_PRECOMPILED_H