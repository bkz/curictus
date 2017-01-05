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

#ifndef CURICTUS_FLASH_PLAYER_H
#define CURICTUS_FLASH_PLAYER_H

#include "FlashEventHandler.h"
#include "FlashControlSite.h"
#include "FlashSink.h"
#include <vector>
#include <string>

// NOTE: FlashPlayer is not thread-safe, using mutexes or critical sections
// if you want to read (IsUpdateNeeded) and write (DrawFrame) in parallell 
// from multiple threads.

class FlashPlayer
{
	friend class Flash;
	friend class FlashControlSite;
	friend class FlashSink;

public:

	enum EState
	{
		STATE_IDLE = 0,			// No movie loaded.
		STATE_PLAYING,
		STATE_STOPPED
	};
	enum ETransparencyMode
	{
		TMODE_OPAQUE      = 0,	// Alpha is disabled.
		TMODE_TRANSPARENT = 1,	// Basic alpha, no semi-transparency.
		TMODE_FULL_ALPHA  = 2,	// Alpha fully supported. A bit slower (not much) than TMODE_TRANSPARENT.
	};
	enum EQuality
	{
		QUALITY_LOW = 0,
		QUALITY_MEDIUM,
		QUALITY_HIGH,
		QUALITY_BEST,
		QUALITY_AUTOLOW,
		QUALITY_AUTOHIGH
	};
	enum EMouseButton
	{
		eMouse1 = 0,			// Left mouse button.
		eMouse2,				// Right mouse button.
		eMouse3,				// Middle (wheel) mouse button.
		eMouse4,
		eMouse5,
	};

public:

	// If the dll/ocx could not be located set `flashDLL` to NULL to force an 
	// attempt to create the player COM instance using "DllGetClassObject".
	FlashPlayer(HMODULE flashDLL, unsigned int width, unsigned int height);
	
	virtual ~FlashPlayer();

	// Adds dirty rectangle, will be combined as need to reduce the number of 
	// draw actions when rendering next frame.
	void AddDirtyRect(const RECT* pRect);

	/// Callbacks when AS3 scripts invoke fscommand() or ExternalInterface.call(), 
	// see IFlashEventHandler for more information.
	HRESULT FlashCall(const wchar_t* request);
	HRESULT FSCommand(const wchar_t* command, const wchar_t* args);

	// Retrieve playback state of player instance.
	EState GetState() const;

	// Rendering quality setting.
	EQuality GetQuality() const;
	void SetQuality(EQuality quality);
	
	// Transparency/alpha setting.
	ETransparencyMode GetTransparencyMode() const;
	void SetTransparencyMode(ETransparencyMode mode);

	// Load movie from local filesystem, either pass a absolute path or relative 
	// one to GetCurrentDirectory(), return true/false to signal success. Note: 
	// the movie will automatically start playing if it was successfully loaded.
	bool LoadMovie(const wchar_t* movie);

	// Load movie from url, returns true/false to signal success. Note: the movie will
	// automatically start playing if it was successfully loaded.
	bool LoadURL(const wchar_t* url);

	// Returns Flash movie background color (only works in OPAQUE mode).
	COLORREF GetBackgroundColor();

	// Set Flash movie background color (only works in OPAQUE mode).
	void SetBackgroundColor(COLORREF color);

	// Manual playback control interface.
	void StartPlaying();
	void StopPlaying();
	void Rewind();
	void StepForward();
	void StepBack();
	int GetCurrentFrame();
	void GotoFrame(int frame);

	// Resize player rendering surface dimensions, should always match 
	// the HDC of the DrawFrame() call.
	void ResizePlayer(unsigned int newWidth, unsigned int newHeight);

	// Check if player wants to update the target surface. We will attempt to optimize 
	// the rendering by maintaining a list of the RECT areas that need to be updated. 
	// Overlapping RECT's are unioned together to form the smallest possible list to 
	// make sure we don't draw stuff twice. Pass pointers to `dirtyRects` and `numDirtyRects` 
	// to access the current list, if you want a single a RECT where all `dirtyRects` 
	// are collapsed into a single union pass a pointer to `unitedDirtyRect` instead.
	bool IsNeedUpdate(const RECT** unitedDirtyRect = NULL, const RECT** dirtyRects = NULL, unsigned int* numDirtyRects = NULL);

	// Render Flash movie frame to target surface.
	void DrawFrame(HDC dc);

	// Interact the Flash movie mouse cursor (doesn't affect the system cursor).
	void SetMousePos(unsigned int x, unsigned int y);
	void SetMouseButtonState(unsigned int x, unsigned int y, EMouseButton button, bool pressed);
	void SendMouseWheel(int delta);

	// Forward keyboard events to the Flash movie, SendKey() should pass both the 
	// virtual key and extended data for the WM_KEYUP/WM_KEYDOWN messages, SendChar() 
	// should send the character and extended data for the WM_CHAR message.
	void SendKey(bool pressed, UINT_PTR virtualKey, LONG_PTR extended);
	void SendChar(UINT_PTR character, LONG_PTR extended);

	// Call AS3 using the ExternalInteface API XML format, returns NULL if failed 
	// or the XML response as a string.
	const wchar_t* CallFunction(const wchar_t* request);

	// Set the response for C++ callback initiated by a AS3 script via ExternalInterface.call(). 
	// NOTE: This method should should only be called from FlashCall() or IFlashEventHandler.
	void SetReturnValue(const wchar_t* returnValue);

	// Add/remote/list player event handlers.
	void AddEventHandler(IFlashEventHandler* pHandler);
	void RemoveEventHandler(IFlashEventHandler* pHandler);
	IFlashEventHandler* GetEventHandlerByIndex(unsigned int index);
	unsigned int GetNumEventHandlers() const;

protected:
	// Re-create the WPARAM for a mouse message intended to be forwarded to the player.
	WPARAM CreateMouseWParam(WPARAM highWord);
	
	// Attempt to optimize list dirty of rects by combining intersectings ones, 
	// returns true if list was optimized  or false if no rects were unioned.
	bool ReduceNumDirtyRects();

	unsigned int					m_width;
	unsigned int					m_height;
	ETransparencyMode				m_transpMode;

	ShockwaveFlashObjects::IShockwaveFlash* 
		m_flashInterface;

protected:
	FlashControlSite				m_controlSite;
	FlashSink						m_flashSink;
	IOleObject*						m_oleObject;
	IOleInPlaceObjectWindowless*	m_windowlessObject;

	RECT							m_dirtyUnionRect;
	std::vector<RECT>				m_dirtyRects;
	bool							m_dirtyFlag;

	RECT							m_savedUnionRect;
	std::vector<RECT>				m_savedDirtyRects;

	unsigned int					m_lastMouseX;
	unsigned int					m_lastMouseY;
	intptr_t						m_lastMouseButtons;

	std::wstring					m_invokeString;
	std::wstring					m_tempStorage;

	std::vector<IFlashEventHandler*> m_eventHandlers;

	HDC								m_alphaBlackDC;
	HBITMAP							m_alphaBlackBitmap;
	BYTE*							m_alphaBlackBuffer;
	HDC								m_alphaWhiteDC;
	HBITMAP							m_alphaWhiteBitmap;
	BYTE*							m_alphaWhiteBuffer;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_FLASH_PLAYER_H