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
#include "Trace.h"
using namespace std;

WideStreamFormat::WideStreamFormat(std::wostream& stream, const std::wstring& fmt)
		: m_stream(stream), m_format(fmt), m_pos(0)
{
	m_len = m_format.length();
}

WideStreamFormat::~WideStreamFormat()
{
	MoveToNextFormatSpecifier();

	if (IsAtEnd() != true)
	{
		DebugTools::FatalError(L"Too few arguments were passed, entire format string not consumed");
	}
}

/**
 * Attempt to parse format options for the next argument and set
 * appropriate stream options.
 */
void WideStreamFormat::ParseNextFormatSpecifier()
{
	if (IsAtEnd() == true)
	{
		DebugTools::FatalError(L"Too many arguments were passed, already at end of format string");
	}

	MoveToNextFormatSpecifier();

	int width = 0;
	int precision = 6;
	int flags = 0;
	wchar_t fill = L' ';
	bool alternate = false;

	if (m_format[m_pos] != L'%')
	{
		DebugTools::FatalError(L"Invalid format string, can't format argument");
	}

	m_pos++;

	// These flags can run through multiple characters (we don't bother
	// checking the order or the validity of the combinations).
	while (m_pos < m_len)
	{
		bool done = false;

		switch (m_format[m_pos])
		{
			case L'+':
				flags |= ios::showpos;
				break;
			case L'-':
				flags |= ios::left;
				break;
			case L'0':
				flags |= ios::internal;
				fill = L'0';
				break;
			case L'#':
				alternate = true;
				break;
			default:
				done = true;
				break;
		}

		if (done)
			break;

		m_pos++;
	}

	if (m_pos >= m_len)
	{
		DebugTools::FatalError(L"Incomplete format specification, format string ended prematurely");
	}

	// Parse width specifier.
	if ((m_pos < m_len) && iswdigit(m_format[m_pos]))
	{
		width = _wtoi(&m_format[m_pos]);
		do
		{
			m_pos++;
		}
		while ((m_pos < m_len) && iswdigit(m_format[m_pos]));
	}

	// Parse output precision.
	if ((m_pos < m_len) && m_format[m_pos] == L'.')
	{
		m_pos++;

		if (m_pos < m_len)
		{
			precision = _wtoi(&m_format[m_pos]);

			do
			{
				m_pos++;
			}
			while ((m_pos < m_len) && iswdigit(m_format[m_pos]));
		}
	}

	if (m_pos >= m_len)
	{
		DebugTools::FatalError(L"Incomplete format specification, format string ended prematurely");
	}

	// Parse type information to set correct stream formatting options.
	switch (m_format[m_pos])
	{
		case L'p':
			break;
		case L's':
			break;
		case L'c':
		case L'C':
			break;
		case L'i':
		case L'u':
		case L'd':
			flags |= ios::dec;
			break;
		case L'x':
			flags |= ios::hex;
			if (alternate) flags |= ios::showbase;
			break;
		case L'X':
			flags |= ios::hex | ios::uppercase;
			if (alternate) flags |= ios::showbase;
			break;
		case L'o':
			flags |= ios::hex;
			if (alternate) flags |= ios::showbase;
			break;
		case L'f':
			flags |= ios::fixed;
			if (alternate) flags |= ios::showpoint;
			break;
		case L'e':
			flags |= ios::scientific;
			if (alternate) flags |= ios::showpoint;
			break;
		case L'E':
			flags |= ios::scientific | ios::uppercase;
			if (alternate) flags |= ios::showpoint;
			break;
		case L'g':
			if (alternate) flags |= ios::showpoint;
			break;
		case L'G':
			flags |= ios::uppercase;
			if (alternate) flags |= ios::showpoint;
			break;
		default:
			DebugTools::FatalError(L"Invalid type specifier");
			break;
	}

	m_stream.unsetf(ios::adjustfield | ios::basefield | ios::floatfield);
	m_stream.setf(flags);
	m_stream.width(width);
	m_stream.precision(precision);
	m_stream.fill(fill);

	// Move past the last character (type specifier) of this format specification
	m_pos++;
}

/**
 * Emit static data in format string move to the next specification
 * in the format string (% character).
 */
void WideStreamFormat::MoveToNextFormatSpecifier()
{
	while (m_pos < m_len)
	{
		if (m_format[m_pos] == L'%')
		{
			// Two % in a row should output a single % and not evaluate to a format specification.
			if ((m_pos < m_len) && m_format[m_pos+1] == L'%')
				m_pos++;
			else
				break;
		}

		m_stream << m_format[m_pos];
		m_pos++;
	}
}
