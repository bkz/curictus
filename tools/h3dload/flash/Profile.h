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

#ifndef CURICTUS_PROFILE_H
#define CURICTUS_PROFILE_H

///////////////////////////////////////////////////////////////////////////////////////////////////
// Precision timer.
///////////////////////////////////////////////////////////////////////////////////////////////////

struct Timer
{
	static double GetTicks()
	{
		static bool initialized = false;
		static __int64 basetime  = 0;
		static __int64 frequency = 0;

		if (!initialized)
		{
			::QueryPerformanceFrequency((LARGE_INTEGER*)(&frequency));
			::QueryPerformanceCounter((LARGE_INTEGER*)(&basetime));

			initialized = true;
		}

		__int64 currtime;
		
		::QueryPerformanceCounter((LARGE_INTEGER*)(&currtime));

		return 1000.0f * (double(currtime) - double(basetime)) / double(frequency);
	}
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// Sampling profiler (averages 32 latest inputs).
///////////////////////////////////////////////////////////////////////////////////////////////////

struct Profile
{
	enum { PROFILE_PERIOD_MS = 2000 };

	Profile(const char *_name, bool _fps=false) 
		: name(_name), fps(_fps)
	{
		nextprint = Timer::GetTicks() + PROFILE_PERIOD_MS;
	}

	void update(double elapsed)
	{
		values.push_back(elapsed);

		double current = Timer::GetTicks();

		if (current > nextprint)
		{
			double kmin = 1000.0f;
			double kmax = 0.0f;

			double sum  = 0;

			for (size_t i = 0; i < values.size(); i++)
			{	
				double v = values[i];
				kmin = min(kmin, v);
				kmax = max(kmax, v);
				sum += v;
			}	

			double avg = sum / values.size();

			if (fps)
			{
				TRACE(L"-> %-10s : %7.2f%7.2f%7.2f (fps)", 
					name, 1000.0f / avg+0.01f, 1000.0f / kmin+0.01f, 1000.0f / kmax+0.01f);
			}
			else
			{
				TRACE(L"-> %-10s : %7.2f%7.2f%7.2f (ms)", 
					name, avg, kmax, kmin);
			}

			nextprint = current + PROFILE_PERIOD_MS;

			values.clear();
		}
	}

	const char*			name;
	bool				fps;
	std::vector<double>	values;
	double				nextprint;
};

///////////////////////////////////////////////////////////////////////////////////////////////////
// Scoped profiler (measures time spent in a block).
///////////////////////////////////////////////////////////////////////////////////////////////////

struct AutoProfile
{	
	AutoProfile(Profile* _target) : target(_target)
	{	
		start = Timer::GetTicks();
	}	

	~AutoProfile()
	{	
		target->update(Timer::GetTicks() - start);
	}	

	double		start;
	Profile*	target;
};

#define PROFILE(name) static Profile _profile(#name);AutoProfile _sample(&_profile);

///////////////////////////////////////////////////////////////////////////////////////////////////
// Global FPS timer.
///////////////////////////////////////////////////////////////////////////////////////////////////

struct ProfileFPS
{	
	ProfileFPS() : profile("frame", true)
	{	
		start = Timer::GetTicks();
	}	

	void update()
	{	
		double current = Timer::GetTicks() - start;
		double elapsed = current - lastframe;

		if (lastframe > 0)
		{
			profile.update(elapsed);
		}

		lastframe = current;
	}	

	double  start;
	double  lastframe;
	Profile	profile;
};

#define PROFILE_FPS() static ProfileFPS _profile;_profile.update();

///////////////////////////////////////////////////////////////////////////////////////////////////
// The End.
///////////////////////////////////////////////////////////////////////////////////////////////////

#endif // CURICTUS_PROFILE_H