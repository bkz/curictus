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

#include "Precompiled.h"
#include "DebugTools.h"
#include "AutoCleanup.h"

#include <crtdbg.h>
#include <eh.h>
#include <signal.h>
#include <new.h>
#include <intrin.h>
#include <psapi.h>

#include <stdio.h>
#include <fcntl.h>
#include <io.h>
#include <time.h>

#ifdef PLATFORM_X64
#define _IMAGEHLP64
#endif

#ifdef PLATFORM_X86
#include "dbghelp/dbghelp.h"
#endif

#ifdef PLATFORM_X64
#include "dbghelp/dbghelp.h"
#endif

#ifdef NDEBUG
#define DEBUG_TOOLS_DISABLE_TRACK_MEMORY_ALLOC
#endif

#pragma comment(lib, "psapi.lib")

///////////////////////////////////////////////////////////////////////////////////////////////////
// Forward declarations.
///////////////////////////////////////////////////////////////////////////////////////////////////

void DefaultOutputCallbackImpl(DWORD dwType, const wchar_t* pwszMessage);
void DefaultCraschCallbackImpl(const wchar_t* pwszErrorMessage);
void VerifyAllocation(void* ptr, void* pAllocatedByAddr);

///////////////////////////////////////////////////////////////////////////////////////////////////
// Module global hooks and variables.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// The purpose of the pragma directive below is to force the global objects
// in this module to be constructed before all other objects in the program.
// For more information search MSDN for Q104248 (Use #pragma init_seg to
// control static construction).
//

#pragma warning( push )
#pragma warning( disable : 4074 )
#pragma init_seg(compiler)
#pragma warning( pop )

/// Global error counter.
static LONG g_ErrorCount = 0;

/// Global callback for redirecting trace output and reporting fatal errors.
static DEBUG_TOOLS_OUTPUT_CALLBACK g_pfnOutputCallback = DefaultOutputCallbackImpl;

/// Global callback for notifying clients when a possible crash is detected.
static DEBUG_TOOLS_CRASH_CALLBACK g_pfnCrashCallback = DefaultCraschCallbackImpl;

/// Are we executing via the test runner?
static bool g_bIsTesting = false;

/// Has the user "activated" the debugging tools?
static bool g_bIsActive = false;

/// Global synchronization object.
static LockCS g_cs;

/// Crash report storage path.
static std::wstring g_minidumpSavePath;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Default callback implementation (overridable via DebugTools::Install()).
///////////////////////////////////////////////////////////////////////////////////////////////////

void DefaultOutputCallbackImpl(DWORD dwType, const wchar_t* pwszMessage)
{
	AutoLockCS lock(&g_cs);

	SYSTEMTIME st;

	::GetLocalTime(&st);

	switch (dwType)
	{
		case DEBUG_TOOLS_CALLBACK_TRACE_DEBUG:
			fwprintf_s(stderr, _T("DBG [%04d] %d/%02d/%02d %02d:%02d:%02d: %s\n"),
			           GetCurrentThreadId(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, pwszMessage);
			break;
		case DEBUG_TOOLS_CALLBACK_TRACE_WARNING:
			fwprintf_s(stderr, _T("WRN [%04d] %d/%02d/%02d %02d:%02d:%02d: %s\n"),
			           GetCurrentThreadId(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, pwszMessage);
			break;
		case DEBUG_TOOLS_CALLBACK_TRACE_ERROR:
			fwprintf_s(stderr, _T("ERR [%04d] %d/%02d/%02d %02d:%02d:%02d: %s\n"),
			           GetCurrentThreadId(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, pwszMessage);
			break;
		default:
			break;
	}

	::OutputDebugString(pwszMessage);
	::OutputDebugString(L"\r\n");
}

void DefaultCraschCallbackImpl(const wchar_t* pwszErrorMessage)
{
	//
	// Don't report the error message while running automated tests...
	//

	if (!g_bIsTesting)
	{
		g_pfnOutputCallback(DEBUG_TOOLS_CALLBACK_TRACE_ERROR, pwszErrorMessage);
	}
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Generic utilities.
///////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Make sure that file path always ends with a terminating backward '\' slash.
 */
static void EnsureTerminatingSlash(std::wstring& filepath)
{
	if (filepath.length() > 0)
	{
		std::wstring::size_type pos = filepath.length() - 1;
		if (filepath[pos] != L'\\' && filepath[pos] != L'/')
			filepath += L'\\';
	}
}

/**
 * Retrieve the corresponding error message for a Win32 error code using a neutral
 * system locale via FormatMessage. The CRLF automatically appended by FormatMessage
 * is removed from the return value.
 *
 * @param[in] dwErrCode - Win32 error code
 * @return string containing system error message
 */
static std::wstring FormatWin32ErrorCode(DWORD dwErrCode)
{
	AutoLocalFree<LPWSTR> pwszErrorMsg;

	DWORD systemLocale = MAKELANGID(LANG_NEUTRAL, SUBLANG_NEUTRAL);

	DWORD dwCount = ::FormatMessage(
	                    FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
	                    NULL, dwErrCode, systemLocale, (LPWSTR) & pwszErrorMsg, 0, NULL);

	if (dwCount == 0)
		return L"Unknown Error";

	std::wstring result = pwszErrorMsg;

	// Remove CRLF...
	if (result.length() > 2)
		result.erase(result.length() - 2);

	return result;
}

/**
 * Set the working directory to the path of the current module.
 *
 * @return true/false to signal success
 */
static bool SetCurrentDirectoryToExePath()
{
	static WCHAR wszCurrPath[_MAX_PATH];

	BOOL bSuccess = FALSE;

	DWORD dwPathLen = ::GetModuleFileName(NULL, wszCurrPath, _countof(wszCurrPath));
	if (dwPathLen > 0)
	{
		for (DWORD i = dwPathLen - 1; i >= 0; --i)
		{
			if (wszCurrPath[i] == L'\\' || wszCurrPath[i] == L'/')
			{
				wszCurrPath[i+1] = L'\0';
				bSuccess = ::SetCurrentDirectory(wszCurrPath);
				break;
			}
		}
	}

	return (bSuccess == TRUE);
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Thread-aware singleton (static initialization is thread-safe)
///////////////////////////////////////////////////////////////////////////////////////////////////

template< typename T >
struct ThreadSafeSingleton
{
	/**
	 * Retrieve the state of the singleton object, signals if the object is safe
	 * to use or if a thread is currently constructing/initializing the singleton
	 * in a first call to GetInstance. For most users this should never be of a
	 * concern unless there is a chance of a recursive call into GetInstance,
	 * for example if operator new is overloaded.
	 *
	 * @return true/false if singleton is currently being constructed
	 */
	static bool IsConstructing()
	{
		return (s_isConstructing == 1);
	}


	/**
	 * Retrieve singleton object (first thread to call this method will also construct
	 * and initialize the object in a thread-safe manner).
	 *
	 * @return pointer to the singleton object
	 */
	static T* GetInstance()
	{
		if (s_pInstance != NULL)
			return s_pInstance;

		AcquireLock();

		try
		{
			if (s_pInstance == NULL)
			{
				::InterlockedExchange(&s_isConstructing, 1);

				//
				// Make sure that object is fully constructed and protect the
				// entire construction phase using the full memory barrier via
				// the InterlockedXXX function family. The double lock checking
				// pattern is not safe enough as the compiler if free to optimize
				// and re-order the instruction where we set the "singleton"
				// instance pointer.
				//

				// Perform in-place construction on a piece of memory which is
				// guaranteed not to be tracked by the memory leak tracker.
				T* instance = new(::HeapAlloc(::GetProcessHeap(), 0, sizeof(T))) T;

				InterlockedExchangePointer((void**)&s_pInstance, (void**)instance);

				::InterlockedExchange(&s_isConstructing, 0);
			}
		}
		catch (...)
		{
			::TerminateProcess(::GetCurrentProcess(), EXIT_FAILURE);
		}

		ReleaseLock();

		return s_pInstance;
	}

private:

	//
	// Simple and effective spin lock variation used to synchronize
	// construction and initialization of the singleton object.
	//

	static void AcquireLock()
	{
		while (::InterlockedExchange(&s_lock, 1) == 1)
		{
			while (s_lock != 0)
				::Sleep(0);
		}
	}

	static void ReleaseLock()
	{
		s_lock = 0;
	}

	static T*    s_pInstance;
	static LONG  s_lock;
	static LONG  s_isConstructing;
};

template< typename T >
T* ThreadSafeSingleton<T>::s_pInstance = NULL;

template< typename T >
LONG ThreadSafeSingleton<T>::s_lock = 0;

template< typename T >
LONG ThreadSafeSingleton<T>::s_isConstructing = 0;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Manage debug console and redirect all output to it.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// Re-open the standard file handles and redirect them to the standard console
// handles attached to newly allocated console. By forcing the iostream library
// to sync with stdio, cout/cerr will automatically output to console as well.
//

void RedirectSTDIN()
{
	HANDLE h = ::GetStdHandle(STD_INPUT_HANDLE);

	FILE* fp = _fdopen(_open_osfhandle(reinterpret_cast<intptr_t>(h), _O_TEXT), "r");

	*stdin = *fp;

	setvbuf(stdin, NULL, _IONBF, 0);
}

void RedirectSTDOUT()
{
	HANDLE h = ::GetStdHandle(STD_OUTPUT_HANDLE);

	FILE* fp = _fdopen(_open_osfhandle(reinterpret_cast<intptr_t>(h), _O_TEXT), "w");

	*stdout = *fp;

	setvbuf(stdout, NULL, _IONBF, 0);
}

void RedirectSTDERR()
{
	HANDLE h = ::GetStdHandle(STD_ERROR_HANDLE);

	FILE* fp = _fdopen(_open_osfhandle(reinterpret_cast<intptr_t>(h), _O_TEXT), "w");

	*stderr = *fp;

	setvbuf(stderr, NULL, _IONBF, 0);
}

void RedirectIOSTREAM()
{
	std::ios::sync_with_stdio();
}

BOOL WINAPI ConsoleHandlerCallback(DWORD dwCtrlType)
{
	switch (dwCtrlType)
	{
		case CTRL_C_EVENT:
			TRACE(L"Got Ctrl+C event...");
			break;
		case CTRL_BREAK_EVENT:
			TRACE(L"Got Ctrl+Break event...");
			break;
		case CTRL_CLOSE_EVENT:
			TRACE(L"Console manually closed...");
			break;
		case CTRL_LOGOFF_EVENT:
			TRACE(L"Got logoff event...");
			break;
		case CTRL_SHUTDOWN_EVENT:
			TRACE(L"Got shutdown event...");
			break;
		default:
			break;
	}

	return FALSE;
}

/**
 * Allocate a console for the current process (displaying a console if we
 * aren't running as a console process) and redirect the stdio and iostream
 * libraries to read from and write to the console.
 */
void InitDebugConsole()
{
	::AllocConsole();
	::SetConsoleTitle(L"Debug Console");
	::SetConsoleCtrlHandler(ConsoleHandlerCallback, TRUE);

	CONSOLE_SCREEN_BUFFER_INFO layout;

	::GetConsoleScreenBufferInfo(::GetStdHandle(STD_OUTPUT_HANDLE), &layout);

	const int CONSOLE_LINE_WIDTH = 120;
	const int CONSOLE_HISTORY_NUM_LINES = 5000;

	layout.dwSize.X = CONSOLE_LINE_WIDTH;
	layout.dwSize.Y = CONSOLE_HISTORY_NUM_LINES;

	::SetConsoleScreenBufferSize(::GetStdHandle(STD_OUTPUT_HANDLE), layout.dwSize);

	RedirectSTDIN();
	RedirectSTDOUT();
	RedirectSTDERR();
	RedirectIOSTREAM();
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// SEH exception descriptions
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// Search for the EXCEPTION_POINTERS structure in MSDN for information about the
// extra description fields available for EXCEPTION_ACCESS_VIOLATION etc...
//

namespace SEH
{
/**
 * Retrieve a textual description of a SEH exception.
 *
 * @param[in] pExceptionContext - SEH exception pointers
 * @return description of the exception (non-mutable string)
 */
const wchar_t* GetDescription(_EXCEPTION_POINTERS * pExceptionContext)
{
	switch (pExceptionContext->ExceptionRecord->ExceptionCode)
	{
		case EXCEPTION_ACCESS_VIOLATION:
			switch ((DWORD)(pExceptionContext->ExceptionRecord->ExceptionInformation[0]))
			{
				case 0:
					return L"EXCEPTION_ACCESS_VIOLATION [READ]";
				case 1:
					return L"EXCEPTION_ACCESS_VIOLATION [WRITE]";
				case 8:
					return L"EXCEPTION_ACCESS_VIOLATION [DEP]";
				default:
					return L"EXCEPTION_ACCESS_VIOLATION";
			}
		case EXCEPTION_DATATYPE_MISALIGNMENT:
			return L"EXCEPTION_DATATYPE_MISALIGNMENT";
		case EXCEPTION_BREAKPOINT:
			return L"EXCEPTION_BREAKPOINT";
		case EXCEPTION_SINGLE_STEP:
			return L"EXCEPTION_SINGLE_STEP";
		case EXCEPTION_ARRAY_BOUNDS_EXCEEDED:
			return L"EXCEPTION_ARRAY_BOUNDS_EXCEEDED";
		case EXCEPTION_FLT_DENORMAL_OPERAND:
			return L"EXCEPTION_FLT_DENORMAL_OPERAND";
		case EXCEPTION_FLT_DIVIDE_BY_ZERO:
			return L"EXCEPTION_FLT_DIVIDE_BY_ZERO";
		case EXCEPTION_FLT_INEXACT_RESULT:
			return L"EXCEPTION_FLT_INEXACT_RESULT";
		case EXCEPTION_FLT_INVALID_OPERATION:
			return L"EXCEPTION_FLT_INVALID_OPERATION";
		case EXCEPTION_FLT_OVERFLOW:
			return L"EXCEPTION_FLT_OVERFLOW";
		case EXCEPTION_FLT_STACK_CHECK:
			return L"EXCEPTION_FLT_STACK_CHECK";
		case EXCEPTION_FLT_UNDERFLOW:
			return L"EXCEPTION_FLT_UNDERFLOW";
		case EXCEPTION_INT_DIVIDE_BY_ZERO:
			return L"EXCEPTION_INT_DIVIDE_BY_ZERO";
		case EXCEPTION_INT_OVERFLOW:
			return L"EXCEPTION_INT_OVERFLOW";
		case EXCEPTION_PRIV_INSTRUCTION:
			return L"EXCEPTION_PRIV_INSTRUCTION";
		case EXCEPTION_IN_PAGE_ERROR:
			switch ((DWORD)(pExceptionContext->ExceptionRecord->ExceptionInformation[0]))
			{
				case 0:
					return L"EXCEPTION_IN_PAGE_ERROR [READ]";
				case 1:
					return L"EXCEPTION_IN_PAGE_ERROR [WRITE]";
				case 8:
					return L"EXCEPTION_IN_PAGE_ERROR [DEP]";
				default:
					return L"EXCEPTION_IN_PAGE_ERROR";
			}
		case EXCEPTION_ILLEGAL_INSTRUCTION:
			return L"EXCEPTION_ILLEGAL_INSTRUCTION";
		case EXCEPTION_NONCONTINUABLE_EXCEPTION:
			return L"EXCEPTION_NONCONTINUABLE_EXCEPTION";
		case EXCEPTION_STACK_OVERFLOW:
			return L"EXCEPTION_STACK_OVERFLOW";
		case EXCEPTION_INVALID_DISPOSITION:
			return L"EXCEPTION_INVALID_DISPOSITION";
		case EXCEPTION_GUARD_PAGE:
			return L"EXCEPTION_GUARD_PAGE";
		case EXCEPTION_INVALID_HANDLE:
			return L"EXCEPTION_INVALID_HANDLE";
		default:
			return L"Unknown SEH exception";
	}
}
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Symbol translation and mini dumping via Windows Debugging Tools (debughlp.dll + PDB:s)
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// These declaration were imported from the dbghelp.h part of the "Windows Debugging
// Tools for Windows SDK" (6.8.0004.0 070515-1751). Please note that the dbghelp.dll
// which is distributed as part of the Windows XP (SP2/SP3) will not support these
// methods, either manually replace the DLL or distribute a newer dbghelp.dll in the
// same directory as the executable.
//

typedef BOOL (WINAPI *pfnSymInitializeW_t)(
    __in HANDLE hProcess,
    __in_opt PCWSTR UserSearchPath,
    __in BOOL fInvadeProcess);

typedef DWORD (WINAPI *pfnSymSetOptions_t)(
    __in DWORD SymOptions);

typedef BOOL (WINAPI *pfnSymFromAddrW_t)(
    __in HANDLE hProcess,
    __in DWORD64 Address,
    __out_opt PDWORD64 Displacement,
    __inout PSYMBOL_INFOW Symbol);

typedef BOOL (WINAPI *pfnSymGetLineFromAddrW64_t)(
    __in HANDLE hProcess,
    __in DWORD64 dwAddr,
    __out PDWORD pdwDisplacement,
    __out PIMAGEHLP_LINEW64 Line);

typedef BOOL(WINAPI *pfnStackWalk64_t)(
    __in DWORD MachineType,
    __in HANDLE hProcess,
    __in HANDLE hThread,
    __inout LPSTACKFRAME64 StackFrame,
    __inout PVOID ContextRecord,
    __in_opt PREAD_PROCESS_MEMORY_ROUTINE64 ReadMemoryRoutine,
    __in_opt PFUNCTION_TABLE_ACCESS_ROUTINE64 FunctionTableAccessRoutine,
    __in_opt PGET_MODULE_BASE_ROUTINE64 GetModuleBaseRoutine,
    __in_opt PTRANSLATE_ADDRESS_ROUTINE64 TranslateAddress);

typedef PVOID(WINAPI *pfnSymFunctionTableAccess64_t)(
    __in HANDLE hProcess,
    __in DWORD64 AddrBase);

typedef DWORD64(WINAPI *pfnSymGetModuleBase64_t)(
    __in HANDLE hProcess,
    __in DWORD64 qwAddr);

typedef BOOL (WINAPI *pfnMiniDumpWriteDump_t)(
    IN HANDLE hProcess,
    IN DWORD ProcessId,
    IN HANDLE hFile,
    IN MINIDUMP_TYPE DumpType,
    IN CONST PMINIDUMP_EXCEPTION_INFORMATION ExceptionParam, OPTIONAL
    IN CONST PMINIDUMP_USER_STREAM_INFORMATION UserStreamParam, OPTIONAL
    IN CONST PMINIDUMP_CALLBACK_INFORMATION CallbackParam OPTIONAL);

enum
{
	MAX_STACKTRACE_DEPTH = 32
};

struct StackTrace
{
	StackTrace() : count(0) {}
	int count;
	ULONGLONG addrs[MAX_STACKTRACE_DEPTH];
};

/**
 * Singleton class wrapping functionality in dbghelp.dll (Windows Debugging Tools),
 * mainly used to retrieve information from PDB:s and for writing minidumps.
*/
struct DebugHelpDLL : public ThreadSafeSingleton<DebugHelpDLL>
{
	DebugHelpDLL()
			: m_bIsOK(FALSE)
			, m_hDLL(NULL)
			, m_pfnSymInitializeW(NULL)
			, m_pfnSymSetOptions(NULL)
			, m_pfnSymFromAddrW(NULL)
			, m_pfnSymGetLineFromAddrW64(NULL)
			, m_pfnStackWalk64(NULL)
			, m_pfnSymFunctionTableAccess64(NULL)
			, m_pfnSymGetModuleBase64(NULL)
			, m_pfnMiniDumpWriteDump(NULL)
	{
		m_bIsOK = LoadDLL();
	}

	~DebugHelpDLL()
	{
		if (m_hDLL)
		{
			::FreeLibrary(m_hDLL);
		}
	}

	/**
	 * Retrieve useful debug information for a symbol using its address.
	 *
	 * @param[in dwAddr - address of the object
	 * @param[out] symbolName - name of the symbol
	 * @param[out] symbolFile - file containing the symbol
	 * @param[out] symbolLine - symbol line offset
	 * @return true/false if address could successfully be translated to a symbol
	 */
	bool GetSymbolForAddress(DWORD64 dwAddr, std::wstring& symbolName, std::wstring& symbolFile, DWORD& symbolLine)
	{
		if (!IsOk())
		{
			return FALSE;
		}

		AutoLockCS lock(&m_cs);

		// The symbol name field is the last member of SYMBOL_INFOW so we can
		// safely allocate the entire struct + space for the name on the stack.
		ULONG64 tempBuffer[
		    (sizeof(SYMBOL_INFOW) + MAX_SYM_NAME * sizeof(WCHAR) + sizeof(ULONG64) - 1)
		    / sizeof(ULONG64)];

		PSYMBOL_INFOW pSymbol = (PSYMBOL_INFOW)(tempBuffer);
		pSymbol->SizeOfStruct = sizeof(SYMBOL_INFOW);
		pSymbol->MaxNameLen = MAX_SYM_NAME;

		DWORD64 dwDisplacement64 = 0;
		if (!m_pfnSymFromAddrW(::GetCurrentProcess(), dwAddr, &dwDisplacement64, pSymbol))
			return FALSE;

		IMAGEHLP_LINEW64 lineInfo;
		lineInfo.SizeOfStruct = sizeof(IMAGEHLP_LINEW64);

		DWORD dwDisplacement = 0;
		if (!m_pfnSymGetLineFromAddrW64(::GetCurrentProcess(), dwAddr, &dwDisplacement, &lineInfo))
			return FALSE;

		symbolName = pSymbol->Name;
		symbolFile = lineInfo.FileName;
		symbolLine = lineInfo.LineNumber;

		return TRUE;
	}

	/**
	 * Attempt to generate a minidump file for a SEH exception.The minidump will be
	 * written to C:\Windows\Temp\ and will use the naming schema minidumpXXX.dmp
	 * where XXX is automatically incremented as appropriate.
	 *
	 * @param[in] pExceptionContext - SEH exception pointers
	 * @return true/false to signal if we could successfully write a minidump
	 */
	bool WriteMiniDump(_EXCEPTION_POINTERS * pExceptionContext)
	{
		if (!IsOk())
		{
			return FALSE;
		}

		AutoLockCS lock(&m_cs);

		std::wstring filepath;

		if (!GenerateMiniDumpFileName(filepath))
		{
			TRACE_WARN(L"Could not generate temporary filename for minidump");
			return FALSE;
		}

		AutoCloseFile hFile = ::CreateFile(filepath.c_str(), GENERIC_WRITE,
		                                   FILE_SHARE_WRITE, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);

		if (!hFile.IsValid())
		{
			TRACE_WARN(L"Could not create minidump file : %s", filepath);
			return FALSE;
		}

		MINIDUMP_EXCEPTION_INFORMATION exinfo;
		exinfo.ThreadId = ::GetCurrentThreadId();
		exinfo.ExceptionPointers = pExceptionContext;
		exinfo.ClientPointers = FALSE;

		DWORD dwFlags = 0;

		// General information about the system/threads/exceptions (default).
		dwFlags |= MiniDumpNormal;

#ifndef NDEBUG
		// Include contents of every readable and writable memory page (stack/heap/TLS/TEB).
		dwFlags |= MiniDumpWithPrivateReadWriteMemory ;

		// Include all writable data sections of all loaded modules (global variables).
		dwFlags |= MiniDumpWithDataSegs;

		// Include process handle table.
		dwFlags |= MiniDumpWithHandleData;

		// Include additional information about threads (addresses, creation time).
		dwFlags |= MiniDumpWithThreadInfo;
#endif

		if (!m_pfnMiniDumpWriteDump(GetCurrentProcess(), GetCurrentProcessId(), hFile, (MINIDUMP_TYPE)(dwFlags), &exinfo, NULL, NULL))
		{
			TRACE_WIN32_ERROR(MiniDumpWriteDump);
			return FALSE;
		}

		TRACE(L"Wrote minidump file to %s", filepath);

		return TRUE;
	}

// Disable global optimization and ignore /GS waning caused by inline assembly.
#ifdef PLATFORM_X86
#pragma optimize( "g", off )
#pragma warning( push )
#pragma warning( disable : 4740 )
#pragma warning( disable : 4748 )
#endif

	/**
	 * Attempt to retrieve the call stack, excluding the call to this
	 * function from the stack trace.
	 *
	 * @param[in,out] trace - filled with stack addresses
	 */
	void GetStackTrace(StackTrace& trace)
	{
		if (!IsOk())
		{
			return;
		}

		AutoLockCS lock(&m_cs);

		//
		// Since GetThreadContext() can't be used on a running thread we need
		// to manually extract a thread context (stack addr, frame ptr)
		//

		CONTEXT context;

#ifdef PLATFORM_X86
		ZeroMemory(&context, sizeof(CONTEXT));
		context.ContextFlags = CONTEXT_CONTROL;
		__asm
		{
GetNextAddr:
			mov [context.Ebp], ebp;
			mov [context.Esp], esp;
			mov eax, [GetNextAddr];
			mov [context.Eip], eax;
		}
#else
		RtlCaptureContext(&context);
#endif

		STACKFRAME64 stackframe;
		ZeroMemory(&stackframe, sizeof(STACKFRAME64));

#ifdef PLATFORM_X86
		DWORD machinetype           = IMAGE_FILE_MACHINE_I386;
		stackframe.AddrPC.Offset    = context.Eip;
		stackframe.AddrPC.Mode      = AddrModeFlat;
		stackframe.AddrFrame.Offset = context.Ebp;
		stackframe.AddrFrame.Mode   = AddrModeFlat;
		stackframe.AddrStack.Offset = context.Esp;
		stackframe.AddrStack.Mode   = AddrModeFlat;
#elif defined(PLATFORM_X64)
		DWORD machinetype           = IMAGE_FILE_MACHINE_AMD64;
		stackframe.AddrPC.Offset    = context.Rip;
		stackframe.AddrPC.Mode      = AddrModeFlat;
		stackframe.AddrFrame.Offset = context.Rsp;
		stackframe.AddrFrame.Mode   = AddrModeFlat;
		stackframe.AddrStack.Offset = context.Rsp;
		stackframe.AddrStack.Mode   = AddrModeFlat;
#endif
		trace.count = 0;

		while (trace.count < MAX_STACKTRACE_DEPTH)
		{
			BOOL bSuccess = m_pfnStackWalk64(
			                    machinetype,
			                    GetCurrentProcess(),
			                    GetCurrentThread(),
			                    &stackframe,
			                    &context,
			                    NULL,
			                    m_pfnSymFunctionTableAccess64,
			                    m_pfnSymGetModuleBase64,
			                    NULL);

			if (bSuccess && stackframe.AddrPC.Offset != 0)
			{
				trace.addrs[trace.count++] = stackframe.AddrPC.Offset;
			}
			else
			{
				break;
			}
		}
	}

// Re-enable global optimization and warning which were temporarily disabled.
#ifdef PLATFORM_X86
#pragma warning( pop )
#pragma optimize( "g", on )
#endif

	/**
	 * Helper method which dumps the stack trace as debug output.
	 *
	 * @param[in] pwszMessage - diagnostic description of stack trace
	 * @param[in] trace - call stack to print
	 */
	void DumpStackTrace(const wchar_t* pwszMessage, const StackTrace& trace)
	{
		int depth = 0;

		if (trace.count > 0)
		{
			TRACE(L"Dumping call stack (%s):", pwszMessage);
		}

		for (int i = 0; i < trace.count; i++)
		{
			DWORD line;
			std::wstring funcname, filename;

			if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)trace.addrs[i], funcname, filename, line))
			{
				if (funcname == L"DebugHelpDLL::GetStackTrace")
					continue;
				if (funcname == L"DebugHelpDLL::DumpStackTrace")
					continue;
				if (funcname == L"DebugTools::AssertionFailed")
					continue;
				if (funcname == L"DebugTools::FatalError")
					continue;

				TRACE(L"[%02d] '%s' in (%s:%d)", depth, funcname, filename, line);
			}
			else
			{
				TRACE(L"[%02d] stack address [%x]", depth, trace.addrs[i]);
			}

			depth++;
		}
	}

	/**
	 * Helper method which retrieves and dumps the call stack as debug output.
	 *
	 * @param[in] pwszMessage - diagnostic description of stack trace
	 */
	void DumpStackTrace(const wchar_t* pwszMessage)
	{
		StackTrace trace;
		GetStackTrace(trace);
		DumpStackTrace(pwszMessage, trace);
	}

private:
	bool IsOk() const
	{
		return m_bIsOK;
	}

	bool GenerateMiniDumpFileName(std::wstring& filepath)
	{
		wchar_t wszTempBuf[256];
		wchar_t wszModuleName[256];

		if (!::GetModuleBaseName(::GetCurrentProcess(), NULL, wszModuleName, _countof(wszModuleName)))
		{
			return false;
		}

		for (size_t i = wcslen(wszModuleName); i > 0; i--)
		{
			if (wszModuleName[i] == L'.')
			{
				wszModuleName[i] = L'\0';
				break;
			}
		}

		for (int i = 1; i < 999; i++)
		{
			time_t timestamp;
			time(&timestamp);
			struct tm currtime;
			localtime_s(&currtime, &timestamp);

			_snwprintf_s(wszTempBuf, _countof(wszTempBuf), L"%s%s_%d_%02d_%02d_%02d_%02d_%02d.dmp",
			             g_minidumpSavePath.c_str(), wszModuleName,
			             1900 + currtime.tm_year, currtime.tm_mon + 1, currtime.tm_mday,
			             currtime.tm_hour, currtime.tm_min, currtime.tm_sec);

			if (::GetFileAttributes(wszTempBuf) == INVALID_FILE_ATTRIBUTES)
			{
				filepath = wszTempBuf;
				return TRUE;
			}
		}

		return TRUE;
	}

	template <typename T>
	bool ImportFromDLL(const char* pszProcName, T* pFun)
	{
		*pFun = (T)::GetProcAddress(m_hDLL, pszProcName);
		return (*pFun != NULL);
	}

	bool LoadDLL()
	{
		m_hDLL = ::LoadLibrary(L"dbghelp.dll");

		if (m_hDLL == NULL)
		{
			TRACE_WARN(L"Could not locate dbghelp.dll");
			return FALSE;
		}

		bool bSuccess = ImportFromDLL("SymInitializeW", &m_pfnSymInitializeW)
		                && ImportFromDLL("SymSetOptions", &m_pfnSymSetOptions)
		                && ImportFromDLL("SymFromAddrW", &m_pfnSymFromAddrW)
		                && ImportFromDLL("SymGetLineFromAddrW64", &m_pfnSymGetLineFromAddrW64)
		                && ImportFromDLL("StackWalk64", &m_pfnStackWalk64)
		                && ImportFromDLL("SymFunctionTableAccess64", &m_pfnSymFunctionTableAccess64)
		                && ImportFromDLL("SymGetModuleBase64", &m_pfnSymGetModuleBase64)
		                && ImportFromDLL("MiniDumpWriteDump", &m_pfnMiniDumpWriteDump)
		                ;

		if (!bSuccess)
		{
			TRACE_WARN(L"Could not import symbols from dbghelp.dll");
			return FALSE;
		}

		// Load line information, always use undecorated symbol names and lazy load PDB:s
		m_pfnSymSetOptions(SYMOPT_LOAD_LINES | SYMOPT_UNDNAME | SYMOPT_DEFERRED_LOADS);

		if (!m_pfnSymInitializeW(::GetCurrentProcess(), NULL, TRUE))
		{
			TRACE_WIN32_ERROR(SymInitializeW);
			return FALSE;
		}

		return TRUE;
	}

	HMODULE                         m_hDLL;
	bool                            m_bIsOK;
	pfnSymInitializeW_t             m_pfnSymInitializeW;
	pfnSymSetOptions_t              m_pfnSymSetOptions;
	pfnSymFromAddrW_t               m_pfnSymFromAddrW;
	pfnSymGetLineFromAddrW64_t      m_pfnSymGetLineFromAddrW64;
	pfnStackWalk64_t                m_pfnStackWalk64;
	pfnSymFunctionTableAccess64_t   m_pfnSymFunctionTableAccess64;
	pfnSymGetModuleBase64_t         m_pfnSymGetModuleBase64;
	pfnMiniDumpWriteDump_t          m_pfnMiniDumpWriteDump;
	LockCS                          m_cs;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// Memory debugging support (track memory leaks and double free attempts)
///////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Simple debugging utility tool for tracking memory allocations to detect
 * memory leaks and double free attempts. As this library is intended to be
 * statically linked in each module will have it's own copy of the memory
 * tracker which will enforce that resources should be allocated and released
 * in the same module.
 */
struct MemoryTracker : public ThreadSafeSingleton<MemoryTracker>
{
	MemoryTracker()
	{
		m_bTrackingEnabled = true;
	}

	~MemoryTracker()
	{
		m_bTrackingEnabled = false;
	}

	/**
	 * Save a checkpoint of currently tracked allocations in order to exclude
	 * them from being treated a memory leaks if they aren't deallocated before
	 * the call to DumpLeaks(). The idea is that once the CRT and the application
	 * has finished initializing (globals, singletons, etc) we'll take a snapshot
	 * and use it as the base for tracking memory leaks.
	 */
	void SetMemoryCheckPoint()
	{
		AutoLockCS lock(&m_cs);

		// Temporarily disable tracking to exclude internal allocations by the tracker.
		m_bTrackingEnabled = false;

		m_checkpoint = m_allocations;

		m_bTrackingEnabled = true;
	}

	/**
	 * Traverse the allocation list and dump detailed information about possible
	 * memory leaks via the trace output facility.
	 *
	 * @return true/false if any leaks were found
	 */
	bool DumpLeaks()
	{
		AutoLockCS lock(&m_cs);

		if (m_allocations.size() ==  0)
			return FALSE;

		int numleaks = 0;

		for (AllocInfoMap::const_iterator it = m_allocations.begin(); it != m_allocations.end(); ++it)
		{
			if (m_checkpoint.find((*it).first) != m_checkpoint.end())
				continue;

			const AllocationInfo& info = (*it).second;

			TraceLeak((*it).first, info);

			numleaks++;
		}

		bool bHaveLeaks = (numleaks > 0);

		if (bHaveLeaks)
			TRACE_ERROR(L"%d memory leak(s) detected", numleaks);

		return bHaveLeaks;
	}

	/**
	 * Record an allocation operation, will trigger a fatal error if
	 * passed a NULL pointer allocation.
	 *
	 * @param[in] ptr - base pointer of the allocation
	 * @param[in] numbytes - size of the allocation
	 * @param[in] bIsArray - true/false to signal allocator type (new/new[])
	 * @param[in] pCalleeAddress - stack address of callee function/statement
	 * @param[in] trace - stack trace up to callee
	 */
	void TrackAlloc(void* ptr, size_t numbytes, bool bIsArray, const void* pCalleeAddress, const StackTrace& trace)
	{
		AutoLockCS lock(&m_cs);

		if (!m_bTrackingEnabled)
		{
			return;
		}

		// Temporarily disable tracking to exclude internal allocations by the tracker.
		m_bTrackingEnabled = false;

		if (ptr != NULL)
		{
			m_allocations.insert(std::make_pair(ptr, AllocationInfo(numbytes, bIsArray, pCalleeAddress, trace)));
		}
		else
		{
			TRACE_ERROR(L"Can't track NULL pointer memory allocation");

			DebugTools::FatalError(L"Memory Allocation Error");
		}

		m_bTrackingEnabled = true;
	}

	/**
	 * Record a deallocation operation (will signal a fatal error if passed a
	 * if passed a pointer which isn't tracked, most likely a double free attempt). 
     * We'll also make sure that memory is released using the correct matching 
     * operator, i.e if the memory is allocated with operator new[] it should be 
     * deallocated using operator delete[].
	 *
	 * @param[in] ptr - base pointer of the allocation
	 * @param[in] bIsArrayDelete - is deallocator operator delete[]?
	 * @param[in] pCalleeAddress - stack address of callee function/statement
	 */
	void TrackFree(void* ptr, bool bIsArrayDelete, const void* pCalleeAddress)
	{
		AutoLockCS lock(&m_cs);

		if (!m_bTrackingEnabled)
		{
			return;
		}

        //
        // Don't bother with NULL pointers.
        //

        if (!ptr)
        {
            return;
        }

		// Temporarily disable tracking to exclude internal allocations by the tracker.
		m_bTrackingEnabled = false;

		AllocInfoMap::const_iterator it = m_allocations.find(ptr);
		if (it == m_allocations.end())
		{
			DWORD line;
			std::wstring funcname, filename;

			const wchar_t* reason = (ptr == NULL) ? L"NULL pointer" : L"double free?";

			if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)pCalleeAddress, funcname, filename, line))
			{
				TRACE_ERROR(L"Invalid memory deallocation [%x], pointer not tracked (%s) in '%s' (%s:%d)",
				            ptr, reason, funcname, filename, line);
			}
			else
			{
				TRACE_ERROR(L"Invalid memory deallocation [%x], pointer not tracked (%s) at address [%x]",
				            ptr, reason, pCalleeAddress);
			}

			DebugTools::FatalError(L"Memory Deallocation Error");
		}
		else
		{
			const AllocationInfo& info = (*it).second;

			// Make sure that delete/delete[] matches original new/new[] call.
			if (bIsArrayDelete != info.bIsArray)
			{
				DWORD line;
				std::wstring funcname, filename;

				const wchar_t* newtype = info.bIsArray  ? L"new[]"    : L"new";
				const wchar_t* deltype = bIsArrayDelete ? L"delete[]" : L"delete";

				if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)pCalleeAddress, funcname, filename, line))
				{
					TRACE_ERROR(L"Invalid memory deallocation [%x], operator mismatch (%s vs %s) in '%s' (%s:%d)",
					            ptr, newtype, deltype, funcname, filename, line);
				}
				else
				{
					TRACE_ERROR(L"Invalid memory deallocation [%x], operator mismatch (%s vs %s) at address [%x]",
					            ptr, newtype, deltype, pCalleeAddress);
				}

				if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)info.pAllocatedByAddr, funcname, filename, line))
				{
					TRACE_ERROR(L"[%x] was allocated by '%s' in %s:%d", ptr, funcname, filename, line);
				}
				else
				{
					TRACE_ERROR(L"[%x] was allocated at address [%x]", ptr, info.pAllocatedByAddr);
				}

				DebugHelpDLL::GetInstance()->DumpStackTrace(L"original allocation", info.trace);

				DebugTools::FatalError(L"Memory Deallocation Error");
			}
			else
			{
				m_allocations.erase(it);
			}
		}

		m_bTrackingEnabled = true;
	}

	/**
	 * Try to locate information about who allocated a particular pointer.
	 *
	 * @param[in] ptr - base pointer of the allocation
	 * @return address of original callee or NULL if no match was found.
	 */
	const void* FindOriginalCallee(void* ptr)
	{
		AutoLockCS lock(&m_cs);

		AllocInfoMap::const_iterator it = m_allocations.find(ptr);

		if (it == m_allocations.end())
		{
			return NULL;
		}

		const AllocationInfo& info = (*it).second;

		return info.pAllocatedByAddr;
	}

	/**
	 * Try to retrieve the call stack of an allocation we're tracking.
	 *
	 * @param[in] ptr - base pointer of the allocation
	 * @param[out] trace - filled with call stack addresses on success
	 * @return true/false to signal success
	 */
	bool GetCallStackFor(void* ptr, StackTrace& trace)
	{
		AutoLockCS lock(&m_cs);

		AllocInfoMap::const_iterator it = m_allocations.find(ptr);

		if (it == m_allocations.end())
		{
			return false;
		}

		const AllocationInfo& info = (*it).second;

		trace = info.trace;

		return true;
	}

	/**
	 * Validate all allocation and check for possible heap corruptions (buffer
	 * under/overflow, etc). If an error is detected the normal DebugTools error
	 * handling will be triggered and this function will not return.
	 */
	void VerifyHeapIntegrity()
	{
		AutoLockCS lock(&m_cs);

		AllocInfoMap::iterator it;

		for (it = m_allocations.begin(); it != m_allocations.end(); ++it)
		{
			void* ptr = (*it).first;
			AllocationInfo& info = (*it).second;

			VerifyAllocation(ptr, (void*)info.pAllocatedByAddr);
		}

		if (::HeapValidate(::GetProcessHeap(), 0, NULL) == 0)
		{
			DebugTools::FatalError(L"HeapValidate() failed, detected memory corruptions");
		}
	}

	/**
	 * Dump general statistical information about memory usage etc..
	 */
	void DumpStats()
	{
		AutoLockCS lock(&m_cs);

		enum { KB1, KB4, KB16, KB64, KB512, LARGE_ALLOCS, NUM_GROUPS };

		size_t totalBytesAllocated = 0;
		size_t allocGroups[NUM_GROUPS] = {0};

		AllocInfoMap::iterator it;

		for (it = m_allocations.begin(); it != m_allocations.end(); ++it)
		{
			AllocationInfo& info = (*it).second;
			totalBytesAllocated += info.size;

			size_t kB = info.size / 1024;

			if (kB <= 1)
				allocGroups[KB1]++;
			else if (kB <= 4)
				allocGroups[KB4]++;
			else if (kB <= 16)
				allocGroups[KB16]++;
			else if (kB <= 64)
				allocGroups[KB64]++;
			else if (kB <= 512)
				allocGroups[KB512]++;
			else
				allocGroups[LARGE_ALLOCS]++;
		}

		TRACE(L"Memory stats: %u kB tracked (%u allocations)", totalBytesAllocated / 1024, m_allocations.size());
		TRACE(L"Allocation size statistics (less than or equal to):");
		TRACE(L"   1 kB = %d", allocGroups[KB1]);
		TRACE(L"   4 kB = %d", allocGroups[KB4]);
		TRACE(L"  16 kB = %d", allocGroups[KB16]);
		TRACE(L"  64 kB = %d", allocGroups[KB64]);
		TRACE(L" 512 kB = %d", allocGroups[KB512]);
		TRACE(L" larger = %d", allocGroups[LARGE_ALLOCS]);
	}

private:

	struct AllocationInfo
	{
		AllocationInfo(size_t size_, bool bIsArray_ , const void* pAllocatedByAddr_, const StackTrace& trace_)
				: size(size_), bIsArray(bIsArray_), pAllocatedByAddr(pAllocatedByAddr_), trace(trace_)
		{}

		size_t size;
		bool bIsArray;
		const void* pAllocatedByAddr;
		StackTrace trace;
	};

	void TraceLeak(void* ptr, const AllocationInfo& info)
	{
		DWORD line;
		std::wstring funcname, filename;

		if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)info.pAllocatedByAddr, funcname, filename, line))
		{
			TRACE(L"[%x] %d bytes were allocated by '%s' in %s:%d", ptr, info.size, funcname, filename, line);
		}
		else
		{
			TRACE(L"[%x] %d bytes were allocated at address [%x]", ptr, info.size, info.pAllocatedByAddr);
		}

		DebugHelpDLL::GetInstance()->DumpStackTrace(L"original allocation", info.trace);
	}

	/// Map pointer -> allocation information.
	typedef std::map<void*, AllocationInfo> AllocInfoMap;

	bool            m_bTrackingEnabled;
	AllocInfoMap    m_allocations;
	AllocInfoMap    m_checkpoint;
	LockCS          m_cs;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// Override built in new/delete operators to track memory allocations.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// Overload operators new/delete so that we can track allocation/deallocation
// operations using the MemoryTracker class. By linking statically to the operators
// defined below, the linker will automatically override the CRT ones so no manual
// inclusion of headers or macros are required for the tracking to work correctly.
//
// The downside is that each module (executable/DLL) will have it's own copy of the
// tracker and will only track it's own allocations. Errors will be signaled if memory
// is allocated in one module and deallocated in a different one. As these kind of
// situations break encapsulation and the concept of resource responsibility this
// setup was deliberately not replaced with a solution where the entire process would
// share a memory tracker.
//
// In order to detect memory corruption errors we'll use custom wrapper for malloc/free
// which insert "guard" blocks around allocations to detect buffer overruns both before
// and after the allocation. The downside with this approach is that we won't detect
// read attempts before or past the end of a buffer but if needed such protection could
// easily be implemented using VirtualProtect to read/write protect a guard page at the
// end of the allocation.
//

/// Sequence of bytes appended before and after an allocation.
static const unsigned char GUARD_SIGNATURE[] = {0xCC, 0xCC, 0xCC, 0xCC};

void* DebugMalloc(size_t numbytes)
{
	if (numbytes == 0)
	{
		FORCE_BREAK_INTO_DEBUGGER;
	}

	//
	// Layout: [allocation size][guard block][allocation buffer][guard block]
	//

	char* mem = (char*) ::HeapAlloc(::GetProcessHeap(), 0, numbytes + sizeof(size_t) + (2 * sizeof(GUARD_SIGNATURE)));

	if (mem == NULL)
	{
		FORCE_BREAK_INTO_DEBUGGER;
	}

	// Write the size of the allocation
	((size_t*)(mem))[0] = numbytes;

	mem += sizeof(size_t);

	// Write a "guard" signature before the allocation.
	memcpy(mem, GUARD_SIGNATURE, sizeof(GUARD_SIGNATURE));

	mem += sizeof(GUARD_SIGNATURE);

	// Write a "guard" signature after the allocation
	memcpy(mem + numbytes, GUARD_SIGNATURE, sizeof(GUARD_SIGNATURE));

	return mem;
}

void HandleMemoryCorruption(void* ptr, const wchar_t* pwszDescription, void* pCalleeAddress)
{
	DWORD line;
	std::wstring funcname, filename;

	if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)pCalleeAddress, funcname, filename, line))
	{
		TRACE_ERROR(L"Detected memory corruption (%s) [%x] in '%s' (%s:%d)",
		            pwszDescription, ptr, funcname, filename, line);
	}
	else
	{
		TRACE_ERROR(L"Detected memory corruption (%s) [%x] at address [%x]",
		            pwszDescription, ptr, pCalleeAddress);
	}

	//
	// Try to find the location where the ptr was originally allocated.
	//

	const void* pOriginalCalleeAddress =
	    MemoryTracker::GetInstance()->FindOriginalCallee(ptr);

	if (pOriginalCalleeAddress)
	{
		DWORD line;
		std::wstring funcname, filename;

		if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)pOriginalCalleeAddress, funcname, filename, line))
		{
			TRACE(L"[%x] was allocated by '%s' in %s:%d", ptr, funcname, filename, line);
		}
		else
		{
			TRACE(L"[%x] was allocated at address [%x]", ptr, pOriginalCalleeAddress);
		}

		StackTrace trace;

		if (MemoryTracker::GetInstance()->GetCallStackFor(ptr, trace))
		{
			DebugHelpDLL::GetInstance()->DumpStackTrace(L"original allocation", trace);
		}
	}

	DebugTools::FatalError(L"Memory Corruption Detected");
}

void VerifyAllocation(void* ptr, void* pAllocatedByAddr)
{
	//
	// Layout: [allocation size][guard block][allocation buffer][guard block]
	//

	// Move back to the actual beginning of the the allocation.
	char* mem = (char*)(ptr) - (sizeof(size_t) + sizeof(GUARD_SIGNATURE));

	// Check the "guard" block right before the allocation.
	if (memcmp(mem + sizeof(size_t), GUARD_SIGNATURE, sizeof(GUARD_SIGNATURE)) != 0)
	{
		HandleMemoryCorruption(ptr, L"before", pAllocatedByAddr);
	}

	// Retrieve size of the allocation as requested in the call to malloc.
	size_t numbytes = ((size_t*)(mem))[0];

	if (numbytes == 0)
	{
		HandleMemoryCorruption(ptr, L"size=0", pAllocatedByAddr);
	}

	// Check the "guard" block right after the allocation
	if (memcmp(mem + sizeof(size_t) + sizeof(GUARD_SIGNATURE) + numbytes, GUARD_SIGNATURE, sizeof(GUARD_SIGNATURE)) != 0)
	{
		HandleMemoryCorruption(ptr, L"after", pAllocatedByAddr);
	}
}

void DebugFree(void *ptr, void* pCalleeAddress)
{
	//
	// In order to respect the the C++ 98 standard (5.3.5/2) which says "if the
	// value of the operand of delete is the null pointer the operation has no
	// effect" we have to allow NULL pointer deallocations.
	//

	if (NULL == ptr)
	{
		return;
	}

	//
	// Layout: [allocation size][guard block][allocation buffer][guard block]
	//

	// Move back to the actual beginning of the the allocation.
	char* mem = (char*)(ptr) - (sizeof(size_t) + sizeof(GUARD_SIGNATURE));

	// Check the "guard" block right before the allocation.
	if (memcmp(mem + sizeof(size_t), GUARD_SIGNATURE, sizeof(GUARD_SIGNATURE)) != 0)
	{
		HandleMemoryCorruption(ptr, L"before", pCalleeAddress);
	}

	// Retrieve size of the allocation as requested in the call to malloc.
	size_t numbytes = ((size_t*)(mem))[0];

	if (numbytes == 0)
	{
		HandleMemoryCorruption(ptr, L"size=0", pCalleeAddress);
	}

	// Check the "guard" block right after the allocation
	if (memcmp(mem + sizeof(size_t) + sizeof(GUARD_SIGNATURE) + numbytes, GUARD_SIGNATURE, sizeof(GUARD_SIGNATURE)) != 0)
	{
		HandleMemoryCorruption(ptr, L"after", pCalleeAddress);
	}

	if (!::HeapFree(::GetProcessHeap(), 0, mem))
	{
		TRACE_WIN32_ERROR(HeapFree);
	}
}

//
// As the memory tracker is implemented as a singleton we have a kind of chicken and
// the egg problem when the tracker is initially created. First of all we need to make
// sure that only the first thread to call new/delete should be allowed to actually
// statically initialize the tracker singleton. This problem is solved by using the
// ThreadSafeSingleton class which takes care of the problem by implementing a "safe"
// version of GetInstance() for us.
//
// The second problem we need to solve are recursive calls into the new operator
// while the singleton is being constructed. Luckily for us ThreadSafeSingleton solves
// this issue as well by exposing the method IsConstructing() which let's us safely
// bypass  the special case and not dead-lock by recursively calling into GetInstance()
// while MemoryTracker is being constructed.
//

// Disable global optimization for the operators to stop Visual C++ from
// inlining the code too aggressively in release builds (breaks the order
// of the MemoryTracker::IsConstructing() checks).
#pragma optimize( "g", off )

#ifndef DEBUG_TOOLS_DISABLE_TRACK_MEMORY_ALLOC

void* __cdecl operator new(size_t numbytes)
{
	void* ptr = DebugMalloc(numbytes);

	if (!MemoryTracker::IsConstructing())
	{
		StackTrace trace;

#ifdef DEBUG_TOOLS_RECORD_STACKTRACE_ON_ALLOC
		if (!DebugHelpDLL::IsConstructing())
		{
			DebugHelpDLL::GetInstance()->GetStackTrace(trace);
		}
#endif

		MemoryTracker::GetInstance()->TrackAlloc(ptr, numbytes, false, _ReturnAddress(), trace);
	}

	return ptr;
}

void* __cdecl operator new(size_t numbytes, const std::nothrow_t &) throw()
{
	void* ptr = DebugMalloc(numbytes);

	if (!MemoryTracker::IsConstructing())
	{
		StackTrace trace;

#ifdef DEBUG_TOOLS_RECORD_STACKTRACE_ON_ALLOC
		if (!DebugHelpDLL::IsConstructing())
		{
			DebugHelpDLL::GetInstance()->GetStackTrace(trace);
		}
#endif

		MemoryTracker::GetInstance()->TrackAlloc(ptr, numbytes, false, _ReturnAddress(), trace);
	}

	return ptr;
}

void* __cdecl operator new[](size_t numbytes)
{
	void* ptr = DebugMalloc(numbytes);

	if (!MemoryTracker::IsConstructing())
	{
		StackTrace trace;

#ifdef DEBUG_TOOLS_RECORD_STACKTRACE_ON_ALLOC
		if (!DebugHelpDLL::IsConstructing())
		{
			DebugHelpDLL::GetInstance()->GetStackTrace(trace);
		}
#endif

		MemoryTracker::GetInstance()->TrackAlloc(ptr, numbytes, true, _ReturnAddress(), trace);
	}

	return ptr;
}

void* __cdecl operator new[](size_t numbytes, const std::nothrow_t &) throw()
{
	void* ptr = DebugMalloc(numbytes);

	if (!MemoryTracker::IsConstructing())
	{
		StackTrace trace;

#ifdef DEBUG_TOOLS_RECORD_STACKTRACE_ON_ALLOC
		if (!DebugHelpDLL::IsConstructing())
		{
			DebugHelpDLL::GetInstance()->GetStackTrace(trace);
		}
#endif

		MemoryTracker::GetInstance()->TrackAlloc(ptr, numbytes, true, _ReturnAddress(), trace);
	}

	return ptr;
}

void __cdecl operator delete(void* p)
{
	if (!MemoryTracker::IsConstructing())
	{
		MemoryTracker::GetInstance()->TrackFree(p, false, _ReturnAddress());
	}

	DebugFree(p, _ReturnAddress());
}

void __cdecl operator delete[](void* p)
{
	if (!MemoryTracker::IsConstructing())
	{
		MemoryTracker::GetInstance()->TrackFree(p, true, _ReturnAddress());
	}

	DebugFree(p, _ReturnAddress());
}

#endif

// Re-enable global optimization
#pragma optimize( "g", on )

///////////////////////////////////////////////////////////////////////////////////////////////////
// Debugging tools interface.
///////////////////////////////////////////////////////////////////////////////////////////////////

LONG WINAPI ForceMiniDumpExceptionFilter(_EXCEPTION_POINTERS * pExceptionContext)
{
	if (!DebugHelpDLL::GetInstance()->WriteMiniDump(pExceptionContext))
	{
		TRACE_WARN(L"Failed to write minidump");
	}

	return EXCEPTION_EXECUTE_HANDLER;
}

void ForceMiniDump()
{
	__try
	{
		FORCE_BREAK_INTO_DEBUGGER;
	}
	__except(ForceMiniDumpExceptionFilter(GetExceptionInformation()))
	{
	}
}

void ForceTerminate()
{
	//
	// Force termination to halt all threads within the process (attached
	// DLL:s won't get notified but since we can't be sure of the state
	// of the remaining threads we don't really have choice).
	//

	::TerminateProcess(::GetCurrentProcess(), EXIT_FAILURE);
}

LONG WINAPI CustomUnhandledExceptionFilter(_EXCEPTION_POINTERS * pExceptionContext)
{
	if (pExceptionContext != NULL && pExceptionContext->ExceptionRecord != NULL)
	{
		DWORD line;
		std::wstring funcname, filename;

		void* pAddress = pExceptionContext->ExceptionRecord->ExceptionAddress;

		if (pAddress && DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)pAddress, funcname, filename, line))
		{
			TRACE_ERROR(L"Unhandled SEH exception: %s in '%s' (%s:%d)",
			            SEH::GetDescription(pExceptionContext), funcname, filename, line);
		}
		else
		{
			TRACE_ERROR(L"Unhandled SEH exception: %s at address [%x]", SEH::GetDescription(pExceptionContext), pAddress);
		}
	}

	DebugTools::FatalError(L"Unhandled Exception", pExceptionContext);

	return EXCEPTION_CONTINUE_SEARCH;
}

void TerminateHandler()
{
	TRACE_ERROR(L"Intercepted call to std::terminate()");

	DebugTools::FatalError(L"Internal Error");

}

void UnexpectedHandler()
{
	TRACE_ERROR(L"Intercepted call to std::unexpected()");

	DebugTools::FatalError(L"Internal Error");
}

void AbortHandler(int signal)
{
	UNREFERENCED_PARAMETER(signal);

	TRACE_ERROR(L"Intercepted call to std::abort()");

	DebugTools::FatalError(L"Internal Error");
}

int OperatorNewFailedHandler(size_t numbytes)
{
	TRACE_ERROR(L"Memory allocation failed (new/malloc : %d bytes)", numbytes);

	DebugTools::FatalError(L"Internal Error");

	return 0;
}

int __cdecl CrtErrorHandler(int reportType, wchar_t* message, int *returnValue)
{
	if (reportType == _CRT_ERROR)
	{
		TRACE_ERROR(L"CRT_ERROR: %s", message);

		DebugTools::FatalError(L"Internal Error");
	}

	if (reportType == _CRT_ASSERT)
	{
		TRACE_ERROR(L"CRT_ASSERT: %s", message);

		DebugTools::FatalError(L"Assertion Failed");
	}

	if (returnValue)
	{
		*returnValue = 0;
	}

	return FALSE;
}

/**
 * Install and setup the debugging tools package for the designated module. After
 * a successful call hooks are inserted to handle CRT related error and to catch
 * unhandled exceptions, all without displaying any kind of dialog boxes or other
 * kinds of mechanisms which require user interaction. All reporting is done via
 * an overridable callback, which allows for customization and redirection of trace
 * output to suit both testing environments as well as production code.
 *
 * For programs which consist of separate modules it it's recommended to initialize
 * the main module first and then register any dynamically loaded modules.
 *
 * @param[in] pOutputCallback - custom report callback or NULL to use the builtin one
 * @param[in] pCrashCallback - custom crash callback or NULL to to use the builtin one
 */
void DebugTools::Install(DEBUG_TOOLS_OUTPUT_CALLBACK pOutputCallback, DEBUG_TOOLS_CRASH_CALLBACK pCrashCallback)
{
	g_bIsActive = true;

	::SetUnhandledExceptionFilter(CustomUnhandledExceptionFilter);

	// Force Windows to not display error dialog boxes for ::LoadLibrary
	// failures or general protection fault since we want to report such
	// errors manually via the console.
	::SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX |
	               SEM_NOOPENFILEERRORBOX);

	// Report CRT assert messages to STDERR (no dialog box)
	_CrtSetReportMode(_CRT_ASSERT, _CRTDBG_MODE_FILE);
	_CrtSetReportFile(_CRT_ASSERT, _CRTDBG_FILE_STDERR);

	// Report CRT error messages to STDERR (no dialog box)
	_CrtSetReportMode(_CRT_ERROR, _CRTDBG_MODE_FILE);
	_CrtSetReportFile(_CRT_ERROR, _CRTDBG_FILE_STDERR);

	// Report CRT warning messages to STDERR (no dialog box)
	_CrtSetReportMode(_CRT_WARN, _CRTDBG_MODE_FILE);
	_CrtSetReportFile(_CRT_WARN, _CRTDBG_FILE_STDERR);

	// Install a custom hook to catch CRT related errors (assertions etc).
	_CrtSetReportHookW2(_CRT_RPTHOOK_INSTALL, CrtErrorHandler);

	// Hook in the C++ exception handler to intercept calls to
	// terminate() when no matching exception handler is found.
	::set_terminate(TerminateHandler);

	// Hook in the C++ exception handler to intercept calls to
	// unexpected() when an exception is thrown in violating with
	// the method exception specification (example: a method is
	// declared with throw() and throws an an exception).
	::set_unexpected(UnexpectedHandler);

	// Hook into the CRT to intercept the abort() signal.
	::signal(SIGABRT, AbortHandler);

	// Suppress the warning printed when abort() is called.
	::_set_abort_behavior(0, _WRITE_ABORT_MSG);

	// Disable automatic crash dump generation via Windows Error Reporting.
	::_set_abort_behavior(0, _CALL_REPORTFAULT);

	// Send CRT error messages to stderr instead of displaying a dialog.
	::_set_error_mode(_OUT_TO_STDERR);

	// Hook in the CRT memory manager to intercept when operator new fails to
	// allocate memory instead of relying on a std::bad_alloc exception which
	// may or may not be thrown and work correctly in multi-threaded environment.
	::_set_new_handler(OperatorNewFailedHandler);

	// Tell the CRT to redirect failed malloc() calls to the overridden operator
	// new handler declared above. This allows us to handle memory allocation in
	// a unified way and not have any CRT calls magically abort during execution.
	::_set_new_mode(1);

	// Enable the low-fragmentation heap (Windows XP/2003+) to combat performance
	// issues related to common C++ allocation patternd (small allocation sizes,
	// repeated allocated/deallocation, naive STL allocators). For some reason this
	// call will fail when running the program under the VS debugger.
	if (!::IsDebuggerPresent())
	{
		ULONG  EnableLowFragHeap = 2;
		if (!::HeapSetInformation(::GetProcessHeap(), HeapCompatibilityInformation, &EnableLowFragHeap, sizeof(EnableLowFragHeap)))
		{
			TRACE_WIN32_ERROR(HeapSetInformation);
		}
	}

	//
	// Setup custom reporting and crash notification callbacks.
	//

	if (pOutputCallback)
	{
		g_pfnOutputCallback = pOutputCallback;
	}
	else
	{
		g_pfnOutputCallback = DefaultOutputCallbackImpl;
	}

	if (pCrashCallback)
	{
		g_pfnCrashCallback = pCrashCallback;
	}
	else
	{
		g_pfnCrashCallback = DefaultCraschCallbackImpl;
	}
}

/**
 * Allocate and configure a console window for viewing trace output (only needed 
 * if application is not configured to link with the console subsystem).
 */
void DebugTools::ShowConsole()
{
	InitDebugConsole();
}

/**
 * Set the default directory where crash report dump files are saved (default = current directory).
 *
 * NOTE: Make sure that the path exists in the system and that "everyone" has
 * read & write access rights to that location or else mini-dumps will not be saved.
 *
 * @param[in,out] path - directory where mini-dumps are saved.
 */
void DebugTools::SetMinidumpStoragePath(const std::wstring& path)
{
	g_minidumpSavePath = path;

	EnsureTerminatingSlash(g_minidumpSavePath);
}

/**
 * Global handler for assertion failure, should only be used in conjunction
 * with the DebugTools assertion macro.
 *
 * @param[in] expr - assertion expression
 * @param[in] file - path to file where the error occurred
 * @param[in] line - line offset to the assert statement
 */
void DebugTools::AssertionFailed(const wchar_t* expr, const wchar_t* file, unsigned int line)
{
	//
	// Ignore error as debugging package hasn't been activated.
	//

	if (!g_bIsActive)
	{
		return;
	}

	TRACE_ERROR(L"Assertion failed: (%s) in %s:%d", expr, file, line);

	::InterlockedIncrement(&g_ErrorCount);

	if (g_ErrorCount == 1)
	{
		if (::IsDebuggerPresent())
		{
			// We'll fall trough and let the assertion macro which called this
			// handler break at the exact location of the error if we're running
			// under a debugger (only the first thread is allowed to break,
			// remaining threads are collected below).
		}
		else
		{
			try
			{
				DebugHelpDLL::GetInstance()->DumpStackTrace(L"current");

				ForceMiniDump();

				//
				// Invoke the custom crash handler to care of reporting the error etc...
				//

				wchar_t pwszErrorMessage[2048];

				_snwprintf_s(
				    pwszErrorMessage,
				    _countof(pwszErrorMessage),
				    L"Assertion failed: (%s) in %s:%d", expr, file, line);

				g_pfnCrashCallback(pwszErrorMessage);

			}
			catch (...)
			{
			}

			ForceTerminate();
		}
	}
	else
	{
		// In order to correctly handle situations where multiple threads
		// simultaneously cause assertion errors we only allow the first
		// thread to break/halt execution. Remaining threads will end up
		// here and wait in an infinite "sleep" loop. The idea is that that
		// we'll break in the first thread and "suspend" all other threads
		// so that we can manually examine them using a debugger.

		for (;;)
		{
			::Sleep(100);
		}
	}
}

/**
 * Generic handler for fatal errors, will report the error via the DebugTools
 * callback as well as write a minidump for postmortem debugging if we aren't
 * running under a debugger. Will eventually forcefully terminate execution of
 * the program as we most likely have hit a unrecoverable error.
 *
 * @param[in] pwszReason - simple description of the error
 * @param[in] pExceptionContext - SEH exception pointer or NULL
 */
void DebugTools::FatalError(const wchar_t* pwszReason, _EXCEPTION_POINTERS * pExceptionContext)
{
	//
	// Ignore error as debugging package hasn't been activated.
	//

	if (!g_bIsActive)
	{
		return;
	}

	TRACE_ERROR(L"%s", pwszReason);

	::InterlockedIncrement(&g_ErrorCount);

	if (g_ErrorCount == 1)
	{
		try
		{
			const void* pCalleeAddres = _ReturnAddress();

			DWORD line;
			std::wstring funcname, filename;

			if (DebugHelpDLL::GetInstance()->GetSymbolForAddress((DWORD64)pCalleeAddres, funcname, filename, line))
			{
				TRACE(L"Fatal error occured in '%s' in %s:%d", funcname, filename, line);
			}
			else
			{
				TRACE(L"Fatal error occured at address [%x]", pCalleeAddres);
			}

			DebugHelpDLL::GetInstance()->DumpStackTrace(L"current");

			if (pExceptionContext)
			{
				if (!DebugHelpDLL::GetInstance()->WriteMiniDump(pExceptionContext))
				{
					TRACE_WARN(L"Failed to write minidump");
				}
			}
			else
			{
				ForceMiniDump();
			}

			//
			// Invoke the custom crash handler to care of reporting the error etc...
			//

			g_pfnCrashCallback(pwszReason);

		}
		catch (...)
		{
		}

		if (::IsDebuggerPresent())
		{
			FORCE_BREAK_INTO_DEBUGGER;
		}
		else
		{
			ForceTerminate();
		}
	}
	else
	{
		// In order to correctly handle situations where multiple threads
		// simultaneously cause fatal errors we only allow the first
		// thread to break/halt execution. Remaining threads will end up
		// here and wait in an infinite "sleep" loop. The idea is that that
		// we'll break in the first thread and "suspend" all other threads
		// so that we can manually examine them using a debugger.

		for (;;)
		{
			::Sleep(100);
		}
	}
}

/**
 * Record a checkpoint of all allocations so far in order to exclude them from a future
 * calls to DumpMemoryLeaks(). The idea is to call this method when the CRT and your
 * application have finished initializing and pair the call with a call to DumpMemoryLeaks()
 * later on to find out if the code which executed between the calls is leaking memory.
 */
void DebugTools::SetMemoryCheckPoint()
{
#ifndef DEBUG_TOOLS_DISABLE_TRACK_MEMORY_ALLOC
	MemoryTracker::GetInstance()->SetMemoryCheckPoint();
#endif
}

/**
 * Report any memory leaks detected by the memory tracker.
 *
 * @return true/false if any memory leaks were detected
 */
bool DebugTools::DumpMemoryLeaks()
{
#ifndef DEBUG_TOOLS_DISABLE_TRACK_MEMORY_ALLOC
	return MemoryTracker::GetInstance()->DumpLeaks();
#else
	return false;
#endif
}


/**
 * Dump statistical information about memory usage etc..
 */
void DebugTools::DumpMemoryStats()
{
#ifndef DEBUG_TOOLS_DISABLE_TRACK_MEMORY_ALLOC
	return MemoryTracker::GetInstance()->DumpStats();
#endif
}

/**
 * Debugging aid use for narrowing down the exact location of a possible
 * heap corruption. Run this method around the sections of code where you
 * believe the error to exists and it will break and report the allocation
 * which is considered invalid. NOTE: This function will NOT return if a
 * memory corruption is detected.
 */
void DebugTools::VerifyHeapIntegrity()
{
#ifndef DEBUG_TOOLS_DISABLE_TRACK_MEMORY_ALLOC
	return MemoryTracker::GetInstance()->VerifyHeapIntegrity();
#endif
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Thread-safe debug trace support.
///////////////////////////////////////////////////////////////////////////////////////////////////

void DebugTools::TraceOutputDebug(const wchar_t* message)
{
	try
	{
		g_pfnOutputCallback(DEBUG_TOOLS_CALLBACK_TRACE_DEBUG, message);
	}
	catch (...)
	{
		ForceTerminate();
	}
}


void DebugTools::TraceOutputWarning(const wchar_t* message)
{
	try
	{
		g_pfnOutputCallback(DEBUG_TOOLS_CALLBACK_TRACE_WARNING, message);
	}
	catch (...)
	{
		ForceTerminate();
	}
}

void DebugTools::TraceOutputError(const wchar_t* message)
{
	try
	{
		g_pfnOutputCallback(DEBUG_TOOLS_CALLBACK_TRACE_ERROR, message);
	}
	catch (...)
	{
		ForceTerminate();
	}
}

void DebugTools::TraceOutputWin32Error(const wchar_t* win32func, DWORD dwError, const wchar_t* funcname, const wchar_t* filename, int linenr)
{
	wchar_t wszTempBuf[1024];

	_snwprintf_s(wszTempBuf, _countof(wszTempBuf), L"%s failed with error message '%s' in method '%s' (%s:%d)",
	             win32func, FormatWin32ErrorCode(dwError).c_str(), funcname, filename, linenr);

	TraceOutputError(wszTempBuf);
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Test runner.
///////////////////////////////////////////////////////////////////////////////////////////////////

/**
 * Run a batch script using cmd.exe while redirecting both stdout and stderr to
 * a logfile (naming it as the name of the batch script appended with ".log").
 *
 * @param[in,out] filepath - full path to batch script
 * @return true/false to signal success/failure
 */
void RunTestSetupBatchScript()
{
	wchar_t tempbuf[1024];

	if (::GetModuleFileName(NULL, tempbuf, _countof(tempbuf)) > 0)
	{
		std::wstring filepath = tempbuf;

		filepath.replace(filepath.find_last_of(L"."), std::wstring::npos, L".bat");

		if (::GetFileAttributes(filepath.c_str()) != INVALID_FILE_ATTRIBUTES)
		{
			_snwprintf_s(tempbuf, _countof(tempbuf), L"%s > %s.log 2>&1", filepath.c_str(), filepath.c_str());

			if (_wsystem(tempbuf) == 0)
			{
				TRACE(L"Test setup batch script executed successfully");
			}
			else
			{
				TRACE_WARN(L"Failed to execute test setup batch script: %s", filepath);
			}
		}
	}
}

/**
 * Generic test runner which runs tests in a debug friendly environment to
 * automatically detect memory related issues (leaks, corruptions, etc)
 * and any unhandled exceptions. To setup complex test scenario two optional
 * functions can be passed to setup or cleanup (tear down) the test, if any
 * of these functions return false we consider the test to be unsuccessful.
 *
 * No special macros are needed to write tests, the default assertion macro
 * works just fine as well as using std::exceptions to signal failure. If the
 * test runner needs to abort testing and terminate the process due a fatal
 * error (access violation etc) it will set the exit code to EXIT_FAILURE.
 *
 * NOTE: If there exists a batch script with the same base name as the current
 * process (TestFoo.exe => TestFoo.bat) we will automatically execute before
 * each test run - before the call to TestSetup().
 *
 * Example:
 *
 *     bool TestSetup()
 *     {
 *         return true;
 *     }
 *
 *     void TestMain()
 *     {
 *         assert( 1 == 0 );
 *     }
 *
 *     bool TestClean()
 *     {
 *         return true;
 *     }
 *
 *     int main( int argc, wchar_t* argv[] )
 *     {
 *         DebugTools::Install( NULL );
 *         if( DebugTools::RunTest( TestSetup, TestMain, TestClean ) )
 *             return EXIT_SUCCESS;
 *         else
 *             return EXIT_FAILURE;
 *     }
 *
 * @param[in] pfnTestSetup - custom setup function (fixture create) or NULL
 * @param[in] pfnTestMain - main test runner function
 * @param[in] pfnTestClean - cleanup function (fixture tear down) or NULL
 * @param[in] numruns - how many times should the test cycle be repeated (default 1)
 */
bool DebugTools::RunTest(bool(*pfnTestSetup)(), void(*pfnTestMain)(), bool(*pfnTestClean)(), int numruns)
{
	g_bIsTesting = true;

	if (!g_bIsActive)
	{
		TRACE_ERROR(L"Debug tools must installed before running test");
		return false;
	}

	bool bSuccess = true;

	try
	{
		for (int i = 0; i < numruns; ++i)
		{
			//
			// Always run from the directory where the executable is located.
			//

			if (!SetCurrentDirectoryToExePath())
			{
				TRACE_ERROR(L"Could not set current directory to executable path");
				bSuccess = false;
				break;
			}

			RunTestSetupBatchScript();

			//
			// Reset current directory if batch script somehow modified it.
			//

			if (!SetCurrentDirectoryToExePath())
			{
				TRACE_ERROR(L"Could not set current directory to executable path");
				bSuccess = false;
				break;
			}

			if (pfnTestSetup)
			{
				if (!pfnTestSetup())
				{
					TRACE_ERROR(L"Test setup failed!");
					bSuccess = false;
					break;
				}
			}

			if (pfnTestMain)
			{
				MemoryTracker::GetInstance()->SetMemoryCheckPoint();

				pfnTestMain();

				if (MemoryTracker::GetInstance()->DumpLeaks())
					bSuccess = false;
			}

			if (pfnTestClean)
			{
				if (!pfnTestClean())
				{
					TRACE_ERROR(L"Test cleanup failed!");
					bSuccess = false;
					break;
				}
			}
		}
	}
	catch (std::exception& ex)
	{
		//
		// During development we don't really want the unhandled exception
		// to be silently reported as a test failure but rather want to examine
		// the call-stack etc. To simulate the desired behavior we'll re-throw
		// the exception when the debugger is attached and let it handled it.
		//

		if (::IsDebuggerPresent())
		{
			throw;
		}
		else
		{
			TRACE_ERROR(L"std::exception caught in DebugTools::RunTest() : %s", ex.what());
			bSuccess = false;
		}
	}

	g_bIsTesting = false;

	return bSuccess;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
