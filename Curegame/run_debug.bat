@echo off
set CUREGAME_OPT_DEBUG=1
:loop
%~dp0\python\python.exe bootstrap.py
echo ------------------------------------------------------------
echo Python Session Restarting!
echo ------------------------------------------------------------
%~dp0\bin\sleep 2
goto loop
