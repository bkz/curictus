@echo off
chdir /d %~dp0
echo Install VRS
%~dp0\python\python.exe %~dp0\bootstrap.py install
echo Register sync scheduled task
schtasks /f /create /sc minute /mo 30 /tn "vrssync" /tr "%~dp0\python\pythonw.exe %~dp0\bootstrap.py sync"
echo Register reboot scheduled task
schtasks /f /create /sc daily /tn "vrsrestart" /st 23:59:00 /tr "shutdown.exe /r /t 30 /f"
echo Setup legacy MySQL DB
"C:\Program Files (x86)\MySQL\MySQL Server 5.0\bin\mysql.exe" -u root -proot        < %~dp0\legacy\create.sql
"C:\Program Files (x86)\MySQL\MySQL Server 5.0\bin\mysql.exe" -u root -proot crs_db < %~dp0\legacy\database.sql
echo Done!

