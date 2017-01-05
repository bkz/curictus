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

#include "Flash.h"
#include "FlashPlayer.h"
using namespace ShockwaveFlashObjects;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Global Flash runtime instance.
///////////////////////////////////////////////////////////////////////////////////////////////////

Flash g_instance;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Flash runtime implementation.
///////////////////////////////////////////////////////////////////////////////////////////////////

Flash::Flash()
{
	CoInitialize(NULL);
	m_flashLibHandle = LoadLibrary(L"flash10.ocx");
}

Flash::~Flash()
{
	FreeLibrary(m_flashLibHandle);	
	CoUninitialize();
}

Flash* Flash::GetInstance()
{
	return &g_instance;
}

double Flash::GetFlashVersion()
{
	IOleObject* pOleObject = NULL;
	if (FAILED(CoCreateInstance(CLSID_ShockwaveFlash, NULL, CLSCTX_INPROC_SERVER, IID_IOleObject, (void**) &pOleObject)))
		return 0.0;	

	IShockwaveFlash* pFlashInterface = NULL;
	if (FAILED(pOleObject->QueryInterface(__uuidof(IShockwaveFlash), (LPVOID*) &pFlashInterface)))
		return 0.0;

	long version = pFlashInterface->FlashVersion();

	pFlashInterface->Release();
	pOleObject->Release();

	return version / 65536.0;
}

FlashPlayer* Flash::CreatePlayer(unsigned int width, unsigned int height)
{
	FlashPlayer* player = new FlashPlayer(m_flashLibHandle, width, height);
	if (player->m_flashInterface == NULL)
	{
		delete player;
		return NULL;
	}
	return player;
}

void Flash::DestroyPlayer(FlashPlayer* pPlayer)
{
	delete (FlashPlayer*)pPlayer;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
