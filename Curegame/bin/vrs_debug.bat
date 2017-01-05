@echo off
set PATH=%PATH%;%~dp0;%~dp0\..\h3d\bin;%~dp0\..\h3d\External\bin;%~dp0\..\python
set H3D_EXTERNAL=%~dp0\..\h3d\External
set H3D_ROOT=%~dp0\..\h3d\H3DAPI
set PYTHONHOME=%~dp0\..\python
cd %~dp1
vrs_debug.exe %* --no-fullscreen --no-mirror --rendermode=MONO
pause
