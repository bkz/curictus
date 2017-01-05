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

#ifndef CURICTUS_FLASH_EVENT_HANDLER_H
#define CURICTUS_FLASH_EVENT_HANDLER_H

#include <windows.h>

// NOTE: FlashCall() uses the AS3 ExternalInterface API XML format.

struct IFlashEventHandler
{
	// Called when AS3 scripts use ExternalInterface.call() with an XML request. You should 
	// return NOERROR if request was processess successfully, E_NOTIMPL if wasn't recognized 
	// as a valid call or any other COM error to signal status back to the Flash runtime.
	virtual HRESULT FlashCall(const wchar_t* request) = 0;

	// Called when AS3 scripts use fscommand() with a command and arguments string. You should 
	// return NOERROR if request was processess successfully, E_NOTIMPL if wasn't recognized 
	// as a valid call or any other COM error to signal status back to the Flash runtime.
	virtual HRESULT FSCommand(const wchar_t* command, const wchar_t* args) = 0;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_FLASH_EVENT_HANDLER_H
