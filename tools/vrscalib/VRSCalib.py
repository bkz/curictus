##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
#
# This file part of Curictus VRS.
#
# Curictus VRS is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Curictus VRS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Curictus VRS; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#
##############################################################################

from H3D import *
from H3DInterface import *
import math

from numpy import resize, array, dot
from optimize import fmin

# Angles in degrees measured relative to the table (xz plane)
# See Documentation folder for explanation of variables
SCREEN_ANGLE = 45.0 # Positive direction up
MIRROR_ANGLE = 10.0 # Positive direction down

SCREEN_HEIGHT = 0.30
SCREEN_DISTANCE = 0.50
INTEROCULAR_DISTANCE = 0.06

# Measurements for calculating virtual origo

# Original monitor placement, 10 degree tilt
#SCREEN_MIRROR_INTERSECTION = 0.26
#SCREEN_TABLE_HEIGHT = 0.57

# Monitor moved 6 cm closer to mirror perpendicular to mounting bar, 10 degree tilt
SCREEN_MIRROR_INTERSECTION = 0.21
SCREEN_TABLE_HEIGHT = 0.52

# Model files
STYLUSFILE = "omni_stylus.x3d"

BRICK_HEIGHT = 0.0194
RADIANS_PER_DEGREE = math.pi / 180.0
NUDGE_INC = 0.005

# Globals
TEXT_LABEL = MFString()
TEXT_LABEL.setValue(["Place the virtual stylus and press <Space>, or <H> for Help."])

class InputListener(AutoUpdate(SFString)):
    def __init__(self, ctrl):
        AutoUpdate(SFString).__init__(self)

        self.ctrl = ctrl

        self.screenHeight = SCREEN_HEIGHT 

        self.dx = 0.0
        self.dy = 0.0
        self.dz = SCREEN_DISTANCE 
        self.calculate_viewpoint()

    def update(self, event):
        key = event.getValue()

        """
        if key == '+':
            self.dz += NUDGE_INC
            self.calculate_viewpoint()
            self.show_viewpoint_info()

        elif key == '-':
            self.dz -= NUDGE_INC
            self.calculate_viewpoint()
            self.show_viewpoint_info()
        """

        if key == ' ':
            self.ctrl.set_virtual()

        elif key == 'b':
            self.ctrl.set_real()
        
        elif key == 'c':
            self.ctrl.calibrate()

        elif key == 'w':
            self.ctrl.write_files()

        elif key == 'z':
            self.ctrl.undo_last_sample()
        
        elif key == 'h':
            TEXT_LABEL.setValue([
                "<H> - Show help",
                "<Space> - Place virtual stylus",
                "<B> - Place real stylus",
                "<C> - Calibrate",
                "<W> - Write device/viewpoint files",
                "<Z> - Undo last sample (repeatable)",
            ])

        return key

    def calculate_viewpoint(self): 
        self.fov = 2 * math.atan(0.5 * self.screenHeight / self.dz) 
        self.ctrl.viewpoint.position.setValue(Vec3f(self.dx, self.dy, self.dz))
        self.ctrl.viewpoint.fieldOfView.setValue(self.fov)
        self.ctrl.stereoinfo.interocularDistance.setValue(INTEROCULAR_DISTANCE)
        self.ctrl.stereoinfo.focalDistance.setValue(self.dz)

    def show_viewpoint_info(self):
        TEXT_LABEL.setValue(
            ["Viewpoint dist (z): %.3f fov: %.2f" % (self.dz, self.fov)]
        )

class Origizer:
    """ Calculate the virtual origo relative to the table """
    def __init__(self):
        self.screenAngle = SCREEN_ANGLE * RADIANS_PER_DEGREE
        self.mirrorAngle = MIRROR_ANGLE * RADIANS_PER_DEGREE
        
        # Distance from the middle of the screen to intersection with
        # mirror plane, measured parallel to the screen.
        self.origoDist = SCREEN_MIRROR_INTERSECTION

        # Distance straight down from the middle of the screen to the table
        # (perpendicular with table)
        self.origoHeight = SCREEN_TABLE_HEIGHT

        self.calculate_origo()

    def calculate_origo(self):
        origoProj = self.origoDist * math.sin(self.screenAngle + self.mirrorAngle)
        oz = 2 * origoProj * math.sin(self.mirrorAngle)
        x = 2 * origoProj * math.cos(self.mirrorAngle)
        oy = self.origoHeight - x

        self.origo = Vec3f(0, oy, oz)

    def dump(self):
        print "Virtual origo at y: %f z: %f" % (self.origo.y, self.origo.z)
        print "Virtual origo length:", self.origo.length()

class VRSCalib:
    def __init__(self):
        root, = references.getValue()

        origizer = Origizer()
        origizer.dump()

        self.group = createX3DNodeFromString('<Group />')[0]
        root.children.push_back(self.group)

        # Create Viewpoint
        self.viewpoint = createX3DNodeFromString("<Viewpoint />")[0]
        root.children.push_back(self.viewpoint)
        self.stereoinfo = createX3DNodeFromString("<StereoInfo />")[0]
        root.children.push_back(self.stereoinfo)

        # This is ugly, but it's Friday afternoon!
        self.viewpointInfo = inputListener = InputListener(self)
       
        # Keyboard listener
        ks = createX3DNodeFromString("<KeySensor />")[0]
        root.children.push_back(ks)
        ks.keyPress.route(inputListener)
        
        # Get haptic device handle (assumption: only one haptic device used)
        di = getActiveDeviceInfo()
        self.dev = di.device.getValue()[0]

        # Init calibration vars
        self.virtualStylusPlaced = False
        self.calibrated = False

        self.Ap = []
        self.Bp = []
        self.Ar = []
        self.Br = []

    def set_virtual(self):
        if not self.virtualStylusPlaced:
            TEXT_LABEL.setValue(["Now place real stylus in the same location and press <B>."])
            
            stylusFile = open(STYLUSFILE, 'rb')
            virtualStylus = createX3DNodeFromString(stylusFile.read())[0]
            stylusFile.close()

            pos = self.dev.trackerPosition.getValue()
            ori = self.dev.trackerOrientation.getValue()

            virtualStylus.translation.setValue(pos)
            virtualStylus.rotation.setValue(ori)
            self.add_node(virtualStylus)

            self.Ap.append([pos.x, pos.y, pos.z, 1])
            self.Ar.append(Quaternion(ori))

            self.virtualStylusPlaced = True
    
    def set_real(self):
        if self.virtualStylusPlaced:
            TEXT_LABEL.setValue(["Place virtual stylus and press <Space>. <C> Calibrates."])
            
            pos = self.dev.trackerPosition.getValue()
            ori = self.dev.trackerOrientation.getValue()

            self.clear_group()

            self.Bp.append([pos.x, pos.y, pos.z, 1])
            self.Br.append(Quaternion(ori))
            
            self.virtualStylusPlaced = False

    def calibrate(self):
        if not self.virtualStylusPlaced:
            TEXT_LABEL.setValue(["Please wait..."])
            T = self.solvePos()
            M = Matrix4f( T[ 0], T[ 1], T[ 2], T[ 3],
                    T[ 4], T[ 5], T[ 6], T[ 7],
                    T[ 8], T[ 9], T[10], T[11],
                    0 ,    0 ,    0 ,    1 )

            M = M.inverse() * self.dev.positionCalibration.getValue()
            self.dev.positionCalibration.setValue(M)
            self.matrix = M

            T = self.solveRot()
            axis = Vec3f( T[0], T[1], T[2] )
            angle = axis.length()
            axis = axis / angle
            R = Rotation( axis, angle )

            R = (-R) * self.dev.orientationCalibration.getValue()
            self.dev.orientationCalibration.setValue(R)
            self.rotation = R

            self.Ap = []
            self.Bp = []

            self.Ar = []
            self.Br = []
            
            self.calibrated = True
            TEXT_LABEL.setValue(["Calibrated. Place virtual stylus and press <Space>. <W> writes files."])

    def write_files(self):
        if self.calibrated:
            fh = open('device.txt', 'wb')
            fh.write("""
<DeviceInfo>
    <PhantomDevice
        orientationCalibration="%s"
        positionCalibration="%s"
    >
        <OpenHapticsRenderer/>
    </PhantomDevice>
</DeviceInfo>
            """ % (self.rotation, self.matrix))
            fh.close()

            fh = open('viewpoint.txt', 'wb')
            fh.write("""
<Group>
  <Viewpoint position="0.0 0.0 %s" fieldOfView="%s" />
  <StereoInfo focalDistance="%s" />
</Group>
            """ % (self.viewpointInfo.dz, self.viewpointInfo.fov, self.viewpointInfo.dz))
            fh.close()
            TEXT_LABEL.setValue(["Files written. Place virtual stylus and press <Space>."])

    def funcPos(self,x):
        M = resize(x,(4,4))
        M[3][0] = M[3][1] = M[3][2] = 0
        M[3][3] = 1
        
        sum = 0
        for i in range(len(self.Ap)):
          
          ap = array(self.Ap[i])
          bp = array(self.Bp[i])
          
          a2 = dot( M, ap );
          
          d = bp - a2
          dL = dot( d, d )
          sum = sum + dL
        
        return sum

    def solvePos(self):
        M = fmin( self.funcPos, [ 1.0, 0.1, 0.1, 0.1,
                                  0.1, 1.0, 0.1, 0.1,
                                  0.1, 0.1, 1.0, 0.1 ],
                  (), 0.00001, 0.00001,
                  100000, 100000, 0, 0, 0 )
        return M
  
    def funcRot(self,x):
        axis = Vec3f( x[0], x[1], x[2] )
        angle = axis.length()
        axis = axis / angle
        
        R = Quaternion( Rotation( axis, angle ) )
        
        sum = 0
        for i in range(len(self.Ar)):
          
          ar = self.Ar[i]
          br = self.Br[i]
          
          sum = sum + Rotation( br.conjugate() * ( R * ar ) ).a
          
        return sum
      
    def solveRot(self):
        M = fmin( self.funcRot, [ 1.0, 1.0, 1.0 ],
                  (), 0.00001, 0.00001,
                  100000, 100000, 0, 0, 0 )
        return M

    def add_node(self, n):
        self.group.children.push_back(n)

    def clear_group(self):
        self.group.children.setValue([])

    def undo_last_sample(self):
        if not self.virtualStylusPlaced and len(self.Ap) > 0:
            self.Ap = self.Ap[:-1]
            self.Bp = self.Bp[:-1]
          
            self.Ar = self.Ar[:-1]
            self.Br = self.Br[:-1]
          
            bricks = self.group.children.getValue()
            self.group.children.setValue( bricks[:-2] )
            TEXT_LABEL.setValue(["Sample %d undone. Place virtual stylus and press <Space>." % (len(self.Ap) + 1,)])


vrsc = VRSCalib()
