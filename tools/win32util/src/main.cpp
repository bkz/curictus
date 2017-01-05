//////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2006-2011 Curictus AB.
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////////

#include <windows.h>
#include <process.h>
#include <gdiplus.h>
#include <sddl.h>

#include <shlguid.h>
#include <shobjidl.h>
#include <atlbase.h>
#include <wininet.h>
#include <shlobj.h>

#include <string>
#include <math.h>

#include "AutoLock.h"

///////////////////////////////////////////////////////////////////////////////////////////////////
// Global data.
///////////////////////////////////////////////////////////////////////////////////////////////////

HWND				  g_hMainWnd		  = NULL;
HANDLE				  g_hThreadHandle	  = NULL;

bool				  g_mirrorOutput	  = false;
std::wstring		  g_progressImagePath = L"";
std::wstring          g_logoImagePath     = L"";
std::wstring          g_progressMessage   = L"";
std::wstring          g_versionInfo       = L"";

LockCS                g_textCS;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Helpers.
///////////////////////////////////////////////////////////////////////////////////////////////////

const char* GetBusTypeStringID(STORAGE_BUS_TYPE type)
{
	if (type == BusTypeScsi)
		return "BusTypeScsi";

	if (type == BusTypeAtapi)
		return "BusTypeAtapi";

	if (type == BusTypeAta)
		return "BusTypeAta";

	if (type == BusType1394)
		return "BusType1394";

	if (type == BusTypeSsa)
		return "BusTypeSsa";

	if (type == BusTypeFibre)
		return "BusTypeFibre";

	if (type == BusTypeUsb)
		return "BusTypeUsb";

	if (type == BusTypeRAID)
		return "BusTypeRAID";

	if (type == BusTypeiScsi)
		return "BusTypeiScsi";

	if (type == BusTypeSas)
		return "BusTypeSas";

	if (type == BusTypeSata)
		return "BusTypeSata";

	if (type == BusTypeSd)
		return "BusTypeSd";

	if (type == BusTypeMmc)
		return "BusTypeMmc";

	return "BusTypeUnknown";
}

bool InitializeWithDefaultAccess(SECURITY_ATTRIBUTES& sa, SECURITY_DESCRIPTOR& sd)
{
	//
	// Default to all access for all users (i.e group = everyone).
	//

	if (!::InitializeSecurityDescriptor(&sd, SECURITY_DESCRIPTOR_REVISION))
	{
		return false;
	}

	if (!::SetSecurityDescriptorDacl(&sd, TRUE, NULL, FALSE))
	{
		return false;
	}

	if (!::SetSecurityDescriptorGroup(&sd, NULL, FALSE))
	{
		return false;
	}

	if (!::SetSecurityDescriptorSacl(&sd, FALSE, NULL, FALSE))
	{
		return false;
	}

	sa.nLength = sizeof(SECURITY_ATTRIBUTES);
	sa.lpSecurityDescriptor = &sd;
	sa.bInheritHandle = TRUE;

	return true;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Hide all other windows.
///////////////////////////////////////////////////////////////////////////////////////////////////

BOOL IsVisibleAppWindow(HWND hWnd)
{
	if (!::IsWindowVisible(hWnd))
	{
		return FALSE;
	}

	if (::IsIconic(hWnd))
	{
		return FALSE;
	}

	HWND hParentWnd = (HWND)::GetWindowLong(hWnd, GWL_HWNDPARENT);

	if (hParentWnd != HWND_DESKTOP || hParentWnd == ::GetDesktopWindow())
	{
		return FALSE;
	}

	wchar_t pwszClassName[256] = {0};

	if (::GetClassName(hWnd, pwszClassName, _countof(pwszClassName)))
	{
		wchar_t* ppwszExcludeWindowClasses[] = { L"progman", L"shell_traywnd" };

		for (int i = 0; i < _countof(ppwszExcludeWindowClasses); i++)
		{
			if (0 == _wcsicmp(pwszClassName, ppwszExcludeWindowClasses[i]))
			{
				return FALSE;
			}
		}
	}
	else
	{
		return FALSE;
	}

	wchar_t pwszWindowTitle[1024] = {0};

	if (!::GetWindowText(hWnd, pwszWindowTitle, _countof(pwszWindowTitle)))
	{
		return FALSE;
	}

	return TRUE;
}

BOOL CALLBACK HideWindowsProc(HWND hWnd, LPARAM lParam)
{
	if (IsVisibleAppWindow(hWnd))
	{
		::ShowWindow(hWnd, SW_MINIMIZE);
	}

	return TRUE;
}

void MinimizeAllWindows()
{
	::EnumDesktopWindows(NULL, HideWindowsProc, NULL);
}


///////////////////////////////////////////////////////////////////////////////////////////////////
// Rotate display support.
///////////////////////////////////////////////////////////////////////////////////////////////////

// NOTE: We only want to rotate the display if it's already been flipped, i.e. we want to 
// restore the standard landscape layout. In the VRS station the screen is mounted upside 
// down but in order to be able to use it directly without the mirror we flip the desktop 
// in Windows. Thus when we are running the VRS software we'll want to rotate it back the 
// original position in order to use the mirror and co-location features.

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

///////////////////////////////////////////////////////////////////////////////////////////////////
// Progress/status window rendering.
///////////////////////////////////////////////////////////////////////////////////////////////////

HFONT				g_hBigFont			= NULL;
HFONT				g_hSmallFont		= NULL;
Gdiplus::Bitmap*	g_pProgressIcon		= NULL;
Gdiplus::Bitmap*	g_pMainLogoIcon		= NULL;

void DrawVersionString(HDC hdc, const wchar_t* msg, RECT& rect)
{
	::SelectObject(hdc, g_hSmallFont);
	::SetTextColor(hdc, RGB(200,200,200));
    ::SetBkMode(hdc, TRANSPARENT);	
	
	RECT r = rect;
	r.top = rect.bottom - 25;
	r.right -= 25;
	::DrawTextW(hdc, msg, -1, &r, DT_SINGLELINE | DT_RIGHT);
}

void DrawStatusString(HDC hdc, const wchar_t* msg, RECT& rect)
{
	::SelectObject(hdc, g_hBigFont);
	::SetTextColor(hdc, RGB(240, 240, 240));
    ::SetBkMode(hdc, TRANSPARENT);	
	
	RECT r = rect;
	r.top = 8.5f * rect.bottom / 10;
	
	::DrawTextW(hdc, msg, -1, &r, DT_SINGLELINE | DT_CENTER | DT_VCENTER);
}

void DrawLogoImage(HDC hdc, RECT &rect)
{
	Gdiplus::Graphics backbuf(hdc);
	backbuf.DrawImage(g_pMainLogoIcon, int(rect.right - g_pMainLogoIcon->GetWidth()) / 2, int(rect.bottom - g_pMainLogoIcon->GetHeight()) / 2);
}

void DrawProgressIcon(HDC hdc, RECT& rect)
{
	static int angle=0;
	
	angle += 30;

	Gdiplus::Bitmap rotatedBitmap(g_pProgressIcon->GetWidth(), g_pProgressIcon->GetHeight());

	float centerX = static_cast<float>(g_pProgressIcon->GetWidth())  / 2;
	float centerY = static_cast<float>(g_pProgressIcon->GetHeight()) / 2;

	{
		Gdiplus::Graphics g(&rotatedBitmap);
		g.ResetTransform();
		g.TranslateTransform(centerX, centerY);
		g.RotateTransform(angle);
		g.TranslateTransform(-centerX, -centerY);
		g.DrawImage(g_pProgressIcon, 0, 0, g_pProgressIcon->GetWidth(), g_pProgressIcon->GetHeight()); 
	}

	Gdiplus::Graphics backbuf(hdc);
	backbuf.DrawImage(&rotatedBitmap, (rect.right - g_pProgressIcon->GetWidth()) / 2, 7.5f * rect.bottom / 10);
}

void ClearScreen(HDC hdc, RECT& rect)
{
	::FillRect(hdc, &rect, static_cast<HBRUSH>(::GetStockObject(BLACK_BRUSH)));
}

void RenderScreen(HWND hWnd, HDC hdc, RECT& rect)
{
	ClearScreen(hdc, rect);
	
	DrawLogoImage(hdc, rect);
	DrawProgressIcon(hdc, rect);
	
	{
		AutoLockCS lock(&g_textCS);
		DrawVersionString(hdc, g_versionInfo.c_str(), rect);
		DrawStatusString(hdc, g_progressMessage.c_str(), rect);
	}
}

void SwapBackBuffer(HWND hWnd, HDC hDC, RECT& rect)
{
	HDC hdc = ::CreateCompatibleDC(hDC);

	HBITMAP hbuffer = ::CreateCompatibleBitmap(hDC, rect.right, rect.bottom);

	::SelectObject(hdc, hbuffer);

	RenderScreen(hWnd, hdc, rect);

	if (g_mirrorOutput)
	{
		Gdiplus::Bitmap backbuf(hbuffer, NULL);
		backbuf.RotateFlip(Gdiplus::RotateNoneFlipX);
		
		Gdiplus::Graphics screen(hDC);
		screen.DrawImage(&backbuf, 0, 0);
	}
	else
	{
		::BitBlt(hDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);
	}

	::DeleteObject(hbuffer);
	::DeleteDC(hdc);
}

bool InitApplication()
{
	g_hBigFont = ::CreateFont(48,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_OUTLINE_PRECIS,
		CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY, VARIABLE_PITCH,TEXT("Droid Sans"));

	g_hSmallFont = ::CreateFont(14,0,0,0,FW_NORMAL,FALSE,FALSE,FALSE,DEFAULT_CHARSET,OUT_OUTLINE_PRECIS,
		CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY, VARIABLE_PITCH,TEXT("Droid Sans"));

	ULONG_PTR gdiplusToken;
	Gdiplus::GdiplusStartupInput gdiplusStartupInput;

	if (Gdiplus::GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL) != Gdiplus::Ok)
	{
		return false;
	}

	g_pProgressIcon = Gdiplus::Bitmap::FromFile(g_progressImagePath.c_str());
	g_pMainLogoIcon = Gdiplus::Bitmap::FromFile(g_logoImagePath.c_str());

	return true;
}

void ExitApplication()
{
	if (g_hBigFont)
	{
		::DeleteObject(g_hBigFont);
		g_hBigFont = NULL;
	}

	if (g_hSmallFont)
	{
		::DeleteObject(g_hSmallFont);
		g_hSmallFont = NULL;
	}

	if (g_pMainLogoIcon)
	{
		delete g_pMainLogoIcon;
		g_pMainLogoIcon = NULL;
	}

	if (g_pProgressIcon)
	{
		delete g_pProgressIcon;
		g_pProgressIcon = NULL;
	}

	Gdiplus::GdiplusShutdown(NULL);
}

LRESULT CALLBACK WndProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
	enum { RENDER_TIMER_ID = 1 };

	switch(uMsg)
	{
		case WM_CREATE:
		{
			::SetTimer(hWnd, RENDER_TIMER_ID, 80, NULL);
			break;
		}
		case WM_CLOSE:
		{
			::DestroyWindow(hWnd);
			break;
		}
		case WM_PAINT:
		{
			RECT rect;
			PAINTSTRUCT ps;
			HDC hdc = ::BeginPaint(hWnd, &ps);
			::GetClientRect(hWnd, &rect);
			SwapBackBuffer(hWnd, hdc, rect);
			::EndPaint(hWnd, &ps);
			break;
		}
		case WM_TIMER:
		{
			RECT rect;
			::GetClientRect(hWnd, &rect);
			HDC hdc = ::GetDC(hWnd);
			SwapBackBuffer(hWnd, hdc, rect);
			::ReleaseDC(hWnd, hdc);
			break;
		}
		case WM_DESTROY:
		{
			::KillTimer(hWnd, RENDER_TIMER_ID);
			::PostQuitMessage(0);
			break;
		}
		default: 
			break;
	}

	return DefWindowProc(hWnd, uMsg, wParam, lParam);
}

unsigned __stdcall MainThreadProc(void* pParam)
{
	const wchar_t* pszWindowName = L"Curictus Status";
	const wchar_t* pszClassName  = L"6F09EA85-E88C-4e30-84DD-FC22A3065BBE";

	HINSTANCE hInstance = static_cast<HINSTANCE>(::GetModuleHandle(NULL));

	WNDCLASSEX wc;
	wc.cbSize		 = sizeof(WNDCLASSEX);
	wc.style		 = CS_VREDRAW | CS_HREDRAW;
	wc.lpfnWndProc	 = WndProc;
	wc.cbClsExtra	 = 0;
	wc.cbWndExtra	 = 0;
	wc.hInstance	 = hInstance;
	wc.hIcon		 = NULL;
	wc.hCursor		 = NULL;
	wc.hbrBackground = static_cast<HBRUSH>(::GetStockObject(BLACK_BRUSH));
	wc.lpszMenuName  = NULL;
	wc.lpszClassName = pszClassName;
	wc.hIconSm		 = ::LoadIcon(NULL, IDI_APPLICATION);

	if (!::RegisterClassEx(&wc))
	{
		return 0;
	}

	::ShowCursor(FALSE);

	g_hMainWnd = ::CreateWindowEx(
		WS_EX_TOPMOST,
		pszClassName,
		pszWindowName,
		WS_POPUP,
		0, 
		0, 
		::GetSystemMetrics(SM_CXSCREEN), 
		::GetSystemMetrics(SM_CYSCREEN),
		NULL, 
		NULL, 
		hInstance, 
		NULL);

	if (!g_hMainWnd)
	{
		return 0;
	}

	if (!InitApplication())
	{
		return 0;
	}

	::ShowWindow(g_hMainWnd, SW_SHOW);
	::UpdateWindow(g_hMainWnd);

	MSG msg;

	while (::GetMessage(&msg, NULL, 0, 0) > 0)
	{
		::TranslateMessage(&msg);
		::DispatchMessage(&msg);
	}

	ExitApplication();

	::UnregisterClass(pszClassName, hInstance);

	return msg.wParam;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Public API exposed to Python.
///////////////////////////////////////////////////////////////////////////////////////////////////

#define DLLEXPORT __declspec(dllexport) 

extern "C"
{
	DLLEXPORT int createshortcut(
		const wchar_t* source, 
		const wchar_t* destination,
		const wchar_t* working_dir, 
		const wchar_t* arguments,
		const wchar_t* description, 
		const wchar_t* icon,
		int icon_index) 
	{
		IShellLink*   pShellLink   = NULL;
		IPersistFile* pPersistFile = NULL;

		::CoInitialize(NULL);

		HRESULT hRet = ::CoCreateInstance(
			CLSID_ShellLink, 
			NULL,
			CLSCTX_INPROC_SERVER, 
			IID_IShellLink,
			reinterpret_cast<LPVOID*>(&pShellLink));

		if (FAILED(hRet))
		{
			return false;
		}

		hRet = pShellLink->QueryInterface(IID_IPersistFile,
			reinterpret_cast<LPVOID*>(&pPersistFile));
		
		if (FAILED(hRet)) 
		{
			pShellLink->Release();
			return false;
		}

		if (FAILED(pShellLink->SetPath(source))) 
		{
			pPersistFile->Release();
			pShellLink->Release();
			return false;
		}

		if (working_dir && FAILED(pShellLink->SetWorkingDirectory(working_dir))) 
		{
			pPersistFile->Release();
			pShellLink->Release();
			return false;
		}

		if (arguments && FAILED(pShellLink->SetArguments(arguments))) 
		{
			pPersistFile->Release();
			pShellLink->Release();
			return false;
		}

		if (description && FAILED(pShellLink->SetDescription(description))) 
		{
			pPersistFile->Release();
			pShellLink->Release();
			return false;
		}

		if (icon && FAILED(pShellLink->SetIconLocation(icon, icon_index))) 
		{
			pPersistFile->Release();
			pShellLink->Release();
			return false;
		}

		hRet = pPersistFile->Save(destination, TRUE);
		
		pPersistFile->Release();
		pShellLink->Release();
		
		return SUCCEEDED(hRet);
	}

	DLLEXPORT int setdesktopimage(const wchar_t* filepath)
	{
		HRESULT hr;

		IActiveDesktop *pActiveDesktop;

		::CoInitialize(NULL);

		hr = ::CoCreateInstance(
			CLSID_ActiveDesktop, 
			NULL, 
			CLSCTX_INPROC_SERVER, 
			IID_IActiveDesktop, 
			(void**)&pActiveDesktop);

		if (hr == S_OK)
		{ 
			WALLPAPEROPT wpo;			
			wpo.dwSize = sizeof(WALLPAPEROPT);
			wpo.dwStyle = WPSTYLE_CENTER;

			pActiveDesktop->SetWallpaper(filepath, 0);
			pActiveDesktop->SetWallpaperOptions(&wpo,0);
			pActiveDesktop->ApplyChanges(AD_APPLY_ALL);
			pActiveDesktop->Release();		
		}

		::CoUninitialize();

		return (hr == S_OK);
	}
	
	DLLEXPORT int setdesktopcolor(int r, int g, int b)
	{
		int elements[] = {
			COLOR_DESKTOP
		};
		
		COLORREF colors[] = {
			RGB(r,g,b) 
		};

		setdesktopimage(L"");

		return (::SetSysColors(_countof(elements), elements, colors) != 0);
	}

	DLLEXPORT int setgamma(int g)
	{
		WORD gamma[3][256] = {0};
	
		for (int i=0; i < 256; i++)
		{
			gamma[0][i] = i * (g + 128);
			gamma[1][i] = i * (g + 128);
			gamma[2][i] = i * (g + 128);
		}

		HDC hDC = ::GetDC(HWND_DESKTOP);
		BOOL bRet = ::SetDeviceGammaRamp(hDC, gamma);
		::ReleaseDC(HWND_DESKTOP, hDC);

		return (bRet == TRUE);
	}

	DLLEXPORT int hidescreen()
	{
		::PostMessage(g_hMainWnd, WM_CLOSE, NULL, NULL);
		::WaitForSingleObject(g_hThreadHandle, INFINITE);
		::CloseHandle(g_hThreadHandle);

		g_hMainWnd      = NULL;
		g_hThreadHandle = NULL;

		return 1;
	}

	DLLEXPORT int showscreen(const wchar_t* progressIcon, const wchar_t* mainLogoIcon, const wchar_t* message,  const wchar_t* version, int mirror)
	{
		if (g_hThreadHandle)
		{
			hidescreen();
		}

		g_mirrorOutput		= mirror != 0;
		g_progressImagePath = progressIcon;
		g_logoImagePath		= mainLogoIcon;
		g_progressMessage	= message;
		g_versionInfo		= version;

		g_hThreadHandle = reinterpret_cast<HANDLE>(
			_beginthreadex(NULL, 0, MainThreadProc, NULL, 0, 0));

		return 1;
	}

	DLLEXPORT int setmessage(const wchar_t* message)
	{
		AutoLockCS lock(&g_textCS);

		g_progressMessage = message;

		return 1;
	}

	DLLEXPORT int minimizewindows()
	{
		MinimizeAllWindows();

		return 1;
	}

	DLLEXPORT int rotatedisplay(int rotate)
	{
		static bool screenOriginallyRotated = IsRotatedScreen180();

		if (rotate)
		{
			if (screenOriginallyRotated)
			{	
				RotateScreen180(false);
			}	
		}
		else
		{
			if (screenOriginallyRotated)
			{	
				RotateScreen180(true);
			}	
		}

		return 1;
	}

	DLLEXPORT int isusbdrive(char drive)
	{
		int result = 0;

		wchar_t wszBuf[32] = {0};
		wsprintf(wszBuf, L"\\\\.\\%c:", drive);

		HANDLE hFile = CreateFile(wszBuf, FILE_READ_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);

		if (hFile != INVALID_HANDLE_VALUE)
		{
			STORAGE_PROPERTY_QUERY storagePropertyQuery;
			::ZeroMemory(&storagePropertyQuery, sizeof(STORAGE_PROPERTY_QUERY));

			storagePropertyQuery.PropertyId = StorageDeviceProperty;
			storagePropertyQuery.QueryType = PropertyStandardQuery;
			
			BYTE cbBuffer[1024];
			DWORD dwBytesReturned;
			
			if (::DeviceIoControl(hFile, IOCTL_STORAGE_QUERY_PROPERTY, &storagePropertyQuery, sizeof(STORAGE_PROPERTY_QUERY), cbBuffer, 1024, &dwBytesReturned, (LPOVERLAPPED)NULL))
			{	
				PSTORAGE_DEVICE_DESCRIPTOR pStorageDeviceDescriptor = (PSTORAGE_DEVICE_DESCRIPTOR)cbBuffer;

				/*
				fprintf(stderr, "%c removable:%s %s\n", 
					drive, 
					pStorageDeviceDescriptor->RemovableMedia ? "1" : "0",
					GetBusTypeStringID(pStorageDeviceDescriptor->BusType));
				*/

				//
				// Include builtin-memory card readers bustypes in our storage check.
				//

				BOOL bIsMaybeFlashStorage = (
					pStorageDeviceDescriptor->BusType == BusTypeSd  ||
					pStorageDeviceDescriptor->BusType == BusTypeMmc ||
					pStorageDeviceDescriptor->BusType == BusTypeUsb );

				if (pStorageDeviceDescriptor->RemovableMedia && bIsMaybeFlashStorage)
				{
					wchar_t wszDirName[32] = {0};
					ULARGE_INTEGER totalSizeInBytes = {0};

					wsprintf(wszDirName, L"%c:\\", drive);

					//
					// Hack: check that drive is available.
					//

					if (::GetDiskFreeSpaceEx(wszDirName, NULL, &totalSizeInBytes, NULL) && totalSizeInBytes.QuadPart > 0)
					{
						result = 1;
					}
				}
			}

			::CloseHandle(hFile);
		}

		return result;
	}

	DLLEXPORT int isadmin()
	{
		PSID AdministratorsGroup;
		SID_IDENTIFIER_AUTHORITY NtAuthority = SECURITY_NT_AUTHORITY;

		BOOL bSuccess = ::AllocateAndInitializeSid(
			&NtAuthority,
			2,
			SECURITY_BUILTIN_DOMAIN_RID,
			DOMAIN_ALIAS_RID_ADMINS,
			0, 0, 0, 0, 0, 0,
			&AdministratorsGroup);

		if (bSuccess)
		{
			if (!::CheckTokenMembership(NULL, AdministratorsGroup, &bSuccess))
			{
				bSuccess = FALSE;
			}

			::FreeSid(AdministratorsGroup);
		}

		return (bSuccess == TRUE);
	}	

	DLLEXPORT int runasdesktop(const wchar_t* program, const wchar_t* args, const wchar_t* workdir)
	{
		BOOL bSuccess = FALSE;

		std::wstring argv;		
		argv += program;
		argv += L" ";
		argv += args;
		
		HANDLE hProcessToken = 0;

		if (::OpenProcessToken(::GetCurrentProcess(), MAXIMUM_ALLOWED, &hProcessToken))
		{
			PSID pAdministratorSid = NULL;

			if (::ConvertStringSidToSid(SDDL_BUILTIN_ADMINISTRATORS, &pAdministratorSid))
			{
				HANDLE hRestrictedToken = 0;

				SID_AND_ATTRIBUTES sidsToDisable[] = 
				{
					pAdministratorSid, 0
				};

				if (::CreateRestrictedToken(hProcessToken, 0, _countof(sidsToDisable), sidsToDisable, 0, NULL, 0, 0, &hRestrictedToken))
				{
					PSID pLowIntegritySid = NULL;

					if (::ConvertStringSidToSid(SDDL_ML_MEDIUM, &pLowIntegritySid))
					{
						TOKEN_MANDATORY_LABEL tokenIntegrityLevel = {0};
						tokenIntegrityLevel.Label.Attributes = SE_GROUP_INTEGRITY;
						tokenIntegrityLevel.Label.Sid = pLowIntegritySid;

						if (::SetTokenInformation(hRestrictedToken, TokenIntegrityLevel, &tokenIntegrityLevel, sizeof(TOKEN_MANDATORY_LABEL) + ::GetLengthSid(pLowIntegritySid)))
						{
							STARTUPINFO startupInfo = {0};
							PROCESS_INFORMATION processInfo = {0};

							if (::CreateProcessAsUser(hRestrictedToken, NULL, const_cast<wchar_t*>(argv.c_str()), NULL, NULL, FALSE, 0, 0, workdir, &startupInfo, &processInfo))
							{
								::CloseHandle(processInfo.hThread);
								::CloseHandle(processInfo.hProcess);

								bSuccess = TRUE;
							}
						}

						::LocalFree(pLowIntegritySid);
					}

					::CloseHandle(hRestrictedToken);
				}

				::LocalFree(pAdministratorSid);
			}      
		}

		::CloseHandle(hProcessToken);

		return bSuccess;
	}

	DLLEXPORT int checksignal(const wchar_t* alias)
	{
		int ret = 0;

		//
		// We need security descriptors to make sure that the mutex
		// can be accessed even if the application is running under
		// two different security context (i.e. one instance is launched
		// with privileges and the other as with standard privileges).
		//

		SECURITY_ATTRIBUTES sa;
		SECURITY_DESCRIPTOR sd;

		if (InitializeWithDefaultAccess(sa, sd))
		{
			std::wstring id = std::wstring(L"Global\\") + std::wstring(alias);

			HANDLE hMutex = ::CreateMutex(&sa, FALSE, id.c_str());

			if (hMutex != NULL)
			{
				if (::GetLastError() == ERROR_ALREADY_EXISTS)
				{
					ret = 1;
				}	

				::CloseHandle(hMutex);
			}
		}

		return ret;
	}

	DLLEXPORT int setsignal(const wchar_t* alias)
	{
		int ret = 0;

		//
		// We need security descriptors to make sure that the mutex
		// can be accessed even if the application is running under
		// two different security context (i.e. one instance is launched
		// with privileges and the other as with standard privileges).
		//

		SECURITY_ATTRIBUTES sa;
		SECURITY_DESCRIPTOR sd;

		if (InitializeWithDefaultAccess(sa, sd))
		{
			std::wstring id = std::wstring(L"Global\\") + std::wstring(alias);

			HANDLE hMutex = ::CreateMutex(&sa, FALSE, id.c_str());

			if (hMutex != NULL)
			{
				//
				// Keep the mutex handle open to tie it's lifetime to the process.
				//

				ret = 1;				
			}
		}

		return ret;
	}

};

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
