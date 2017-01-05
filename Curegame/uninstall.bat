@echo off
chdir /d %~dp0
echo Uninstall VRS
%~dp0\python\python.exe %~dp0\bootstrap.py uninstall
echo Unregister sync scheduled task
schtasks /f /delete /tn "vrssync"
echo Uninstall reboot scheduled task
schtasks /f /delete /tn "vrsrestart"
echo Delete legacy MySQL DB
"C:\Program Files (x86)\MySQL\MySQL Server 5.0\bin\mysql.exe" -u root -proot        < %~dp0\legacy\create.sql
