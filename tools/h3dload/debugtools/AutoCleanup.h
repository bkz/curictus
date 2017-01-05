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

#pragma once

#include "DebugTools.h"

///////////////////////////////////////////////////////////////////////////////
// Policy-driven scoped resource manager.
///////////////////////////////////////////////////////////////////////////////

/*

 An AutoObject will wrap a pointer of type T and take care of freeing the pointer
 via a custom policy object when the AutoObject instance is destroyed. The intended
 usage of an AutoObject is to automatically manage resources on a function/method
 scope level so that the programmer doesn't have to manually free up resources in
 complex code paths. By also taking care of validating the pointer against special
 "null" value placeholders coding becomes less error prone as you don't have to
 remember the "null" value for each resource type - you only need to specify it
 once when you create a new AutoObject typedef for a resource.

 Example: Win32 file HANDLE

    struct FileHandlePolicy {
        static void Free(HANDLE h) throw() { ::CloseHandle(h); }
    };

    typedef AutoObject<HANDLE, FileHandlePolicy, INVALID_HANDLE_VALUE> AutoCloseFile;

    {
        //
        // Take ownership of a file handle resource (automatically closed via
        // FileHandlePolicy::Free() when leave the scope).
        //

        AutoCloseFile h = ::CreateFile(...);

        // No need to remember that Win32 file handles use INVALID_HANDLE_VALUE and not NULL
        if( h.IsValid() )
        {
            // Automatic conversion from wrapped resource to HANDLE object
            ::ReadFile(h, ...);
        }
    }

*/

template <typename T, typename Policy, T EmptyValue>
struct AutoObject
{
	inline AutoObject()
	{
		m_data = EmptyValue;
	}

	inline AutoObject(T value)
	{
		m_data = value;
	}

	inline ~AutoObject() throw()
	{
		Release();
	}

	inline BOOL IsValid() const throw()
	{
		return m_data != EmptyValue;
	}

	inline AutoObject& operator = (T value) throw()
	{
		Release();
		m_data = value;
		return *this;
	};

	inline operator bool() throw()
	{
		STATIC_ASSERT(0); // Implicit boolean casts are not allowed!
	}

	inline operator T() throw()
	{
		return m_data;
	}

	template <typename P>
	inline operator P() throw()
	{
		assert(m_data != EmptyValue);
		return static_cast<P>(m_data);
	}

	T* operator & ()
	{
		return &m_data;
	}

	const T* operator & () const
	{
		return &m_data;
	}

	void Release() throw()
	{
		if (m_data != EmptyValue)
		{
			Policy::Free(m_data);
			m_data = EmptyValue;
		}
	}

private:
	FORBID_COPY_CTOR(AutoObject);
	FORBID_ASSIGNMENT(AutoObject);

	T m_data;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// Generate automatic managers for native Win32 resource types.
///////////////////////////////////////////////////////////////////////////////////////////////////

// Wrapper for types where the resource free callback doesn't have a return value.
#define MAKE_AUTO_OBJECT_VOID(xClassName, xDataType, xCallback, xEmptyValue)            \
    struct xClassName##Policy {                                                         \
        static inline void Free(xDataType data) throw() { (void)xCallback(data); }      \
    };                                                                                  \
    typedef AutoObject<xDataType, xClassName##Policy, (xDataType)(xEmptyValue)> xClassName;

// Wrapper for types where the resource free callback returns true to signal success.
#define MAKE_AUTO_OBJECT_TRUE(xClassName, xDataType, xCallback, xEmptyValue)            \
    struct xClassName##Policy {                                                         \
        static inline void Free(xDataType data) throw()                                 \
        { if( xCallback(data) != TRUE ) TRACE_WIN32_ERROR(xCallback); }                 \
    };                                                                                  \
    typedef AutoObject<xDataType, xClassName##Policy, (xDataType)(xEmptyValue)> xClassName;

// Wrapper for types where the resource free callback returns 0 (ERROR_SUCCESS) to signal success.
#define MAKE_AUTO_OBJECT_ZERO(xClassName, xDataType, xCallback, xEmptyValue)            \
    struct xClassName##Policy {                                                         \
  static inline void Free(xDataType data) throw()                                       \
   { if( xCallback(data) != ERROR_SUCCESS ) TRACE_WIN32_ERROR(xCallback); }             \
 };                                                                                     \
 typedef AutoObject<xDataType, xClassName##Policy, (xDataType)(xEmptyValue)> xClassName;

//                    -------                   ---------       ----------------        -------------------
//                    Typedef                   Data type       Callback to wrap        Default empty value
//                    -------                   ---------       ----------------        -------------------
MAKE_AUTO_OBJECT_TRUE(AutoCloseHandle,          HANDLE,         ::CloseHandle,          NULL);
MAKE_AUTO_OBJECT_TRUE(AutoCloseFile,            HANDLE,         ::CloseHandle,          INVALID_HANDLE_VALUE);
MAKE_AUTO_OBJECT_TRUE(AutoFindClose,            HANDLE,         ::FindClose,            INVALID_HANDLE_VALUE);
MAKE_AUTO_OBJECT_TRUE(AutoCloseDesktop,         HDESK,          ::CloseDesktop,         NULL);
MAKE_AUTO_OBJECT_TRUE(AutoCloseWindowStation,   HWINSTA,        ::CloseWindowStation,   NULL);
MAKE_AUTO_OBJECT_ZERO(AutoRegCloseKey,          HKEY,           ::RegCloseKey,          NULL);
MAKE_AUTO_OBJECT_TRUE(AutoUnmapViewOfFile,      PVOID,          ::UnmapViewOfFile,      NULL);
MAKE_AUTO_OBJECT_TRUE(AutoFreeLibrary,          HMODULE,        ::FreeLibrary,          NULL);
MAKE_AUTO_OBJECT_TRUE(AutoCloseServiceHandle,   SC_HANDLE,      ::CloseServiceHandle,   NULL);
MAKE_AUTO_OBJECT_VOID(AutoFclose,               FILE*,          fclose,                 NULL);

#undef MAKE_AUTO_OBJECT_VOID
#undef MAKE_AUTO_OBJECT_TRUE

///////////////////////////////////////////////////////////////////////////////////////////////////
// Generate automatic managers for resource with special deallocation policies.
///////////////////////////////////////////////////////////////////////////////////////////////////

struct HeapFreePolicy
{
	static inline void Free(PVOID ptr) throw()
	{
		::HeapFree(::GetProcessHeap(), 0, ptr);
	}
};

typedef AutoObject<PVOID, HeapFreePolicy, NULL> AutoHeapFree;

template <typename T>
struct LocalFreePolicy
{
	static inline void Free(T ptr) throw()
	{
		::LocalFree((PVOID)(ptr));
	}
};

template <typename T>
struct AutoLocalFree : public AutoObject<T, LocalFreePolicy<T>, NULL> {};



///////////////////////////////////////////////////////////////////////////////////////////////////
// Generic scoped locking mechanism (critical sections).
///////////////////////////////////////////////////////////////////////////////////////////////////

template <typename T>
struct AutoLock
{
	AutoLock(T* pObj) : m_pObj(pObj)
	{
		assert(m_pObj != NULL);
		m_pObj->Lock();
	}

	AutoLock(const T* pObj) : m_pObj(const_cast<T*>(pObj))
	{
		assert(m_pObj != NULL);
		m_pObj->Lock();
	}

	~AutoLock()
	{
		assert(m_pObj != NULL);
		m_pObj->Unlock();
	}

private:
	T* m_pObj;
};

struct LockCS
{
	LockCS()
	{
		::InitializeCriticalSection(&m_cs);
	}

	~LockCS()
	{
		::DeleteCriticalSection(&m_cs);
	}

	void Lock()
	{
		::EnterCriticalSection(&m_cs);
	}

	bool TryLock()
	{
		return (::TryEnterCriticalSection(&m_cs) == TRUE);
	}

	void Unlock()
	{
		LeaveCriticalSection(&m_cs);
	}

private:
	CRITICAL_SECTION m_cs;
};
typedef AutoLock<LockCS> AutoLockCS;

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
