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

#ifndef CURICTUS_COMMON_DEBUG_TOOLS_H
#define CURICTUS_COMMON_DEBUG_TOOLS_H

///////////////////////////////////////////////////////////////////////////////////////////////////
// Debug tools public API (documentation is inlined with the function definitions).
///////////////////////////////////////////////////////////////////////////////////////////////////

enum
{
	DEBUG_TOOLS_CALLBACK_TRACE_DEBUG,
	DEBUG_TOOLS_CALLBACK_TRACE_WARNING,
	DEBUG_TOOLS_CALLBACK_TRACE_ERROR,
};

/// Generic hook to customize and redirect trace output and error messages.
/// Note: pwszMessage is always a complete line and doesn't end with a newline.
typedef void(*DEBUG_TOOLS_OUTPUT_CALLBACK)(DWORD dwCallbackType, const wchar_t* pwszMessage);

/// Generic callback for reporting a program crash to the user when DebugTools has detected
/// a fatal error (triggered after we have recorded a minidump and are about to terminate the
/// application). If you want to display a error message to the user or upload crash report,
/// this callback is the preferred way of doing so.
typedef void(*DEBUG_TOOLS_CRASH_CALLBACK)(const wchar_t* pwszErrorMessage);

namespace DebugTools
{
void Install(DEBUG_TOOLS_OUTPUT_CALLBACK pOutputCallback = NULL, DEBUG_TOOLS_CRASH_CALLBACK pCrashCallback = NULL);
void ShowConsole();
void SetMinidumpStoragePath(const std::wstring& path);
void FatalError(const wchar_t* pwszReason, _EXCEPTION_POINTERS * pExceptionContext = NULL);
void SetMemoryCheckPoint();
bool DumpMemoryLeaks();
void DumpMemoryStats();
void VerifyHeapIntegrity();
bool RunTest(bool(*pfnTestSetup)(), void(*pfnTestMain)(), bool(*pfnTestClean)(), int numruns = 1);
void TraceOutputDebug(const wchar_t* message);
void TraceOutputWarning(const wchar_t* message);
void TraceOutputError(const wchar_t* message);
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// Generic runtime assertion support.
///////////////////////////////////////////////////////////////////////////////////////////////////

#ifdef assert
#undef assert
#endif

// Force a write to address 0 to automatically break when running under a debugger.
// The advantage of breaking manually instead of using ::DebugBreak() is that you
// can't unintentionally step past the forced "access violation".
#define FORCE_BREAK_INTO_DEBUGGER ((*(char*)(0))=0)

namespace DebugTools
{
void AssertionFailed(const wchar_t* expr, const wchar_t* file, unsigned int line);
};

// Specialized assertion macro which allows for assert(0) without VC++
// spewing out warnings. Keeping the macro in one single line will also help
// as the macro will break at the exact location of assert statement.
#define assert(expr) (void)( (!!(expr)) || ( DebugTools::AssertionFailed( _CRT_WIDE(#expr), _CRT_WIDE(__FILE__), __LINE__ ), FORCE_BREAK_INTO_DEBUGGER, 0 ) )

///////////////////////////////////////////////////////////////////////////////////////////////////
// Static assertions for compile time checks.
///////////////////////////////////////////////////////////////////////////////////////////////////

#ifdef STATIC_ASSERT
#undef STATIC_ASSERT
#endif

namespace StaticAssert
{
template <bool condition>
struct AbortCompilationIfConditionIsFalse {};

template <>
struct AbortCompilationIfConditionIsFalse<false>;
};

#define STATIC_ASSERT(expr) StaticAssert::AbortCompilationIfConditionIsFalse<expr>();

///////////////////////////////////////////////////////////////////////////////////////////////////
// Generic type safe printf style trace support.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// The header file below implements a iostream based tracing facility which uses
// the standard printf syntax for formatting output. Three templates are implemented,
// TRACE, TRACE_WARN and TRACE_ERROR which use the DebugTools callback to output
// debug information. By default the output is redirected to stderr but this behavior
// can easily be customized by calling DebugTools::Install() with a custom callback.
//
// The main motivation for using these functions instead of fprintf is safety and code
// correctness - any type which can be formatted using the iostream << operator can be
// passed as an argument. The implementation will also catch situations where too many
// or too few arguments are passed (via runtime checks) which isn't possible using
// printf. Another big win is that there is no chance of crashes due to a mismatches in
// the format string and the actual type of arguments passed (ex: passing wstring to
// "%s"  and forgetting to call c_str()).
//
// Note:
//
// Since the trace functions output complete lines make sure that the format string
// doesn't end with newline characters...
//
// Example:
//
//     TRACE_ERROR(L"Hello %s", std::wstring(L"World"))
//

#ifdef TRACE
#undef TRACE
#endif

#ifdef TRACE_WARN
#undef TRACE_WARN
#endif

#ifdef TRACE_ERROR
#undef TRACE_ERROR
#endif

#include "Trace.h"

///////////////////////////////////////////////////////////////////////////////////////////////////
// Trace failed Win32 calls (error message and location details).
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// Example:
//
//     HANDLE h = ::LoadLibrary(L"invalid.dll");
//     if( h == NULL )
//     {
//         TRACE_WIN32_ERROR(LoadLibrary);
//        return FALSE;
//     }
//
// Output:
//
//     [10:40:53 tid:0772] ERROR: LoadLibrary failed with error message 'The specified module
//     could not be found.' in method 'main' (c:\home\research\prototype\prototype\winmain.cpp:25)
//

#ifdef TRACE_WIN32_ERROR
#undef TRACE_WIN32_ERROR
#endif

#ifdef TRACE_WIN32_ERROR_EX
#undef TRACE_WIN32_ERROR_EX
#endif

namespace DebugTools
{
void TraceOutputWin32Error(const wchar_t* win32func, DWORD dwError,
                           const wchar_t* funcname, const wchar_t* filename, int linenr);
};

#define TRACE_WIN32_ERROR(win32func) \
{ DebugTools::TraceOutputWin32Error( _CRT_WIDE(#win32func), ::GetLastError(), _CRT_WIDE(__FUNCTION__), _CRT_WIDE(__FILE__), __LINE__ ); }

#define TRACE_WIN32_ERROR_EX(win32func, dwErrCode) \
{ DebugTools::TraceOutputWin32Error( _CRT_WIDE(#win32func), dwErrCode, _CRT_WIDE(__FUNCTION__), _CRT_WIDE(__FILE__), __LINE__ ); }

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_COMMON_DEBUG_TOOLS_H