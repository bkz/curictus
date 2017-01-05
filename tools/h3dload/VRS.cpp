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

///////////////////////////////////////////////////////////////////////////////////////////////////
// Global configuration.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include "debugtools/Precompiled.h"
#include "debugtools/DebugTools.h"

// Build configuration:
//
// - Release   => console=off debugtools=on
// - ReleseDev => console=on  debugtools=on
// - Debug     => console=on  debugtools=off
//
// Note: DebugTools are installed/enabled in main()!

#ifdef NDEBUG
	#ifdef CURICTUS_DEVELOPER_MODE
		#pragma comment(linker, "/entry:mainCRTStartup")
		#pragma comment(linker, "/subsystem:console")
	#else
		#pragma comment(linker, "/entry:mainCRTStartup")
		#pragma comment(linker, "/subsystem:windows")
	#endif
#else
	#pragma comment(linker, "/entry:mainCRTStartup")
	#pragma comment(linker, "/subsystem:console")
#endif

#pragma comment(lib, "winmm.lib")

///////////////////////////////////////////////////////////////////////////////////////////////////
// Utilities.
///////////////////////////////////////////////////////////////////////////////////////////////////

std::wstring GetExePath()
{
	static WCHAR wszCurrPath[_MAX_PATH] = {L'\0'};

	DWORD dwPathLen = ::GetModuleFileName(NULL, wszCurrPath, _countof(wszCurrPath));

	if (dwPathLen > 0)
	{
		for (DWORD i = dwPathLen - 1; i >= 0; --i)
		{
			if (wszCurrPath[i] == L'\\' || wszCurrPath[i] == L'/')
			{
				wszCurrPath[i+1] = L'\0';
				break;
			}
		}
	}

	return wszCurrPath;
}

void PlaySoundFile(const wchar_t* pwszSoundFile)
{
	std::wstring path = GetExePath() + pwszSoundFile;

	TRACE(L"Playing sound: %s", path.c_str());

	::PlaySound(path.c_str(), NULL, SND_FILENAME|SND_ASYNC|SND_NODEFAULT);
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// DeviceLogger.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include <H3D/SFVec3f.h>
#include <H3D/SFVec3d.h>
#include <H3D/H3DForceEffect.h> 
#include <H3DUtil/Threads.h>
#include <HAPI/HAPIHapticsDevice.h>
#include <HAPI/HapticForceField.h>
#include <HAPI/HAPIForceEffect.h> 

using namespace H3D;

// The haptic device logger is a singleton used to record raw haptic data and 
// generate a XML logfile from the sampled data. Basically the client makes 
// sure that the environment variable H3D_DEVICELOG_FILENAME has been set and 
// calls RecordHapticState() from the haptic servo loop and the class dynamically 
// downsample data and generate a logfile. Normally OpenHaptics will poll the 
// device at a rate of 1000 Hz which we downsample by collecting sample and 
// averaging out the force and velocity measurements, the last position and 
// rotation values for a sample period is used as the measurement since we can't 
// really calculate averages in this case.

struct DeviceLogger 
{
	enum { DOWNSAMPLE_FREQ = 60 };

	enum { MAX_LOG_DURATION_SECS = 60 * 60 };

	typedef HAPI::HAPIHapticsDevice::DeviceValues DeviceValues;

	typedef std::vector<DeviceValues> DeviceValuesVector;

	DeviceLogger() : m_pLogFile(NULL), m_startTime(0), m_lastTime(0)
	{
		const char* filename = getenv("H3D_DEVICELOG_FILENAME");

		if (filename != NULL)
		{
			if (!strcmp(filename, "stdout"))
			{
				m_pLogFile = stdout;
			}
			else if (!strcmp(filename, "stderr"))
			{
				m_pLogFile = stderr;
			}
			else
			{
				m_pLogFile = _fsopen(filename, "wt", _SH_DENYNO);
			}

			TRACE(L"Device log file %s => %s", filename, m_pLogFile ? "true" : "false");
		}

		if (m_pLogFile)
		{
			DeviceInfo* di = DeviceInfo::getActive();

			if ( di && di->device->size() > 0 ) 
			{
				H3DHapticsDevice *d = static_cast< H3DHapticsDevice * >(*di->device->begin());

				fprintf(m_pLogFile,
					"<calibration>\n"																							\
					"<position>%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f</position>\n"	\
					"<orientation x=\"%.8f\" y=\"%.8f\" z=\"%.8f\" a=\"%.8f\" />\n"												\
					"</calibration>\n",
					d->positionCalibration->rt_pos_calibration.getElement(0,0),
					d->positionCalibration->rt_pos_calibration.getElement(1,0),
					d->positionCalibration->rt_pos_calibration.getElement(2,0),
					d->positionCalibration->rt_pos_calibration.getElement(3,0),
					d->positionCalibration->rt_pos_calibration.getElement(0,1),
					d->positionCalibration->rt_pos_calibration.getElement(1,1),
					d->positionCalibration->rt_pos_calibration.getElement(2,1),
					d->positionCalibration->rt_pos_calibration.getElement(3,1),
					d->positionCalibration->rt_pos_calibration.getElement(0,2),
					d->positionCalibration->rt_pos_calibration.getElement(1,2),
					d->positionCalibration->rt_pos_calibration.getElement(2,2),
					d->positionCalibration->rt_pos_calibration.getElement(3,2),
					d->positionCalibration->rt_pos_calibration.getElement(0,3),
					d->positionCalibration->rt_pos_calibration.getElement(1,3),
					d->positionCalibration->rt_pos_calibration.getElement(2,3),
					d->positionCalibration->rt_pos_calibration.getElement(3,3),
					d->orientationCalibration->rt_orn_calibration.axis.x, 
					d->orientationCalibration->rt_orn_calibration.axis.y, 
					d->orientationCalibration->rt_orn_calibration.axis.z, 
					d->orientationCalibration->rt_orn_calibration.angle);
			}
		}

		m_startTime = m_lastTime = TimeStamp::now();
	}

	~DeviceLogger()
	{
		if (m_pLogFile && (m_pLogFile != stdout) && (m_pLogFile != stderr))
		{
			fclose(m_pLogFile);
		}
	}

	void RecordHapticState(DeviceValues& values)
	{
		double elapsed = GetElapsedTime();

		// Stop logging altogether if the session has lasted more than this, 
		// normally sessions should be quite short so think of this as a safety 
		// mechanism to keep the disk from filling up.

		if (elapsed < MAX_LOG_DURATION_SECS)
		{
			if (GetDeltaTime() > (1.0 / DOWNSAMPLE_FREQ))
			{
				WriteHapticEvent(elapsed);
				ResetDelta();
			}
			else
			{
				m_samples.push_back(values);
			}
		}
	}

	void WriteHapticEvent(double timestamp)
	{
		if (m_pLogFile && m_samples.size() > 0)
		{
			const DeviceValues& last = m_samples[m_samples.size()-1];

			double fX = 0, fY = 0, fZ = 0;
			double vX = 0, vY = 0, vZ = 0;

			for (DeviceValuesVector::const_iterator it = m_samples.begin(); it != m_samples.end(); ++it)
			{
				const DeviceValues& values (*it);

				fX += values.force.x;
				fY += values.force.y;
				fZ += values.force.z;

				vX += values.velocity.x;
				vY += values.velocity.y;
				vZ += values.velocity.z;
			}

			fX /= m_samples.size();
			fY /= m_samples.size();
			fZ /= m_samples.size();

			vX /= m_samples.size();
			vY /= m_samples.size();
			vZ /= m_samples.size();

			fprintf(m_pLogFile, 
				"<event timestamp=\"%.8f\">\n"									\
				"<position x=\"%.8f\" y=\"%.8f\" z=\"%.8f\" />\n"				\
				"<orientation x=\"%.8f\" y=\"%.8f\" z=\"%.8f\" a=\"%.8f\" />\n"	\
				"<force x=\"%.8f\" y=\"%.8f\" z=\"%.8f\" />\n"					\
				"<velocity x=\"%.8f\" y=\"%.8f\" z=\"%.8f\" />\n"				\
				"</event>\n",
				timestamp,
				last.position.x, 
				last.position.y, 
				last.position.z,
				last.orientation.axis.x, 
				last.orientation.axis.y, 
				last.orientation.axis.z, 
				last.orientation.angle,
				fX, fY, fZ,
				vX, vY, vZ);

			fflush(m_pLogFile);
		}

		m_samples.clear();
	}

	double GetElapsedTime() const
	{
		return TimeStamp::now() - m_startTime;
	}

	double GetDeltaTime() const
	{
		return TimeStamp::now() - m_lastTime;
	}

	void ResetDelta()
	{
		m_lastTime = TimeStamp::now();
	}

	static DeviceLogger* GetInstance()
	{
		static DeviceLogger* instance = NULL;
		
		if (!instance) 
			instance = new DeviceLogger;

		return instance;
	}

	FILE*				m_pLogFile;
	DeviceValuesVector	m_samples;
	double				m_startTime;
	double				m_lastTime;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// HapticDeviceStats.
///////////////////////////////////////////////////////////////////////////////////////////////////

// Due to limitations in H3D we have to use a separate X3D node from which 
// clients read device data polled by HapticDeviceLogger node. Nodes that 
// are put inside <PythonScript> tags and refereces by a script won't get
// updated properly (traverseSG() won't get called) and thus we'll have 
// to use something like this:
//
//	<HapticDeviceLogger />
//	<PythonScript DEF="PS" url="test.py" >
//		<HapticDeviceStats containerField="references" />
//	</PythonScript>
//
// Basically we'll internally route data from HapticeDeviceLogger to the 
// HapticDeviceStats node to make the data available to client for scripting 
// purposes. The only remaining problem is the scenegraph might get updated 
// and/or rendered via traverseSG() in the Python script before we've even 
// managed to read data from the haptic device. This always occurs during 
// the scenegraph construction initialization phase which means that we have 
// signal to client somehow when we actually have some data available for 
// them so that they can skip polling us for the first couple of N calls to 
// traverseSG(). We solve this by adding a field called "active" which remains 
// set to false until the first time we recieve data via the Update() method 
// and from then on it is always set to true.
//
// Note: this node is treated as a singleton but you always have to check the 
// result from GetInstance() as depending on the order in the scenegraph, this 
// node might not have been created yet!
//

typedef HAPI::HAPIHapticsDevice::DeviceValues HapticDeviceValues;

struct HapticDeviceStats : public H3DForceEffect 
{
	HapticDeviceStats( 
		Inst< SFNode >		_metadata = 0, 
		Inst< SFBool >		_active = 0,
		Inst< SFVec3d >		_force = 0,
		Inst< SFVec3d >		_torque = 0,
		Inst< SFVec3d >		_position = 0,
		Inst< SFVec3d >		_velocity = 0,
		Inst< SFRotation >	_orientation = 0,
		Inst< SFBool >		_button1 = 0,
		Inst< SFBool >		_button2 = 0,
		Inst< SFBool >		_button3 = 0,
		Inst< SFBool >		_button4 = 0,
		Inst< SFDouble >	_timestamp = 0,
		Inst< SFDouble >	_distance = 0
		)
		: H3DForceEffect( _metadata )
		, force			( _force )
		, active		( _active )
		, torque		( _torque )
		, position		( _position )
		, velocity		( _velocity )
		, orientation	( _orientation )
		, button1		( _button1 )
		, button2		( _button2 )
		, button3		( _button3 )
		, button4		( _button4 )
		, timestamp		( _timestamp )
		, distance		( _distance )
	{
		type_name = "HapticDeviceStats";
		database.initFields( this );
		
		s_instance = this;
		
		active->setValue(false);
		button1->setValue(0);
		button2->setValue(0);
		button3->setValue(0);
		button4->setValue(0);
		timestamp->setValue(0);
		distance->setValue(0);
	}

	~HapticDeviceStats()
	{
		s_instance = NULL;
	}

	void Update( const H3DDouble& _timestamp, const HapticDeviceValues& _values, const H3DDouble& _distance )
	{
		active->setValue(true);

		force->setValue( _values.force ); 
		torque->setValue( _values.torque );
		position->setValue( _values.position );
		velocity->setValue( _values.velocity );
		
		orientation->setValue( 
			H3D::Rotation(
				static_cast<float>(_values.orientation.axis.x),  
				static_cast<float>(_values.orientation.axis.y), 
				static_cast<float>(_values.orientation.axis.z), 
				static_cast<float>(_values.orientation.angle)));

		button1->setValue( !!(_values.button_status & (1<<0)) );
		button2->setValue( !!(_values.button_status & (1<<1)) );
		button3->setValue( !!(_values.button_status & (1<<2)) );
		button4->setValue( !!(_values.button_status & (1<<3)) );
		
		timestamp->setValue( _timestamp );
		distance->setValue( _distance );
	}

	static HapticDeviceStats* GetInstance()
	{
		return s_instance;
	}

	auto_ptr< SFBool >		active;
	auto_ptr< SFVec3d >		force;
	auto_ptr< SFVec3d >		torque;
	auto_ptr< SFVec3d >		position;
	auto_ptr< SFVec3d >		velocity;
	auto_ptr< SFRotation >	orientation;
	auto_ptr< SFBool >		button1;
	auto_ptr< SFBool >		button2;
	auto_ptr< SFBool >		button3;
	auto_ptr< SFBool >		button4;
	auto_ptr< SFDouble >	timestamp;
	auto_ptr< SFDouble >	distance;
		
	static H3DNodeDatabase database;

	static HapticDeviceStats* s_instance;
};

H3DNodeDatabase HapticDeviceStats::database( 
	"HapticDeviceStats", 
	&(newInstance<HapticDeviceStats>), 
	typeid( HapticDeviceStats ),
	&H3DForceEffect::database 
);

HapticDeviceStats* HapticDeviceStats::s_instance = NULL;

namespace HapticDeviceStatsInternals 
{
	FIELDDB_ELEMENT( HapticDeviceStats, active,			INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, force,			INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, torque,			INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, position,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, velocity,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, orientation,	INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, button1,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, button2,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, button3,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, button4,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, timestamp,		INPUT_OUTPUT );
	FIELDDB_ELEMENT( HapticDeviceStats, distance,		INPUT_OUTPUT );
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// HapticDeviceLoggerForceEffect.
///////////////////////////////////////////////////////////////////////////////////////////////////

// In order to poll the haptic device for raw data we use fake force effect 
// which gets added to all H3D haptic devices. This hook into the haptic 
// update loop allows us the recieve updated data at the real-time rate of 
// the haptic servo loop (running in a separate thread) which is normally 
// running at 1000 Hz. The device data is then pushed to both the DeviceLogger 
// and instances of the HapticDeviceStats node which take care of logging 
// it and exposing it to clients.

struct HapticDeviceLoggerForceEffect : public HAPI::HAPIForceEffect 
{
	EffectOutput virtual calculateForces( const EffectInput &input ) 
	{	
		HAPI::HAPIHapticsDevice::DeviceValues values = input.hd->getRawDeviceValues();

		// We can't really do any distance calculation until we have read twice 
		// from the haptic devicem otherwise we'll just end up calculating the 
		// distance of the haptic pen from origo (0,0,0) as the first measurement.

		if (!s_firstMeasurement)
		{
			s_distance = s_distance + sqrt( 
				(values.position.x - s_lastDeviceValues.position.x) * (values.position.x - s_lastDeviceValues.position.x) +
				(values.position.y - s_lastDeviceValues.position.y) * (values.position.y - s_lastDeviceValues.position.y) +
				(values.position.z - s_lastDeviceValues.position.z) * (values.position.z - s_lastDeviceValues.position.z));
		}
		else
		{
			s_firstMeasurement = false;
		}

		s_lastDeviceValues = values;

		s_timestamp = DeviceLogger::GetInstance()->GetElapsedTime();
			
		HapticDeviceStats* pDeviceStats = HapticDeviceStats::GetInstance();
		
		if (pDeviceStats)
		{
			pDeviceStats->Update(s_timestamp, s_lastDeviceValues, s_distance);
		}
		
		DeviceLogger::GetInstance()->RecordHapticState(values);

		return EffectOutput();
	}

	static H3DDouble GetDistance()
	{
		return s_distance;
	}

	static H3DDouble GetElapsedTime()
	{
		return s_timestamp;
	}

private:
	static H3DDouble			s_timestamp;
	static H3DDouble			s_distance;
	static HapticDeviceValues	s_lastDeviceValues;
	static bool					s_firstMeasurement;
};

H3DDouble			HapticDeviceLoggerForceEffect::s_distance			= 0;
H3DDouble			HapticDeviceLoggerForceEffect::s_timestamp			= 0;
bool				HapticDeviceLoggerForceEffect::s_firstMeasurement	= true;
HapticDeviceValues	HapticDeviceLoggerForceEffect::s_lastDeviceValues;

///////////////////////////////////////////////////////////////////////////////////////////////////
// HapticDeviceLogger.
///////////////////////////////////////////////////////////////////////////////////////////////////

// If this X3D node is added to a scenegraph it will insert a special force 
// effect for logging purposes which will generate a XML logfile. One can also 
// add a HapticeDeviceStats X3D node in combination to this node to be able to 
// access raw device data in real-time from Python scripts.

struct HapticDeviceLogger : public H3DForceEffect 
{
	HapticDeviceLogger( Inst< SFNode > _metadata = 0 )
		: H3DForceEffect( _metadata )
	{
		type_name = "HapticDeviceLogger";
		database.initFields( this );
	}

	virtual void traverseSG( TraverseInfo &ti ) 
	{
		if ( ti.hapticsEnabled() ) 
		{
			ti.addForceEffectToAll( new HapticDeviceLoggerForceEffect );
		}
	}

private:
	static H3DNodeDatabase database;
};

H3DNodeDatabase HapticDeviceLogger::database( 
	"HapticDeviceLogger", 
	&(newInstance<HapticDeviceLogger>), 
	typeid( HapticDeviceLogger ),
	&H3DForceEffect::database 
);

///////////////////////////////////////////////////////////////////////////////////////////////////
// FlashController.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include "flash/Flash.h"
#include "flash/FlashPlayer.h"

#ifdef CURICTUS_DEVELOPER_MODE
	#include "flash/Profile.h"
#else
	#define PROFILE(name) 
	#define PROFILE_FPS() 
#endif

H3D_API_EXCEPTION( FlashQuitException );
H3D_API_EXCEPTION( FlashAbortException );

class FlashController
{
private:
	struct EventHandler : public IFlashEventHandler
	{
		virtual HRESULT FlashCall(const wchar_t* request)
		{
			return E_NOTIMPL;
		}

		virtual HRESULT FSCommand(const wchar_t* command, const wchar_t* args)
		{
			TRACE(L"fscommand(%s)", command);

			if (!wcscmp(command, L"quit_h3d"))
			{
				throw FlashQuitException();
			}

			if (!wcscmp(command, L"abort_h3d"))
			{
				throw FlashAbortException();
			}

			return E_NOTIMPL;
		}
	};	

public:
	FlashController()
	{
		m_hMemDC      = NULL;
		m_hBitmap     = NULL;
		m_flashPlayer = NULL;

		Reset();
	}

	~FlashController()
	{
		Reset();
	}

	bool LoadMovie(int width, int height, const wchar_t* pwszFileName)
	{
		return Resize(width, height) && m_flashPlayer->LoadMovie(pwszFileName);
	}

	bool LoadURL(int width, int height, const wchar_t* pwszURL)
	{
		return Resize(width, height) && m_flashPlayer->LoadURL(pwszURL);
	}

	bool RenderBGR(unsigned char*& data)
	{
		const RECT* pUpdateRect = NULL;

		if (m_flashPlayer && m_flashPlayer->IsNeedUpdate(&pUpdateRect))
		{
			PROFILE(flash);

			m_flashPlayer->DrawFrame(m_hMemDC);

			BITMAPINFO BMInfo;
			BMInfo.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
			BMInfo.bmiHeader.biBitCount = 0;

			if (::GetDIBits(m_hMemDC, (HBITMAP)m_hBitmap, 0,0, NULL, &BMInfo, DIB_RGB_COLORS) != 0)
			{
				int sizeX = BMInfo.bmiHeader.biWidth;
				int sizeY = BMInfo.bmiHeader.biHeight;
				BMInfo.bmiHeader.biBitCount = 24;
				BMInfo.bmiHeader.biCompression = BI_RGB;  
				const DWORD BitmapLength = sizeX * sizeY * 3;

				if (::GetDIBits(m_hMemDC, (HBITMAP)m_hBitmap, 0, sizeY, data, &BMInfo, DIB_RGB_COLORS) != 0)
				{
					return true;
				}
			}
		}

		return false;
	}

	void SendMouseMove(int x, int y)
	{
		if (m_flashPlayer) 
		{
			if (x != m_mousex && y != m_mousey)
			{
				m_mousex = x;
				m_mousey = y;

				m_flashPlayer->SetMousePos(x, y);
			}
		}
	}

	void SendMouseClick(bool pressed)
	{
		if (m_flashPlayer) 
		{
			m_flashPlayer->SetMouseButtonState(m_mousex, m_mousey, FlashPlayer::eMouse1, pressed);
		}
	}

	void SendChar(int ch)
	{
		if (m_flashPlayer) 
		{
			m_flashPlayer->SendChar(ch, 0);
		}
	}

	void SendKey(int vk)
	{
		if (m_flashPlayer) 
		{
			m_flashPlayer->SendKey(true,  vk, 0);
			m_flashPlayer->SendKey(false, vk, 0);
		}
	}

private:
	void Reset()
	{
		if (m_hBitmap)
		{
			::DeleteObject(m_hBitmap);
			m_hBitmap = NULL;
		}

		if (m_hMemDC)
		{
			::DeleteDC(m_hMemDC);
			m_hMemDC = NULL;
		}

		if (m_flashPlayer)
		{
			delete m_flashPlayer;
			m_flashPlayer = NULL;
		}

		m_mousex = 0;
		m_mousey = 0;
	}

	bool Resize(int width, int height)
	{
		Reset();

		HDC hDC = ::GetDC(HWND_DESKTOP);		
		
		m_hMemDC  = ::CreateCompatibleDC(hDC);		
		m_hBitmap = ::CreateCompatibleBitmap(hDC, width, height);			
		
		::SelectObject(m_hMemDC, m_hBitmap);		
		
		::ReleaseDC(HWND_DESKTOP, hDC);

		m_flashPlayer = Flash::GetInstance()->CreatePlayer(width, height);

		if (m_flashPlayer)
		{
			m_flashPlayer->AddEventHandler(&m_eventHandler);
		}

		return (m_flashPlayer != NULL);
	}

	HDC				m_hMemDC;
	HBITMAP			m_hBitmap;
	int				m_mousex;
	int				m_mousey;
	FlashPlayer*	m_flashPlayer;
	EventHandler    m_eventHandler;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// FlashMovieTexture.
///////////////////////////////////////////////////////////////////////////////////////////////////

#include <H3D/X3DTexture2DNode.h>

// Simulate a Wacom style tablet instead of the default "point touch and click" 
// iPhone style mouse emulation. Instead of merely "touching" the FlashMovieTexture 
// we'll also use the force route to simulate a pressure sensitive surface. 
const bool SIMULATE_WACOM_TABLET = false;

class FlashMovieTexture : public X3DTexture2DNode 
{
public:
	class FilenameField: public OnNewValueSField< AutoUpdate< SFString > > 
	{
		virtual void onNewValue( const std::string &v );
    };

	class URLField: public OnNewValueSField< AutoUpdate< SFString > > 
	{
		virtual void onNewValue( const std::string &v );
    };

	class WidthField: public OnNewValueSField< AutoUpdate< SFInt32 > > 
	{
		virtual void onNewValue( const int &v );
    };

	class HeightField: public OnNewValueSField< AutoUpdate< SFInt32 > > 
	{
		virtual void onNewValue( const int &v );
    };

	class ForceField: public OnNewValueSField< AutoUpdate< SFVec3f > > 
	{
      virtual void onNewValue( const Vec3f &v );
    };

	class IsTouchedField: public OnNewValueSField< AutoUpdate< SFBool > > 
	{
		virtual void onNewValue( const bool &b );
    };

	class ContactTexCoordField: public OnNewValueSField< AutoUpdate< SFVec3f > > 
	{
      virtual void onNewValue( const Vec3f &v );
    };

	class KeyPressField: public OnNewValueSField< AutoUpdate< SFString > > 
	{
		virtual void onNewValue( const std::string &v );
    };

	class ActionKeyPressField: public OnNewValueSField< AutoUpdate< SFInt32 > > 
	{
		virtual void onNewValue( const int &v );
    };

	FlashMovieTexture( 
        Inst< DisplayList               > _displayList          = 0,
        Inst< SFNode                    > _metadata             = 0,
        Inst< SFBool                    > _repeatS              = 0,
        Inst< SFBool                    > _repeatT              = 0,
        Inst< SFBool                    > _scaleToP2            = 0,
        Inst< SFImage                   > _image                = 0,
        Inst< SFTextureProperties       > _textureProperties    = 0,
        Inst< SFString                  > _pressSoundFilename   = 0,
        Inst< SFString                  > _releaseSoundFilename = 0,
        Inst< SFFloat                   > _pressForce           = 0,
        Inst< SFFloat                   > _releaseForce         = 0,
        Inst< WidthField                > _width                = 0,
        Inst< HeightField               > _height               = 0,
        Inst< FilenameField             > _filename             = 0,
		Inst< URLField                  > _url                  = 0,
        Inst< ForceField                > _force                = 0,
        Inst< IsTouchedField            > _isTouched            = 0,
        Inst< ContactTexCoordField      > _contactTexCoord      = 0,
		Inst< KeyPressField             > _keyPress             = 0,
		Inst< ActionKeyPressField       > _actionKeyPress       = 0 )
		: X3DTexture2DNode( _displayList, _metadata, _repeatS, _repeatT, _scaleToP2, _image, _textureProperties )
		, pressSoundFilename( _pressSoundFilename )
		, releaseSoundFilename( _releaseSoundFilename )
		, pressForce( _pressForce )
		, releaseForce( _releaseForce )
		, width( _width)
		, height( _height )
		, filename( _filename )
		, url( _url )
		, force( _force )
		, isTouched( _isTouched)
		, contactTexCoord( _contactTexCoord )
		, keyPress( _keyPress )
		, actionKeyPress( _actionKeyPress )
	{
		type_name = "X3DTexture2DNode";
		database.initFields( this );
		pressForce->setValue(2.5f);
		releaseForce->setValue(1.0f);
		width->setValue(256);
		height->setValue(256);
		image->setValue( NULL );
		isMouseUp = true;
		isMouseDown = false;
		needMouseReset = false;
		pTextureData = NULL;
		reload = true;
	}

	virtual ~FlashMovieTexture()
	{
	}

	virtual void traverseSG( TraverseInfo &ti )
	{
		PROFILE_FPS();

		const int WIDTH       = width->getValue();
		const int HEIGHT      = height->getValue();
		const int BUFFER_SIZE = WIDTH * HEIGHT * 3;

		PixelImage *i = dynamic_cast< PixelImage * >( image->getValue() ); 

		if( !i || reload ) 
		{ 		
			reload = false;

			if (filename->getValue().size())
			{
				std::wstring ws;
				ws.assign(filename->getValue().begin(), filename->getValue().end());			
				bool success = flash.LoadMovie(WIDTH, HEIGHT, ws.c_str());
				TRACE(L"Load movie: %s @ %d x %d => %s", 
					filename->getValue().c_str(), WIDTH, HEIGHT, 
					success ? "true" : "false");
			}
			
			if (url->getValue().size())
			{
				std::wstring ws;
				ws.assign(url->getValue().begin(), url->getValue().end());			
				bool success = flash.LoadURL(WIDTH, HEIGHT, ws.c_str());
				TRACE(L"Load URL: %s @ %d x %d => %s", 
					url->getValue().c_str(), WIDTH, HEIGHT,
					success ? "true" : "false");
			}

			pTextureData = new unsigned char[ BUFFER_SIZE ];
			
			if (!flash.RenderBGR(pTextureData))
			{
				memset(pTextureData, 255, BUFFER_SIZE);
			}

			image->setValue( new PixelImage( 
				WIDTH,
				HEIGHT,
				1, 
				24,
				Image::BGR,
				Image::UNSIGNED,
				pTextureData));
 		} 
		else 
		{
			if (flash.RenderBGR(pTextureData))
			{
				image->setEditedArea( 0, 0, 0,
					WIDTH  - 1, 
					HEIGHT - 1, 
					0 );

				image->endEditing();
			}
		}
	}

	bool								isMouseUp;
	bool								isMouseDown;
	bool								needMouseReset;
	bool								reload;
	FlashController						flash;
	
	auto_ptr< SFInt32  >				width;
	auto_ptr< SFInt32  >				height;
	auto_ptr< SFString >				pressSoundFilename;	
	auto_ptr< SFString >				releaseSoundFilename;	
	auto_ptr< SFFloat  >				pressForce;	
	auto_ptr< SFFloat  >				releaseForce;	
	
	auto_ptr< FilenameField        >	filename;	
	auto_ptr< URLField             >	url;	
	auto_ptr< ForceField           > 	force;
	auto_ptr< IsTouchedField       > 	isTouched;
	auto_ptr< ContactTexCoordField > 	contactTexCoord;
	auto_ptr< KeyPressField        > 	keyPress;
	auto_ptr< ActionKeyPressField  > 	actionKeyPress;

	static H3DNodeDatabase database;

protected:
	unsigned char *pTextureData;
};

void FlashMovieTexture::FilenameField::onNewValue( const std::string &s )
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	pTex->reload = true;
}

void FlashMovieTexture::URLField::onNewValue( const std::string &s )
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	pTex->reload = true;
}

void FlashMovieTexture::WidthField::onNewValue( const int &v )
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	//
	// Don't allow dynamic resize of texture after it has been initialized.
	//

	assert(pTex->image->getValue() == NULL);
}

void FlashMovieTexture::HeightField::onNewValue( const int &v )
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	//
	// Don't allow dynamic resize of texture after it has been initialized.
	//

	assert(pTex->image->getValue() == NULL);
}

void FlashMovieTexture::ForceField::onNewValue( const Vec3f &tc ) 
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	if (SIMULATE_WACOM_TABLET)
	{
		int x = int(tc.x * pTex->width->getValue());
		int y = pTex->height->getValue() - int(tc.y * pTex->height->getValue());	
		
		float f = tc.length();

		float pressF   = pTex->pressForce->getValue();
		float releaseF = pTex->releaseForce->getValue();

		if (f > pressF && !pTex->isMouseDown && pTex->isMouseUp)
		{
			pTex->isMouseDown = true;
			pTex->isMouseUp = false;

			std::wstring filename;
			filename.assign(
				pTex->pressSoundFilename->getValue().begin(), 
				pTex->pressSoundFilename->getValue().end());

			if (filename.size())
			{
				PlaySoundFile(filename.c_str());
			}

			TRACE(L"Force = %f @ %d %d", f, x, y);
			TRACE(L"Mouse click -> down");
			pTex->flash.SendMouseClick(true);
		}

		if (f < releaseF && pTex->isMouseDown && !pTex->isMouseUp)
		{
			pTex->isMouseDown = false;
			pTex->isMouseUp = true;

			std::wstring filename;
			filename.assign(
				pTex->releaseSoundFilename->getValue().begin(), 
				pTex->releaseSoundFilename->getValue().end());
			
			if (filename.size())
			{
				PlaySoundFile(filename.c_str());
			}

			TRACE(L"Force = %f @ %d %d", f, x, y);
			TRACE(L"Mouse click -> up");
			pTex->flash.SendMouseClick(false);

			if (pTex->needMouseReset)
			{
				TRACE(L"Performing queued mouse reset to 0,0");
				pTex->flash.SendMouseMove(0,0);
				pTex->needMouseReset = false;
			}
		}
	}
}

void FlashMovieTexture::IsTouchedField::onNewValue( const bool  &touched ) 
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	TRACE(L"isTouched = %d", int(touched)); 

	if (SIMULATE_WACOM_TABLET)
	{
		// For tablet style mouse handling we want to reset the mouse to (0,0) as 
		// soon as the user leaves the haptic surface. As we control the mouse up/down 
		// events by measuring the applied force there is a race condition where the 
		// "isTouch" event can be triggered before a mouse up event is sent to Flash. 
		// To deal with situation correctly we'll enqueue the moust reset action if 
		/// a mouse down is in progress and wait until we have sent a mouse up before 
		// moving the mouse to (0,0). 

		if (!touched)
		{
			if (pTex->isMouseDown)
			{
				TRACE(L"Enqueing mouse reset 0,0 action");
				pTex->needMouseReset = true;
			}
			else
			{
				TRACE(L"Reset mouse to 0,0");
				pTex->flash.SendMouseMove(0,0);
			}
		}
	}
	else
	{
		if (touched)
		{
			std::wstring filename;
			filename.assign(
				pTex->pressSoundFilename->getValue().begin(), 
				pTex->pressSoundFilename->getValue().end());

			if (filename.size())
			{
				PlaySoundFile(filename.c_str());
			}

			TRACE(L"Mouse click -> down");
			pTex->flash.SendMouseClick(true);
		}
		else
		{
			std::wstring filename;
			filename.assign(
				pTex->releaseSoundFilename->getValue().begin(), 
				pTex->releaseSoundFilename->getValue().end());
			
			if (filename.size())
			{
				PlaySoundFile(filename.c_str());
			}

			TRACE(L"Mouse click -> up");
			pTex->flash.SendMouseClick(false);

			TRACE(L"Reset mouse to 0,0");
			pTex->flash.SendMouseMove(0,0);
		}
	}
}

void FlashMovieTexture::ContactTexCoordField::onNewValue( const Vec3f &tc ) 
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );
	
	int x = int(tc.x * pTex->width->getValue());
	int y = pTex->height->getValue() - int(tc.y * pTex->height->getValue());
	
	TRACE(L"Texture contact %f %f %f -> mouse move %d %d", tc.x, tc.y, tc.z, x, y);
	
	pTex->flash.SendMouseMove(x,y);
}

void FlashMovieTexture::KeyPressField::onNewValue( const std::string &s )
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	if (s.size() > 0)
	{
		int ascii_key = s[0];

		TRACE(L"Got key press = %d", ascii_key );

		enum { BACKSPACE = 8, TAB = 9, ENTER = 13, ESC = 27, SPACE = 32 };

		switch(ascii_key)
		{
		case BACKSPACE:
			pTex->flash.SendKey(VK_BACK);
			break;
		case TAB:
			pTex->flash.SendKey(VK_TAB);
			break;
		case ENTER:
			pTex->flash.SendKey(VK_RETURN);
			break;
		case ESC:
			pTex->flash.SendKey(VK_ESCAPE);
			break;
		case SPACE:
			pTex->flash.SendChar(' ');
			pTex->flash.SendKey(VK_SPACE);
			break;
		default:
			pTex->flash.SendChar(ascii_key);
			break;
		}
	}
}

void FlashMovieTexture::ActionKeyPressField::onNewValue( const int& v )
{
	FlashMovieTexture* pTex = static_cast< FlashMovieTexture * >( getOwner() );

	TRACE(L"Got action key press = %d", v);

	bool reload = false;

	switch (v)
	{
	case KeySensor::F5:
		reload = true;
		break;
	case KeySensor::HOME:
		pTex->flash.SendKey(VK_HOME);
		break;
	case KeySensor::END:
		pTex->flash.SendKey(VK_END);
		break;
	case KeySensor::PGUP:
		pTex->flash.SendKey(VK_PRIOR);
		break;
	case KeySensor::PGDN:
		pTex->flash.SendKey(VK_NEXT);
		break;
	case KeySensor::LEFT:
		pTex->flash.SendKey(VK_LEFT);
		break;
	case KeySensor::RIGHT:
		pTex->flash.SendKey(VK_RIGHT);
		break;
	case KeySensor::UP:
		pTex->flash.SendKey(VK_UP);
		break;
	case KeySensor::DOWN:
		pTex->flash.SendKey(VK_DOWN);
		break;
	default:
		break;
	}

	if (reload)
	{
		if (pTex->filename->getValue().size())
		{
			pTex->filename->setValue(pTex->filename->getValue());
		}

		if (pTex->url->getValue().size())
		{
			pTex->url->setValue(pTex->url->getValue());
		}
	}
}

H3DNodeDatabase FlashMovieTexture::database( 
	"FlashMovieTexture", 
	&(newInstance< FlashMovieTexture > ),
	typeid( FlashMovieTexture ),
	&X3DTexture2DNode::database 
);

namespace FlashMovieTextureInternals 
{
    FIELDDB_ELEMENT(FlashMovieTexture, pressSoundFilename,          INPUT_OUTPUT );
    FIELDDB_ELEMENT(FlashMovieTexture, releaseSoundFilename,        INPUT_OUTPUT );
    FIELDDB_ELEMENT(FlashMovieTexture, pressForce,                  INPUT_OUTPUT );
    FIELDDB_ELEMENT(FlashMovieTexture, releaseForce,                INPUT_OUTPUT );

    FIELDDB_ELEMENT(FlashMovieTexture, width,                       INPUT_OUTPUT );
    FIELDDB_ELEMENT(FlashMovieTexture, height,                      INPUT_OUTPUT );
	FIELDDB_ELEMENT(FlashMovieTexture, filename,                    INPUT_OUTPUT );
    FIELDDB_ELEMENT(FlashMovieTexture, url,                         INPUT_OUTPUT );

    FIELDDB_ELEMENT(FlashMovieTexture, force,                       INPUT_ONLY   );
    FIELDDB_ELEMENT(FlashMovieTexture, isTouched,                   INPUT_ONLY   );
    FIELDDB_ELEMENT(FlashMovieTexture, contactTexCoord,             INPUT_ONLY   );
	FIELDDB_ELEMENT(FlashMovieTexture, keyPress,					INPUT_ONLY   );
	FIELDDB_ELEMENT(FlashMovieTexture, actionKeyPress,				INPUT_ONLY   );
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Curictus H3D Customization.
///////////////////////////////////////////////////////////////////////////////////////////////////

void SetupCurictusWindowStyle(H3D::GLUTWindow* glwindow)
{
	if (glwindow->fullscreen->getValue())
	{
		glwindow->setFullscreen(true);

		for (int n = 0; n < 10; n++)
		{
			HWND hWnd = ::FindWindow( L"FREEGLUT", L"H3D" );

			if (hWnd) 
			{
				// GLUT will create the rendering window with a normal overlapped style 
				// until the fullscreen call is initiated and a first rendering pass is 
				// performed. To keep things nice and clean we'll forcefully set the 
				// correct window style from the get go.
				LONG nOldStyle = ::GetWindowLong(hWnd, GWL_STYLE);
				LONG nNewStyle = nOldStyle & ~(WS_BORDER | WS_SYSMENU | WS_CAPTION);
				::SetWindowLong(hWnd, GWL_STYLE, nNewStyle);
				break;
			}

			::Sleep(100);
		}

		// The ShowCursor() API maintains a reference count which we have to work 
		// around to forcefully disable the mouse pointer. Since GLUT creates and 
		// initializes the window before we get a chance to modify it to our liking 
		// we have to make several calls to make that our request is acknowledged.
		while (::ShowCursor(FALSE) >= 0)
			;
	}

	//
	// Forcefully disable window minimize/maximize animations via the registry to prevent 
	// extensive flickering when switching between different H3D sessions. H3DLoad.exe 
	// is executed for each activity and will create new OpenGL rendering windows each 
	// time which ruin the user experience a bit due to flickering as Windows tries to 
	// animate the windows.
	//

	HKEY hKey = NULL;

	if (::RegOpenKey(HKEY_CURRENT_USER, L"Control Panel\\Desktop\\WindowMetrics", &hKey) == ERROR_SUCCESS)
	{
		BYTE value[2] = {'0', '\0'};

		::RegSetValueEx(hKey, L"MinAnimate", 0, REG_SZ, value, _countof(value));
		::RegCloseKey(hKey);
	}
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// H3DLoad main() wrapper which takes care of C++ exception handling.
///////////////////////////////////////////////////////////////////////////////////////////////////

// NOTE: Rename the main() in H3DLoad.cpp to h3dmain() in order to use our wrapper. 

int main_wrapper(int argc, char* argv[])
{
	int exitcode = EXIT_SUCCESS;

#if defined(NDEBUG) && !defined(CURICTUS_DEVELOPER_MODE)
	::SetCursorPos(
		::GetSystemMetrics(SM_CXSCREEN), 
		::GetSystemMetrics(SM_CYSCREEN) / 2);
#endif

	BOOL bSceenSaverWasEnabled = FALSE;
	::SystemParametersInfo(SPI_GETSCREENSAVEACTIVE, 0, (PVOID)(&bSceenSaverWasEnabled), 0);

	BOOL bDisable = FALSE;
	::SystemParametersInfo(SPI_SETSCREENSAVEACTIVE, 0, (PVOID)(&bDisable), 0);
	::SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED | ES_DISPLAY_REQUIRED);

	try
	{
		extern int h3dmain(int argc, char* argv[]);

		exitcode = h3dmain(argc, argv);
	}
	catch (const FlashQuitException&)
	{
		TRACE(L"H3DLoad: FlashQuitException");

		exitcode = EXIT_SUCCESS;
	}
	catch (const FlashAbortException&)
	{
		enum { EXIT_MANUALLY = 2 };

		TRACE(L"H3DLoad: FlashAbortException");

		exitcode = EXIT_MANUALLY;
	}
	catch (const H3D::Exception::QuitAPI&) 
	{
		enum { EXIT_MANUALLY = 2 };

		TRACE(L"H3DLoad: QuitAPI");

		exitcode = EXIT_MANUALLY; 
	}
	catch (const H3D::Exception::H3DException& e) 
	{
		TRACE(L"H3DLoad: H3DException: %s", e.message.c_str());

		exitcode = EXIT_FAILURE;
	}
	catch (const std::exception& e)
	{
		TRACE(L"H3DLoad: std::excepcetion: %s", e.what());

		exitcode = EXIT_FAILURE;
	}

#if defined(NDEBUG) && !defined(CURICTUS_DEVELOPER_MODE)
	::SetCursorPos(
		::GetSystemMetrics(SM_CXSCREEN), 
		::GetSystemMetrics(SM_CYSCREEN) / 2);
#endif

	::SystemParametersInfo(SPI_SETSCREENSAVEACTIVE, 0, (PVOID)(&bSceenSaverWasEnabled), 0);
	::SetThreadExecutionState(ES_CONTINUOUS);

#ifdef H3DAPI_LIB
	deinitializeH3D();
#endif

	return exitcode;
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Custom debug handling for release builds..
///////////////////////////////////////////////////////////////////////////////////////////////////

#include "debugtools/AutoCleanup.h"

/// Output synchronization object.
static LockCS g_output;

// Redirect output to this logfile.
static FILE* g_pLogFile = NULL;

void CustomOutputCallback(DWORD dwType, const wchar_t* pwszMessage)
{
	AutoLockCS lock(&g_output);

	SYSTEMTIME st;

	::GetLocalTime(&st);

	if (g_pLogFile)
	{
		switch (dwType)
		{
		case DEBUG_TOOLS_CALLBACK_TRACE_DEBUG:
			fwprintf_s(g_pLogFile, _T("%d-%02d-%02d %02d:%02d:%02d,%03d : Debug: %s\n"), 
				st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, pwszMessage);
			break;
		case DEBUG_TOOLS_CALLBACK_TRACE_WARNING:
			fwprintf_s(g_pLogFile, _T("%d-%02d-%02d %02d:%02d:%02d,%03d : Warning: %s\n"), 
				st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, pwszMessage);
			break;
		case DEBUG_TOOLS_CALLBACK_TRACE_ERROR:
			fwprintf_s(g_pLogFile, _T("%d-%02d-%02d %02d:%02d:%02d,%03d : Error: %s\n"), 
				st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, pwszMessage);
			break;
		default:
			break;
		}

		fflush(g_pLogFile);
	}

#ifdef CURICTUS_DEVELOPER_MODE
	switch (dwType)
	{
		case DEBUG_TOOLS_CALLBACK_TRACE_DEBUG:
			fwprintf_s(stderr, _T("DBG [%04d] %d/%02d/%02d %02d:%02d:%02d: %s\n"),
			           GetCurrentThreadId(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, pwszMessage);
			break;
		case DEBUG_TOOLS_CALLBACK_TRACE_WARNING:
			fwprintf_s(stderr, _T("WRN [%04d] %d/%02d/%02d %02d:%02d:%02d: %s\n"),
			           GetCurrentThreadId(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, pwszMessage);
			break;
		case DEBUG_TOOLS_CALLBACK_TRACE_ERROR:
			fwprintf_s(stderr, _T("ERR [%04d] %d/%02d/%02d %02d:%02d:%02d: %s\n"),
			           GetCurrentThreadId(), st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond, pwszMessage);
			break;
		default:
			break;
	}

	::OutputDebugString(pwszMessage);
	::OutputDebugString(L"\r\n");
#endif
}

void CustomCraschCallback(const wchar_t* pwszErrorMessage)
{
#ifdef CURICTUS_DEVELOPER_MODE
	::MessageBox(HWND_DESKTOP, pwszErrorMessage, L"VRS H3D (DebugTools)", MB_OK|MB_ICONERROR);
#else
	// Release builds are intended to be used as part of a kioskmode setup, 
	// error handling should be silent and thus we won't popup a messagebox 
	// or something similar. In case of a fatal error the details will already 
	// have been logged (including a minidump if possible).
#endif
}

void InitDebugSupport()
{
	//
	// Optionally override and redirect debugging output to logfile.
	//

	const char* pszLogFilename = getenv("H3D_DEBUGTOOLS_FILENAME");

	if (pszLogFilename)
	{
		g_pLogFile = _fsopen(pszLogFilename, "at", _SH_DENYNO);
	}

	DebugTools::Install(CustomOutputCallback, CustomCraschCallback);

	//
	// Optionally override default directory where minidumps will be saved.
	//

	const char* pszMinidumpStoragePath = getenv("H3D_DEBUGTOOLS_MINIDUMP_PATH");

	if (pszMinidumpStoragePath)
	{
		std::wstring ws;

		ws.assign(pszMinidumpStoragePath, pszMinidumpStoragePath + strlen(pszMinidumpStoragePath));

		DebugTools::SetMinidumpStoragePath(ws);
	}
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// VRS (H3D) entry-point.
///////////////////////////////////////////////////////////////////////////////////////////////////


int main(int argc, char* argv[])
{
#ifdef NDEBUG
	InitDebugSupport();
#endif

	return main_wrapper(argc, argv);
}

///////////////////////////////////////////////////////////////////////////////////////////////////
// Override default H3DLoad entry-point with our own wrapper.
///////////////////////////////////////////////////////////////////////////////////////////////////

#define main h3dmain

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////
