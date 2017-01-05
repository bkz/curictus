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

#ifndef CURICTUS_FLASH_CONTROLSITE_H
#define CURICTUS_FLASH_CONTROLSITE_H

#include "Flash.h"

class FlashControlSite : public IOleInPlaceSiteWindowless, public IOleClientSite	
{
protected:
	FlashPlayer*	m_flashPlayer;
	ULONG			m_refs;

public:
	FlashControlSite();	
	virtual ~FlashControlSite();

	void Init(FlashPlayer* flashPlayer);

	HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, LPVOID* ppv);
	ULONG STDMETHODCALLTYPE AddRef();
	ULONG STDMETHODCALLTYPE Release();

	HRESULT STDMETHODCALLTYPE SaveObject();
	HRESULT STDMETHODCALLTYPE GetMoniker(DWORD dwAssign, DWORD dwWhichMoniker, IMoniker** ppmk);
	HRESULT STDMETHODCALLTYPE GetContainer(IOleContainer ** theContainerP);
	HRESULT STDMETHODCALLTYPE ShowObject();
	HRESULT STDMETHODCALLTYPE OnShowWindow(BOOL);
	HRESULT STDMETHODCALLTYPE RequestNewObjectLayout();

	HRESULT STDMETHODCALLTYPE ContextSensitiveHelp(/* [in] */ BOOL fEnterMode);
	HRESULT STDMETHODCALLTYPE GetWindow(/* [out] */ HWND __RPC_FAR* theWnndow);
	HRESULT STDMETHODCALLTYPE CanInPlaceActivate();
	HRESULT STDMETHODCALLTYPE OnInPlaceActivate();
	HRESULT STDMETHODCALLTYPE OnUIActivate();

	HRESULT STDMETHODCALLTYPE GetWindowContext(/* [out] */ IOleInPlaceFrame __RPC_FAR *__RPC_FAR *ppFrame,
											   /* [out] */ IOleInPlaceUIWindow __RPC_FAR *__RPC_FAR *ppDoc,
											   /* [out] */ LPRECT lprcPosRect,
											   /* [out] */ LPRECT lprcClipRect,
											   /* [out][in] */ LPOLEINPLACEFRAMEINFO lpFrameInfo);

	HRESULT STDMETHODCALLTYPE Scroll(/* [in] */ SIZE scrollExtant);
	HRESULT STDMETHODCALLTYPE OnUIDeactivate(/* [in] */ BOOL fUndoable);
	HRESULT STDMETHODCALLTYPE OnInPlaceDeactivate();
	HRESULT STDMETHODCALLTYPE DiscardUndoState();
	HRESULT STDMETHODCALLTYPE DeactivateAndUndo();
	HRESULT STDMETHODCALLTYPE OnPosRectChange(/* [in] */ LPCRECT lprcPosRect);
	HRESULT STDMETHODCALLTYPE OnInPlaceActivateEx(/* [out] */ BOOL __RPC_FAR *pfNoRedraw, /* [in] */ DWORD dwFlags);
	HRESULT STDMETHODCALLTYPE OnInPlaceDeactivateEx(/* [in] */ BOOL fNoRedraw);
	HRESULT STDMETHODCALLTYPE RequestUIActivate();
	HRESULT STDMETHODCALLTYPE CanWindowlessActivate();
	HRESULT STDMETHODCALLTYPE GetCapture();
	HRESULT STDMETHODCALLTYPE SetCapture(/* [in] */ BOOL fCapture);
	HRESULT STDMETHODCALLTYPE GetFocus();
	HRESULT STDMETHODCALLTYPE SetFocus(/* [in] */ BOOL fFocus);
	HRESULT STDMETHODCALLTYPE GetDC(/* [in] */ LPCRECT pRect, /* [in] */ DWORD grfFlags, /* [out] */ HDC __RPC_FAR *phDC);
	HRESULT STDMETHODCALLTYPE ReleaseDC(/* [in] */ HDC hDC);
	HRESULT STDMETHODCALLTYPE InvalidateRect(/* [in] */ LPCRECT pRect, /* [in] */ BOOL fErase);
	HRESULT STDMETHODCALLTYPE InvalidateRgn(/* [in] */ HRGN hRGN, /* [in] */ BOOL fErase);
	HRESULT STDMETHODCALLTYPE ScrollRect(/* [in] */ INT dx, /* [in] */ INT dy, /* [in] */ LPCRECT pRectScroll, /* [in] */ LPCRECT pRectClip);
	HRESULT STDMETHODCALLTYPE AdjustRect(/* [out][in] */ LPRECT prc);
	HRESULT STDMETHODCALLTYPE OnDefWindowMessage(/* [in] */ UINT msg, /* [in] */ WPARAM wParam, /* [in] */ LPARAM lParam, /* [out] */ LRESULT __RPC_FAR *plResult);
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_FLASH_CONTROLSITE_H