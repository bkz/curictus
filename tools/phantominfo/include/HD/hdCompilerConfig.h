/*****************************************************************************

Copyright (c) 2004 SensAble Technologies, Inc. All rights reserved.

OpenHaptics(TM) toolkit. The material embodied in this software and use of
this software is subject to the terms and conditions of the clickthrough
Development License Agreement.

For questions, comments or bug reports, go to forums at: 
    http://dsc.sensable.com
  
Module Name:

    HdCompilerConfig.h
    
Description: 

    Windows-specific compiler flags.

******************************************************************************/

#ifndef HD_COMPILERCONFIG_H_DEFINE
#define HD_COMPILERCONFIG_H_DEFINE

#if defined(WIN32)
#  include <windows.h>
#endif /* WIN32 */

#if defined(linux) || defined(__APPLE__)
#  if !defined(TRUE)
#     define TRUE 1
#  endif
#  if !defined(FALSE)
#     define FALSE 0
#  endif
#  if !defined(max)
#     define max(a,b) (((a) > (b)) ? (a) : (b))
#  endif
#  if !defined(min)
#     define min(a,b) (((a) < (b)) ? (a) : (b))
#  endif
#  if !defined(MB_OK)
#     define MB_OK 0
#  endif
#  if !defined(Sleep)
#     define Sleep(x) usleep((x) * 1000)
#  endif
#endif /* linux || __APPLE__ */

#if defined(__APPLE__)
#     include <TargetConditionals.h>
#endif /* __APPLE__ */

#endif /* HD_COMPILER_CONFIG_H_DEFINE */

/******************************************************************************/
