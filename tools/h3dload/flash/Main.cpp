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

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "Flash.h"
#include "FlashPlayer.h"
#include "Profile.h"

const UINT_PTR RENDER_TIMER  = 0;

static HDC				g_hDC			= NULL;
static HDC				g_hMemDC		= NULL;
static HBITMAP			g_hBitmap		= NULL;
static int				g_mousex		= 0;
static int				g_mousey		= 0;
static int				g_lastmousex	= 0;
static int				g_lastmousey	= 0;
static bool             g_mirror		= false;
static Flash*			g_flash			= NULL;
static FlashPlayer*		g_flashPlayer	= NULL;

#ifndef GET_X_LPARAM
#define GET_X_LPARAM(lp)	((int)(short)LOWORD(lp))
#endif
#ifndef GET_Y_LPARAM
#define GET_Y_LPARAM(lp)	((int)(short)HIWORD(lp))
#endif

#pragma comment(linker, "/ENTRY:wWinMainCRTStartup")
#pragma comment(linker, "/SUBSYSTEM:CONSOLE")

void FreeBuffers(HWND hWnd)
{
	if (g_hBitmap)
	{
		::DeleteObject(g_hBitmap);
		g_hBitmap = NULL;
	}

	if (g_hMemDC)
	{
		::DeleteDC(g_hMemDC);
		g_hMemDC = NULL;
	}

	if (g_hDC)
	{
		::ReleaseDC(hWnd, g_hDC);
		g_hDC = NULL;
	}

}

void ResizeBuffers(HWND hWnd, int width, int height)
{
	FreeBuffers(hWnd);
	
	g_hDC	  = ::GetDC(hWnd);
	g_hMemDC  = ::CreateCompatibleDC(g_hDC);		
	g_hBitmap = ::CreateCompatibleBitmap(g_hDC, width,height);	
	
	::SelectObject(g_hMemDC, g_hBitmap);
}

void RenderFrame(HWND hWnd)
{
	unsigned int numDirtyRects = 0;
	const RECT* dirtyRects = NULL;

	if (g_lastmousex != g_mousex || g_lastmousey != g_mousey)
	{
		RECT rect = {g_lastmousex-5, g_lastmousey-5,g_lastmousex+5, g_lastmousey+5};
		g_flashPlayer->AddDirtyRect(&rect);
	}

	if (g_flashPlayer->IsNeedUpdate(NULL, &dirtyRects, &numDirtyRects))
	{
		g_flashPlayer->DrawFrame(g_hMemDC);

		if (g_mirror)
		{
			RECT rect = {0};		
			
			::GetWindowRect(hWnd, &rect);
			
			int width = rect.right - rect.left;

			for (unsigned int i = 0; i < numDirtyRects; i++)
			{									
				::StretchBlt( 
					g_hDC, 
					width-dirtyRects[i].right, dirtyRects[i].top, dirtyRects[i].right-dirtyRects[i].left, dirtyRects[i].bottom-dirtyRects[i].top, 
					g_hMemDC,
					dirtyRects[i].right-1, dirtyRects[i].top, -(dirtyRects[i].right-dirtyRects[i].left), dirtyRects[i].bottom-dirtyRects[i].top, 
					SRCCOPY);
			}

			::Rectangle(g_hDC, width-g_mousex-5, g_mousey-5, width-g_mousex+5, g_mousey+5);
		}
		else
		{
			for (unsigned int i = 0; i < numDirtyRects; i++)
			{
				::BitBlt(g_hDC, 
					dirtyRects[i].left, 
					dirtyRects[i].top, 
					dirtyRects[i].right,
					dirtyRects[i].bottom, 
					g_hMemDC, 
					dirtyRects[i].left, dirtyRects[i].top, 
					SRCCOPY);
			}

			::Rectangle(g_hDC, g_mousex-5, g_mousey-5, g_mousex+5, g_mousey+5);
		}
	}

	g_lastmousex = g_mousex;
	g_lastmousey = g_mousey;
}

static LRESULT CALLBACK WndProc(HWND hWnd, UINT uMessage, WPARAM wParam, LPARAM lParam)
{
	switch(uMessage)
	{
	case WM_TIMER:
		RenderFrame(hWnd);
		return 0;
	case WM_PAINT:
		::ValidateRect(hWnd, NULL);
		return 0;
	case WM_DESTROY:
		FreeBuffers(hWnd);
		PostQuitMessage(0);
		return 0;
	case WM_MOUSEWHEEL:
		if (g_flashPlayer)
			g_flashPlayer->SendMouseWheel(HIWORD(wParam));
		return 0;
	case WM_MOUSEMOVE:
		if (g_flashPlayer)
		{			
			if (abs(GET_X_LPARAM(lParam) - g_mousex) > 2 || abs(GET_Y_LPARAM(lParam) - g_mousey) > 2)
			{
				g_mousex = GET_X_LPARAM(lParam);
				g_mousey = GET_Y_LPARAM(lParam);
				g_flashPlayer->SetMousePos(g_mousex, g_mousey);
			}
		}
		return 0;
	case WM_LBUTTONDOWN:
		if (g_flashPlayer)
			g_flashPlayer->SetMouseButtonState(GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam), FlashPlayer::eMouse1, true);
		return 0;
	case WM_LBUTTONUP:
		if (g_flashPlayer)
			g_flashPlayer->SetMouseButtonState(GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam), FlashPlayer::eMouse1, false);
		return 0;
	case WM_KEYDOWN:
		if (g_flashPlayer)
		{
			if (wParam == VK_F1) g_mirror = !g_mirror;
			g_flashPlayer->AddDirtyRect(NULL);
			g_flashPlayer->SendKey(true, wParam, lParam);
		}
		return 0;
	case WM_KEYUP:
		if (g_flashPlayer)
			g_flashPlayer->SendKey(false, wParam, lParam);
		return 0;
	case WM_CHAR:
		if (g_flashPlayer)
			g_flashPlayer->SendChar(wParam, lParam);
		return 0;
	case WM_SIZE:
		if (g_flashPlayer)
		{
			int width  = GET_X_LPARAM(lParam);
			int height = GET_Y_LPARAM(lParam);
			g_flashPlayer->ResizePlayer(width, height);
			ResizeBuffers(hWnd, width, height);
		}
		return 0;
	}

	return DefWindowProc(hWnd, uMessage, wParam, lParam);
}

bool IsRotatedScreen180()
{
	DEVMODE DeviceMode = { 0 };
	
	::EnumDisplaySettings( NULL, ENUM_CURRENT_SETTINGS,	&DeviceMode );

	return (DeviceMode.dmDisplayOrientation == DMDO_180);
}

void RotateScreen180(bool enable)
{	
	DEVMODE DeviceMode = { 0 };
	
	::EnumDisplaySettings( NULL, ENUM_CURRENT_SETTINGS,	&DeviceMode );

	if (enable)
	{	
		DeviceMode.dmDisplayOrientation = DMDO_180;
	}	
	else
	{	
		DeviceMode.dmDisplayOrientation = DMDO_DEFAULT;
	}	

	::ChangeDisplaySettings( &DeviceMode, 0 );	
}

int APIENTRY wWinMain(HINSTANCE hInstance, HINSTANCE hPrev, LPWSTR pwszCmdLine, int nCmdShow)
{
	const wchar_t* pwszClassName = L"Curictus Dashboard";
	const wchar_t* pwszTitleName = L"Curictus Dashboard Demo";

	WNDCLASSEX wc = {0};
    wc.cbSize        = sizeof(WNDCLASSEX);
    wc.style         = 0;
    wc.lpfnWndProc   = WndProc;
    wc.cbClsExtra    = 0;
    wc.cbWndExtra    = 0;
    wc.hInstance     = hInstance;
	wc.hIcon         = ::LoadIcon(NULL, IDI_APPLICATION);
    wc.hCursor       = ::LoadCursor(NULL, IDC_ARROW);
	wc.hbrBackground = static_cast<HBRUSH>(::GetStockObject(WHITE_BRUSH));
    wc.lpszMenuName  = NULL;
    wc.lpszClassName = pwszClassName;
    wc.hIconSm       = ::LoadIcon(NULL, IDI_APPLICATION);

	if (!::RegisterClassEx(&wc))
	{
		return ::MessageBox(HWND_DESKTOP, L"Could not register window class!", L"Error", MB_ICONERROR | MB_OK);
	}

	const int WINDOW_WIDTH  = 1680; 
	const int WINDOW_HEIGHT = 1050;

	const int nX = ((::GetSystemMetrics(SM_CXSCREEN) - WINDOW_WIDTH)  / 2);
	const int nY = ((::GetSystemMetrics(SM_CYSCREEN) - WINDOW_HEIGHT) / 2);
	
	HWND hWnd = ::CreateWindowEx(
		0, 
		pwszClassName, 
		pwszTitleName,
		WS_POPUP, 
		nX , 
		nY, 
		WINDOW_WIDTH, 
		WINDOW_HEIGHT, 
		HWND_DESKTOP, 
		NULL, 
		hInstance, 
		NULL);
	
	if(!hWnd)
	{
		return ::MessageBox(HWND_DESKTOP, L"Could not create window!", L"Error", MB_ICONERROR | MB_OK);
	}

	::ShowWindow(hWnd, nCmdShow);

	g_flash = Flash::GetInstance();
	printf("Flash player version = %2.2lf\n", g_flash->GetFlashVersion());
	g_flashPlayer = g_flash->CreatePlayer(WINDOW_WIDTH, WINDOW_HEIGHT);
	g_flashPlayer->LoadMovie(L"data\\pcms.swf");
	g_flashPlayer->SetQuality(FlashPlayer::QUALITY_AUTOHIGH);
	ResizeBuffers(hWnd, WINDOW_WIDTH, WINDOW_HEIGHT);

	MSG msg;

	::SetTimer(hWnd, RENDER_TIMER, 15, NULL);

	while (::GetMessage(&msg, NULL, 0, 0))
	{
		::TranslateMessage(&msg);
		::DispatchMessage(&msg);
	}

	return 0;
}
