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
#include <stdio.h>

#pragma comment(linker, "/entry:mainCRTStartup")
#pragma comment(linker, "/subsystem:console")

bool ConfigureDisplay(int width, int height, int refresh_rate, bool flipped)
{	
	bool update = false;

	DEVMODE DeviceMode = { 0 };

	::EnumDisplaySettings( NULL, ENUM_CURRENT_SETTINGS,	&DeviceMode );

	if (width != DeviceMode.dmPelsWidth || height != DeviceMode.dmPelsHeight)
	{

		DeviceMode.dmFields |= DM_PELSWIDTH;		
		DeviceMode.dmPelsWidth = height;
		
		DeviceMode.dmFields |= DM_PELSHEIGHT;
		DeviceMode.dmPelsHeight = height;

		update = false;
	}

	if (DeviceMode.dmDisplayFrequency != refresh_rate)
	{
		DeviceMode.dmFields |= DM_DISPLAYFREQUENCY;
		DeviceMode.dmDisplayFrequency = refresh_rate;

		update = true;
	}

	if (flipped && DeviceMode.dmDisplayOrientation != DMDO_180)
	{
		DeviceMode.dmDisplayOrientation = DMDO_180;

		update = true;
	}

	if (!flipped && DeviceMode.dmDisplayOrientation != DMDO_DEFAULT)
	{	
		DeviceMode.dmDisplayOrientation = DMDO_DEFAULT;

		update = true;
	}

	if (update)
	{
		return (::ChangeDisplaySettings( &DeviceMode, CDS_UPDATEREGISTRY ) == DISP_CHANGE_SUCCESSFUL);
	}

	return true;
}

int main(int argc, char *argv[])
{
	struct DisplayMode {
		char* name;
		int width;
		int height;
		int refresh_rate;
		bool flipped;
	} modes[] = {
		{"/1680x1050_60Hz_landscape",  1680, 1050,  60, false},
		{"/1680x1050_60Hz_flipped",    1680, 1050,  60, true},
		{"/1680x1050_120Hz_landscape", 1680, 1050, 120, false},
		{"/1680x1050_120Hz_flipped",   1680, 1050, 120, true},
		{"/1920x1080_120Hz_landscape", 1920, 1080, 120, false},
		{"/1920x1080_120Hz_flipped",   1920, 1080, 120, true},
	};

	bool success = false;

	if (argc == 2)
	{
		for (int i = 0; i < _countof(modes); i++)
		{
			if (!strcmp(argv[1], modes[i].name))
			{
				success = ConfigureDisplay(modes[i].width, modes[i].height, modes[i].refresh_rate, modes[i].flipped);				
			}
		}
	}

	if (!success)
	{
		fprintf(stderr, "Missing or unsupported display mode, choose between:\n");
		for (int i = 0; i < _countof(modes); i++)
		{
			fprintf(stderr, "  %s\n", modes[i].name);
		}
	}

	return success ? EXIT_SUCCESS : EXIT_FAILURE;
}
