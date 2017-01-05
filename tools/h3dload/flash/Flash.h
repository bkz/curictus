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

#ifndef CURICTUS_FLASH_H
#define CURICTUS_FLASH_H

///////////////////////////////////////////////////////////////////////////////////////////////////
// Import Flash 10 ActiveX control.
///////////////////////////////////////////////////////////////////////////////////////////////////

#import "PROGID:ShockwaveFlash.ShockwaveFlash" named_guids exclude("IServiceProvider")

///////////////////////////////////////////////////////////////////////////////////////////////////
// Forward declarations.
///////////////////////////////////////////////////////////////////////////////////////////////////

class FlashPlayer;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Flash runtime interfance.
///////////////////////////////////////////////////////////////////////////////////////////////////

class Flash
{
public:
	Flash();
	~Flash();

	// Access global Flash runtime instance.
	static Flash* GetInstance();

	// Return version of installed Flash ActiveX control (e.g. 10.0).
	double GetFlashVersion();

	// Returns NULL on failure, can be called multiple times to create different players.
	FlashPlayer* CreatePlayer(unsigned int width, unsigned int height);

	// Destroy and deallocate a player instance.
	void DestroyPlayer(FlashPlayer* pPlayer);

protected:
	HMODULE m_flashLibHandle;		
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_FLASH_H
