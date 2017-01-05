This directory contains code and binaries for a special build of H3DLoad.exe which is part of the H3D 2.0 SDK. In order to build the project in the vcbuild/ folder it is assumed that H3D is installed to C:\H3D or else the build will fail. If you wish to generate a new set of .vproj files installed the CMake build tools and use the C:\H3D\H3DAPI\H3DLoad\build\CMakeLists as the build source.

VRS related modification are self-contained in VRS.cpp which is injected into H3DLoad.cpp. Some minor modication were made to H3DLoad.cpp which you can view by diffing H3DLoad.cpp against H3DLoadOrig.cpp which is the version included in the H3D SDK.

Note: When making changes to H3dLoad.cpp make sure to perform a batch-build to build both the normal "vrs.exe" as well as the developer version "vrs_debug.exe" is configured to have a console window for viewing stdout/stderr output.

Changes made to H3DLoad.exe include:

- automatically set HKEY_CURRENT_USER\Control Panel\Desktop\WindowMetrics\MinAnimate=0 to disable window animations
- disable <ESC> for exiting scenes (since it's handled in a more general fashion by VRS itself)
- return code now allows callee to differentiate between 0=normal, 1=crash, 2=forced exits
- capture all SEH exceptions to keep Windows from displaying the Dr. Watson dialog
- suppress all unhandled errors and exception to keep Dr.Watson from showing dialog boxes
- support for logging raw device data from haptic devices (HapticDataLogger X3D node).
- support for tracking total distance traveled of the attached haptic device pen (HapticDeviceStats X3D node)
- support for exposing most of the relevant haptic device values via the HapticDeviceStats X3D Node (see below)
- added a custom X3D node <AbortIfUserIdle /> which terminates the session if no movement is detected for 10 minutes
- added a custom X3D texture <FlashMovieTexture /> which allows users to view and interact with Flash movies in 3D.

========================
Device data logging
========================

Add the <HapticDeviceLogger /> node to your X3D scene and set the environment variable H3D_DEVICELOG_FILENAME to a filename or either "stdout" or "stderr" to output device data in XML format. The device position and orientation (vec3f) is reported as raw values from the device. Separate calibration matrices are used to adjust both the position and orientation coordinates into what is known as the tracker position and orientation.

Note: The device data is downsampled from 1000 hz to 60 hz! 

The following is an example of how the device data output looks like.

<deviceinfo>
  <calibration>
    <position>1.000000,0.000000,0.000000,0.000000,0.000000, ...</position>
    <orientation x="1.000000" y="0.000000" z="0.000000" a="0.915263" />
  </calibration>
</deviceinfo>
<event timestamp="0.198370">
 <position x="0.084311" y="-0.092544" z="-0.027273" />
 <orientation x="0.416861" y="0.521564" z="0.744444" a="1.680742" />
 <force x="0.000000" y="0.000000" z="0.000000" />
 <velocity x="0.000000" y="0.000000" z="0.000000" />
</event>
<event timestamp="0.219371">
 <position x="0.084311" y="-0.092544" z="-0.027273" />
 <orientation x="0.417496" y="0.521176" z="0.744361" a="1.680118" />
 <force x="0.000000" y="-0.000000" z="-0.000000" />
 <velocity x="0.000000" y="0.000000" z="0.000000" />
</event>
...
...
...

========================
Haptic device stats
========================

To access raw values and measurements from the Python script "test.py" add the following block to your X3D scene (note the HapticDeviceLogger node is required):

Note: You need to check the "active" field of the HapticDeviceStats node to make sure that the node has valid data. This only used during the initialization period so you only need to check it during first N calls tro traverseSG() where N usually = 2. The reason for this is that the device data reader hooks into force feedback system of H3D where our callback isn't called during the first N rendered frames, after that everything works as you'd expect.

<HapticDeviceLogger />
<PythonScript DEF="PS" url="test.py" >
  <HapticDeviceStats containerField="references" />
</PythonScript>

In the Python script use the following code to access the data:

data = references.getValue()[0]
print "active       : ", data.active.getValue()
print "force        : ", data.force.getValue()
print "torque       : ", data.torque.getValue()
print "position     : ", data.position.getValue()
print "velocity     : ", data.velocity.getValue()
print "orientation  : ", data.orientation.getValue()
print "button1      : ", data.button1.getValue()
print "button2      : ", data.button2.getValue()
print "button3      : ", data.button3.getValue()
print "button4      : ", data.button4.getValue()
print "timestamp    : ", data.timestamp.getValue()
print "distance     : ", data.distance.getValue()
    
========================
Flash movie texture
========================

There a two ways in which you can integrate a realtime Flash movie texture in your H3D scene:

1. Passive, texture is updated in realtime and is rendered by H3D but the user can't interact with the Flash movie.

2. Active, in addition to being updated and rendered in realtime, the isTouched and force fields are routed to the texture in order emulate mouse handling. For example you could apply the texture onto a Rectangle and simulate touch surface.

Have a look at the flash.x3d and flash.py in the "bin" folder for a real example.
