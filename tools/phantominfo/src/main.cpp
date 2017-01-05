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

#include <stdio.h>
#include <string>
#include <HD/hd.h>
#include <HDU/hduVector.h>
#include <HDU/hduError.h>

#pragma comment(lib, "hd.lib")

struct DeviceData
{
    int             m_buttonCount;
    HDboolean       m_buttonState1;     // Has the device button 1 has been pressed.
    HDboolean       m_buttonState2;     // Has the device button 2 has been pressed.
    HDboolean       m_buttonState3;     // Has the device button 3 has been pressed.
    HDboolean       m_buttonState4;     // Has the device button 4 has been pressed.
    HDboolean       m_inkwellActive;    // Is haptic pen inserted into inkwell?
    hduVector3Dd    m_devicePosition;   // Current coordinates of haptic pen.
    HDErrorInfo     m_error;
};

static DeviceData	gServoDeviceData			= {0};
static bool			gDeviceVersionInitialized	= false;
static std::string  gDeviceVersion;

///////////////////////////////////////////////////////////////////////////////////////////////////
// Utilities.
///////////////////////////////////////////////////////////////////////////////////////////////////

void debugPrint(DeviceData& deviceData)
{
    fprintf(stderr, "Buttons:%d 1:%s 2:%s 3:%s 4:%s | Inkwell: %s | Pos: (%g, %g, %g)\n", 
        deviceData.m_buttonCount,
        deviceData.m_buttonState1  ? "on " : "off",
        deviceData.m_buttonState2  ? "on " : "off",
        deviceData.m_buttonState3  ? "on " : "off",
        deviceData.m_buttonState4  ? "on " : "off",
        deviceData.m_inkwellActive ? "on " : "off",
        deviceData.m_devicePosition[0], 
        deviceData.m_devicePosition[1], 
        deviceData.m_devicePosition[2]); 
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// HDAPI Device Callbacks.
///////////////////////////////////////////////////////////////////////////////////////////////////

HDCallbackCode HDCALLBACK updateDeviceCallback(void *pUserData)
{   
    hdBeginFrame(hdGetCurrentDevice());

	if (!gDeviceVersionInitialized)
	{
		gDeviceVersionInitialized = true;

		char buffer[2048]={0};

		HDdouble firmware = 0;
		hdGetDoublev( HD_DEVICE_FIRMWARE_VERSION, &firmware );

		sprintf_s(buffer, "<phantom><hdapi>%s</hdapi><vendor>%s</vendor><model>%s</model><driver>%s</driver><firmware>%g</firmware><serial>%s</serial></phantom>",
			hdGetString( HD_VERSION ),
			hdGetString( HD_DEVICE_VENDOR ),
			hdGetString( HD_DEVICE_MODEL_TYPE ),
			hdGetString( HD_DEVICE_DRIVER_VERSION ),
			firmware,
			hdGetString( HD_DEVICE_SERIAL_NUMBER )
			);

		gDeviceVersion = buffer;
	}
	
	hdGetIntegerv(HD_CURRENT_BUTTONS, 
        &gServoDeviceData.m_buttonCount);
    
    gServoDeviceData.m_buttonState1 = 
        (gServoDeviceData.m_buttonCount & HD_DEVICE_BUTTON_1) ? TRUE : FALSE;
    gServoDeviceData.m_buttonState2 = 
        (gServoDeviceData.m_buttonCount & HD_DEVICE_BUTTON_2) ? TRUE : FALSE;
    gServoDeviceData.m_buttonState3 = 
        (gServoDeviceData.m_buttonCount & HD_DEVICE_BUTTON_3) ? TRUE : FALSE;
    gServoDeviceData.m_buttonState4 = 
        (gServoDeviceData.m_buttonCount & HD_DEVICE_BUTTON_4) ? TRUE : FALSE;
        
    HDboolean inkwellNotActive = 0;

    hdGetDoublev(HD_CURRENT_POSITION, 
        gServoDeviceData.m_devicePosition);
    
    hdGetBooleanv(HD_CURRENT_INKWELL_SWITCH, 
        &inkwellNotActive);

    gServoDeviceData.m_inkwellActive = !inkwellNotActive;
    gServoDeviceData.m_error = hdGetError();
        
    hdEndFrame(hdGetCurrentDevice());

    return HD_CALLBACK_CONTINUE;    
}

HDCallbackCode HDCALLBACK copyDeviceDataCallback(void *pUserData)
{
    DeviceData *pDeviceData = (DeviceData *) pUserData;

    memcpy(pDeviceData, &gServoDeviceData, sizeof(DeviceData));

    return HD_CALLBACK_DONE;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Public API.
///////////////////////////////////////////////////////////////////////////////////////////////////

extern "C" 
{

// Swallow unhandled access-violation exceptions.
int handleException(unsigned int code, struct _EXCEPTION_POINTERS *ep) 
{
	fprintf(stderr, "Unhandled exception (%X) in phantominfo DLL\n", code);
	return (code == EXCEPTION_ACCESS_VIOLATION) ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH;
}


// Return -1 if no Phantom is connected, 1 if pen is in inkwell, 0 if it isn't.
__declspec(dllexport) int __cdecl getInkwellState()
{
	/*
	__try
	*/
	{
		HDSchedulerHandle hUpdateHandle = 0;
		HDErrorInfo error;

		HHD hHD = hdInitDevice(HD_DEFAULT_DEVICE);

		if (HD_DEVICE_ERROR(error = hdGetError()))
		{
			return -1;           
		}

		hUpdateHandle = hdScheduleAsynchronous(
			updateDeviceCallback, 
			0, 
			HD_MAX_SCHEDULER_PRIORITY);

		hdStartScheduler();

		if (HD_DEVICE_ERROR(error = hdGetError()))
		{
			return -1;
		}
	    
		DeviceData deviceData;
		memset(&deviceData, 0, sizeof(DeviceData));

		for (int i = 0; i < 10; i++)
		{
			hdScheduleSynchronous(copyDeviceDataCallback, 
				&deviceData, HD_MIN_SCHEDULER_PRIORITY);

			if (HD_DEVICE_ERROR(deviceData.m_error))
			{
				break;
			}
	       
			::Sleep(100);
		}

		hdStopScheduler();
		hdUnschedule(hUpdateHandle);
		hdDisableDevice(hHD);

		return (deviceData.m_inkwellActive ? 1 : 0);
	}
	/*
	__except(handleException(GetExceptionCode(), GetExceptionInformation()))
	{
		// Handle errors internally preventing them from bubbling up into the VRS Python 
		// system. Why? We've already been defeated, better keep the system running than 
		// going down due a driver glitch etc.
	}

	return -1;
	*/
}

__declspec(dllexport) const char* __cdecl getVersionInfo()
{
	if (!gDeviceVersionInitialized)
	{
		if (getInkwellState() == -1)
		{
			return "";
		}
	}

	return gDeviceVersion.c_str();
}

} // extern "C"

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
