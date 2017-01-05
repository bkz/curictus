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

#ifndef CURICTUS_COMMON_TRACE_H
#define CURICTUS_COMMON_TRACE_H

#include <sstream>
#include <string>

///////////////////////////////////////////////////////////////////////////////////////////////////
// Utility class which allow formatting of iostreams using the standard printf syntax.
///////////////////////////////////////////////////////////////////////////////////////////////////

//
// Example:
//
//   WideStreamFormat format( std::cout, L"%d %c %d = %d" ) << 1 << '+' << 1 << 2;
//

struct WideStreamFormat
{
	WideStreamFormat(std::wostream& stream, const std::wstring& fmt);
	~WideStreamFormat();

	inline WideStreamFormat& operator << (const void* p)
	{
		ParseNextFormatSpecifier();
		m_stream << p;
		return *this;
	}

	inline WideStreamFormat& operator << (const char* s)
	{
		ParseNextFormatSpecifier();
		m_stream << s;
		return *this;
	}

	inline WideStreamFormat& operator << (const wchar_t* s)
	{
		ParseNextFormatSpecifier();
		m_stream << s;
		return *this;
	}

	template <typename T>
	inline WideStreamFormat& operator << (const T* ptr)
	{
		STATIC_ASSERT(FALSE);
		return *this;
	}

	template <typename T>
	inline WideStreamFormat& operator << (const T& value)
	{
		ParseNextFormatSpecifier();
		m_stream << value;
		return *this;
	}

private:
	WideStreamFormat(const WideStreamFormat&);
	void operator=(WideStreamFormat&);

	bool IsAtEnd()
	{
		return (m_pos == m_len);
	}

	void ParseNextFormatSpecifier();
	void MoveToNextFormatSpecifier();

	std::wostream&              m_stream;
	std::wstring                m_format;
	std::wstring::size_type     m_pos;
	std::wstring::size_type     m_len;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// NOTE: This code below is auto generated, don't modify.
///////////////////////////////////////////////////////////////////////////////////////////////////

inline void TRACE(const std::wstring& fmt)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt);
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1>
inline void TRACE(const std::wstring& fmt, const T1& t1)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10, typename T11>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10, const T11& t11)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10 << t11;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10, typename T11, typename T12>
inline void TRACE(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10, const T11& t11, const T12& t12)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10 << t11 << t12;
	}
	DebugTools::TraceOutputDebug(ss.str().c_str());
}


inline void TRACE_WARN(const std::wstring& fmt)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt);
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10, typename T11>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10, const T11& t11)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10 << t11;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10, typename T11, typename T12>
inline void TRACE_WARN(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10, const T11& t11, const T12& t12)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10 << t11 << t12;
	}
	DebugTools::TraceOutputWarning(ss.str().c_str());
}


inline void TRACE_ERROR(const std::wstring& fmt)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt);
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10, typename T11>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10, const T11& t11)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10 << t11;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}


template <typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8, typename T9, typename T10, typename T11, typename T12>
inline void TRACE_ERROR(const std::wstring& fmt, const T1& t1, const T2& t2, const T3& t3, const T4& t4, const T5& t5, const T6& t6, const T7& t7, const T8& t8, const T9& t9, const T10& t10, const T11& t11, const T12& t12)
{
	std::wostringstream ss;
	{
		WideStreamFormat(ss, fmt) << t1 << t2 << t3 << t4 << t5 << t6 << t7 << t8 << t9 << t10 << t11 << t12;
	}
	DebugTools::TraceOutputError(ss.str().c_str());
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_COMMON_TRACE_H
