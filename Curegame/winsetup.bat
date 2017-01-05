@echo off

echo Rotate Screen 180 degrees
%~dp0\bin\display.exe /rotate:180

echo Rebuild icon cache
taskkill /F /IM explorer.exe  
cd /d %userprofile%\AppData\Local 
del /f IconCache.db  
start explorer.exe

echo Setup custom logon background
mkdir %windir%\System32\oobe\info\backgrounds
copy /Y %~dp0\media\wallpapers\winlogon.jpg %windir%\System32\oobe\info\backgrounds\backgroundDefault.jpg

echo Clear Internet Explorer Cache
RunDll32.exe InetCpl.cpl,ClearMyTracksByProcess 255 

echo Disable Disk Defragmenter
sc config defragsvc start= disabled

echo Disable Printer Spooler
sc config Spooler start= disabled

echo Disable Security Center
sc config wscsvc start= disabled

echo Disable Superfetch
sc config SysMain start= disabled

echo Disable Windows Defender
sc config WinDefend start= disabled

echo Disable Windows Media Player Network Sharing
sc config WMPNetworkSvc start= disabled

echo Disable Windows Search
sc config WSearch start= disabled

echo Disable Windows Update
sc config wuauserv start= disabled

echo Apply Custom Registry changes
reg import %~dp0\winsetup.reg

echo Setup Cygwin SSHD (import accounts and restart)
net stop sshd
C:\Cygwin\bin\mkgroup.exe  --local > C:\Cygwin\etc\group
C:\Cygwin\bin\mkpasswd.exe --local > C:\Cygwin\etc\passwd
net start sshd
