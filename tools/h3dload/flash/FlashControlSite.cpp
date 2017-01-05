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

#include "FlashControlSite.h"
#include "FlashPlayer.h"
#include <assert.h>

///////////////////////////////////////////////////////////////////////////////////////////////////
// Flash control site implementation.
///////////////////////////////////////////////////////////////////////////////////////////////////

FlashControlSite::FlashControlSite()
{
	m_flashPlayer = NULL;
	m_refs = 0;
}

FlashControlSite::~FlashControlSite()
{
	assert(m_refs == 0);
}

void FlashControlSite::Init(FlashPlayer* flashPlayer)
{
	m_flashPlayer = flashPlayer;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::QueryInterface(REFIID riid, LPVOID* ppv)
{
	*ppv = NULL;

	if (riid == IID_IUnknown)
	{
		*ppv = (IUnknown*) (IOleWindow*) this;
		AddRef();
		return S_OK;
	}
	else if (riid == IID_IOleWindow)
	{
		*ppv = (IOleWindow*)this;
		AddRef();
		return S_OK;
	}
	else if (riid == IID_IOleInPlaceSite)
	{
		*ppv = (IOleInPlaceSite*)this;
		AddRef();
		return S_OK;
	}
	else if (riid == IID_IOleInPlaceSiteEx)
	{
		*ppv = (IOleInPlaceSiteEx*)this;
		AddRef();
		return S_OK;
	}
	else if (riid == IID_IOleInPlaceSiteWindowless)
	{
		*ppv = (IOleInPlaceSiteWindowless*)this;
		AddRef();
		return S_OK;
	}
	else if (riid == IID_IOleClientSite)
	{
		*ppv = (IOleClientSite*)this;
		AddRef();
		return S_OK;
	}
	else if (riid == __uuidof(ShockwaveFlashObjects::_IShockwaveFlashEvents))
	{
		*ppv = (ShockwaveFlashObjects::_IShockwaveFlashEvents*) this;
		AddRef();
		return S_OK;
	}
	else
	{   
		return E_NOTIMPL;
	}
}

ULONG STDMETHODCALLTYPE FlashControlSite::AddRef()
{
	return ++m_refs;
}

ULONG STDMETHODCALLTYPE FlashControlSite::Release()
{
	return --m_refs;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::SaveObject()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetMoniker(DWORD dwAssign, DWORD dwWhichMoniker, IMoniker** ppmk)
{
	*ppmk = NULL;
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetContainer(IOleContainer ** theContainerP)
{
	return E_NOINTERFACE;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::ShowObject()
{
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnShowWindow(BOOL)
{
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::RequestNewObjectLayout()
{
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::ContextSensitiveHelp(/* [in] */ BOOL fEnterMode)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetWindow(/* [out] */ HWND __RPC_FAR* theWnndow)
{
	return E_FAIL;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::CanInPlaceActivate()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnInPlaceActivate()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnUIActivate()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetWindowContext(/* [out] */ IOleInPlaceFrame __RPC_FAR *__RPC_FAR *ppFrame,
														 /* [out] */ IOleInPlaceUIWindow __RPC_FAR *__RPC_FAR *ppDoc,
														 /* [out] */ LPRECT lprcPosRect,
														 /* [out] */ LPRECT lprcClipRect,
														 /* [out][in] */ LPOLEINPLACEFRAMEINFO lpFrameInfo)
{
	RECT rect = { 0, 0, m_flashPlayer->m_width, m_flashPlayer->m_height };

	*lprcPosRect = rect;
	*lprcClipRect = rect;

	*ppFrame = NULL;
	QueryInterface(__uuidof(IOleInPlaceFrame), (void**) ppFrame);		
	*ppDoc = NULL;

	lpFrameInfo->fMDIApp = FALSE;
	lpFrameInfo->hwndFrame = NULL;
	lpFrameInfo->haccel = NULL;
	lpFrameInfo->cAccelEntries = 0;

	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::Scroll(/* [in] */ SIZE scrollExtant)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnUIDeactivate(/* [in] */ BOOL fUndoable)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnInPlaceDeactivate()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::DiscardUndoState()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::DeactivateAndUndo()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnPosRectChange(/* [in] */ LPCRECT lprcPosRect)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnInPlaceActivateEx(/* [out] */ BOOL __RPC_FAR *pfNoRedraw, /* [in] */ DWORD dwFlags)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnInPlaceDeactivateEx(/* [in] */ BOOL fNoRedraw)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::RequestUIActivate()
{
	return S_FALSE;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::CanWindowlessActivate()
{
	// Allow windowless activation?
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetCapture()
{
	// TODO capture the mouse for the object
	return S_FALSE;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::SetCapture(/* [in] */ BOOL fCapture)
{
	// TODO capture the mouse for the object
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetFocus()
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::SetFocus(/* [in] */ BOOL fFocus)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::GetDC(/* [in] */ LPCRECT pRect, /* [in] */ DWORD grfFlags, /* [out] */ HDC __RPC_FAR *phDC)
{
	return E_INVALIDARG;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::ReleaseDC(/* [in] */ HDC hDC)
{
	return E_INVALIDARG;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::InvalidateRect(/* [in] */ LPCRECT pRect, /* [in] */ BOOL fErase)
{
	m_flashPlayer->AddDirtyRect(pRect);

	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::InvalidateRgn(/* [in] */ HRGN hRGN, /* [in] */ BOOL fErase)
{
	m_flashPlayer->AddDirtyRect(NULL);

	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::ScrollRect(/* [in] */ INT dx, /* [in] */ INT dy, /* [in] */ LPCRECT pRectScroll, /* [in] */ LPCRECT pRectClip)
{
	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::AdjustRect(/* [out][in] */ LPRECT prc)
{
	if (prc == NULL)
	{
		return E_INVALIDARG;
	}

	return S_OK;
}

HRESULT STDMETHODCALLTYPE FlashControlSite::OnDefWindowMessage(/* [in] */ UINT msg, /* [in] */ WPARAM wParam, /* [in] */ LPARAM lParam, /* [out] */ LRESULT __RPC_FAR *plResult)
{
	return S_FALSE;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
