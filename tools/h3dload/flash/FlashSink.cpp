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

#include "FlashSink.h"
#include "FlashPlayer.h"

///////////////////////////////////////////////////////////////////////////////////////////////////
// Flash event sink implementation.
///////////////////////////////////////////////////////////////////////////////////////////////////

FlashSink::FlashSink()
{
	m_cookie = 0;
	m_connectionPoint = NULL;
	m_refs = 0;
	m_flashPlayer = NULL;
}

FlashSink::~FlashSink()
{
}

HRESULT FlashSink::Init(FlashPlayer* flashPlayer)
{
	m_flashPlayer = flashPlayer;

	HRESULT hr = NOERROR;
	LPCONNECTIONPOINTCONTAINER pConnectionPoint = NULL;

	if ((m_flashPlayer->m_flashInterface->QueryInterface(IID_IConnectionPointContainer, (void**) &pConnectionPoint) == S_OK) &&
		(pConnectionPoint->FindConnectionPoint(__uuidof(ShockwaveFlashObjects::_IShockwaveFlashEvents), &m_connectionPoint) == S_OK))			
	{
		IDispatch* pDispatch = NULL;
		QueryInterface(__uuidof(IDispatch), (void**) &pDispatch);
		if (pDispatch != NULL)
		{
			hr = m_connectionPoint->Advise((LPUNKNOWN)pDispatch, &m_cookie);
			pDispatch->Release();
		}
	}

	if (pConnectionPoint != NULL) 
		pConnectionPoint->Release();

	return hr;
}

HRESULT FlashSink::Shutdown()
{
	HRESULT aResult = S_OK;

	if (m_connectionPoint)
	{
		if (m_cookie)
		{
			aResult = m_connectionPoint->Unadvise(m_cookie);
			m_cookie = 0;
		}

		m_connectionPoint->Release();
		m_connectionPoint = NULL;
	}

	return aResult;
}

HRESULT STDMETHODCALLTYPE FlashSink::QueryInterface(REFIID riid, LPVOID* ppv)
{
	*ppv = NULL;

	if (riid == IID_IUnknown)
	{
		*ppv = (LPUNKNOWN)this;
		AddRef();
		return S_OK;
	}
	else if (riid == IID_IDispatch)
	{
		*ppv = (IDispatch*)this;
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

ULONG STDMETHODCALLTYPE FlashSink::AddRef()
{
	return ++m_refs;
}

ULONG STDMETHODCALLTYPE FlashSink::Release()
{
	return --m_refs;
}

HRESULT STDMETHODCALLTYPE FlashSink::GetTypeInfoCount(UINT* pctinfo)
{
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashSink::GetTypeInfo(UINT iTInfo, LCID lcid, ITypeInfo** ppTInfo)
{
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashSink::GetIDsOfNames(REFIID riid, LPOLESTR* rgszNames, UINT cNames, LCID lcid,DISPID* rgDispId)
{
	return E_NOTIMPL;
}

HRESULT STDMETHODCALLTYPE FlashSink::Invoke(DISPID dispIdMember, REFIID riid, LCID lcid, WORD wFlags, ::DISPPARAMS __RPC_FAR *pDispParams, VARIANT __RPC_FAR *pVarResult, ::EXCEPINFO __RPC_FAR *pExcepInfo, UINT __RPC_FAR *puArgErr)
{
	switch (dispIdMember)
	{
	case 0xc5: // FlashCall
		if (pDispParams->cArgs != 1 || pDispParams->rgvarg[0].vt != VT_BSTR) 
			return E_INVALIDARG;
		return m_flashPlayer->FlashCall(pDispParams->rgvarg[0].bstrVal);
	case 0x96: // FSCommand
		if (pDispParams->cArgs != 2 || pDispParams->rgvarg[0].vt != VT_BSTR || pDispParams->rgvarg[1].vt != VT_BSTR) 
			return E_INVALIDARG;
		return m_flashPlayer->FSCommand(pDispParams->rgvarg[1].bstrVal, pDispParams->rgvarg[0].bstrVal);
	case 0x7a6: // OnProgress
		return E_NOTIMPL;
	case DISPID_READYSTATECHANGE:
		return E_NOTIMPL;
	}

	return DISP_E_MEMBERNOTFOUND;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
