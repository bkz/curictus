Note: You need a config.cfg in this folder to run VRS. It needs to at least
contain a ZONE_GUID, STATION_GUID and a STATION_ALIAS (see Config class in
./modules/vrs/config/__init__.py). UUIDs should be generated as
str(uuid.uuid4()) using the uuid module from the Python standard library.

Sample config:

ZONE_GUID      = 'fy3438b7-faaf-41a5-9ee9-2affd18061e8'
STATION_GUID   = '44f42b66-586a-4957-a571-be3a449b5b32'
STATION_ALIAS  = 'dev1'

Batch files:

./run.bat         => Run VRS client in release mode
./run_debug.bat   => Run VRS client in developer mode (no dashboard etc)
./run_server      => Run VRS server locally
./run_sync.bat    => Force a VRS sync (ping the server)

./install.bat     => Executed by CUP or manually (elevatated, UAC)
./uninstall.bat   => Executed by CUP or manually (elevatated, UAC)
./winsetup.bat    => Executed as part of install.bat

./test_func.bat   => Run tests in ./tests/func_hgt and ./tests/func_vrs
./test_unit.bat   => Run tests in ./tests/unit_hgt and ./tests/unit_vrs
