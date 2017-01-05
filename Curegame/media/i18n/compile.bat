set PATH=%~dp0\..\..\..\tools\gettext-0.14.4\bin;%PATH%;
%~dp0\..\..\python\python.exe compile.py ../../../flex/ ../../activities/ ../../modules ../html
pause