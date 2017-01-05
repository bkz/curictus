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

# Standardized Pointtest ("Pricktest")
# Copyright Curictus AB

import hgt
from hgt.utils import *
from hgt.nodes import *
from H3DInterface import * # Vec3f() ...
from hgt.listeners import * # ForceListener()
from hgt.gameelements import * # Sound()
import hgt.game

# Settings - do not change unless absolutely necessary.
# Important to maintain fixed order and position for comparison.

# Original target order and coordinates.
# There should be 32 target positions / 31 inter-target motions.

TARGET_ORDER = [ 1, 9, 3, 7, 8, 6, 1, 8, 3, 2, 5, 4, 6, 3, 9, 2, 7, 5, 9, 1, 7, 9, 8, 5, 7, 3, 8, 1, 4, 9, 7, 1] #, 2 ]

TARGET_COORDINATES = [
  (-10.00, 10.000,  0.000), # "Hidden" location (not used here)	
  ( 0.09, -0.095, -0.015),	
  ( 0.00, -0.095,  0.040),	
  (-0.09, -0.095,  0.030),	
  (-0.09, -0.030,  0.000),	
  ( 0.00, -0.030, -0.050),	
  ( 0.09, -0.030,  0.030),	
  ( 0.09,  0.035,  0.015),	

  # Altered position of this target - was too far in to reach
  #(   0.00,  0.035, -0.040 ),
  ( 0.00,  0.035,  0.030),
    
  (-0.09,  0.035, -0.030),
]

# Required activation pressure, Newtons
TARGET_PRESSURE = 0.5

TARGET_DELAY = 0.100
START_DELAY = 0.5
POST_DELAY = 2.0
TOUCH_DELAY = 0.2

class Game(hgt.game.Game):
    def build(self):
        self.world = X3DFileNode("world.x3d")
        self.add_node(self.world)

        self.build_starter()
        self.build_targets()

        self.dingSound = Sound("../../../media/sounds/ding.wav")
        self.clickSound = Sound("../../../media/sounds/click.wav")

        self.log_event("init", "Pointtest initialized")

        # Debug: target changer
        #hgt.keyboard.bind_key(key = "a", onPress = self.next_target, noEvent = True)

    def start(self):
        self.log_event("show_start", "Show start button")

        self.startButtonToggle.hapticsOn = True
        self.startButtonToggle.graphicsOn = True
       
        #self.dingSound.play()

    def update(self):
        pass

    # Events sent from ForceListeners
    def start_button_press(self):
        # Remove listener
        self.startButtonMesh.h3dNode.force.unroute(self.startButtonListener)

        self.startButtonToggle.hapticsOn = False
        self.startButtonToggle.graphicsOn = False

        self.log_event("press_start", "Press start button")
        self.startTime = hgt.time.now

        self.clickSound.play()

        # Display first target
        hgt.time.add_timeout(START_DELAY, self.next_target)
    
    def press_target(self):
        if not self.targetLocked:
            self.targetMat.diffuseColor = RGB(1, 1, 0)
            self.clickSound.play(location = hgt.haptics.trackerPosition)
            self.log_event("press_target", "Press target %02d" % self.targetCounter, target=self.targetCounter)
            self.targetLocked = True
            
            hgt.time.add_timeout(TOUCH_DELAY, self.next_target)
            # self.next_target()
            
    def next_target(self):
        # Disable further force events
        self.targetLocked = True

        self.targetToggle.graphicsOn = False
        self.targetToggle.hapticsOn = False
        self.shadowToggle.graphicsOn = False

        # Hide and move target
        if len(self.targetIndices) > 0:
            self.targetCounter += 1
            
            targetIndex = self.targetIndices.pop(0)
            targetPosition = self.targetCoords[targetIndex]

            self.target.translation = self.targetCoords[targetIndex]

            # Update shadow xz position
            self.targetShadow.translation = Vec3f(
                self.target.translation.x,
                self.targetShadow.translation.y,
                self.target.translation.z
            )

            # Schedule target display
            hgt.time.add_timeout(TARGET_DELAY, self.display_target)

        # Trial done
        else:
            self.log_event("completed", "Trial completed")
            self.targetMesh.h3dNode.force.unroute(self.forceListener)
            hgt.time.add_timeout(POST_DELAY, self.post_trial)
            
    def display_target(self):
        self.targetMat.diffuseColor = RGB(0, 0.9, 0)
        self.targetToggle.graphicsOn = True
        self.targetToggle.hapticsOn = True
        self.shadowToggle.graphicsOn = True
        self.targetLocked = False
        self.log_event("show_target", "Show target %02d" % self.targetCounter, target=self.targetCounter)

    def post_trial(self):
        self.log_event("quit", "Pointtest quit")
        self.log_info("target_count", "Target count %d" % self.targetCounter, count=self.targetCounter)

        # Record trial duration (for menu graph display)
        self.set_result('min_result', 0.0)  # Bug: need to set for correct graph scaling
        self.set_result('max_result', 60.0) # - " - 
        self.set_result('result_type', 'min_time')
        self.set_result('result', hgt.time.now - self.startTime)
         
        self.quit()

    def build_targets(self):
        targetNode = X3DNode("""\
<Group>
<ToggleGroup DEF="TOGGLE" >
 <Transform  DEF="TRANSFORM" translation="0.09 -0.095 0.0" scale="0.6 0.6 0.6"
 rotation="1.0 0.0 0.0  1.57">
   <Shape >
      <Appearance >
         <Material DEF="BUTMAT" diffuseColor="0.0 0.7 0.0"
         emissiveColor="0 0 0"/>
         <Material transparency="1" />
         <FrictionalSurface />
      </Appearance>
     <Cylinder DEF="GEOMETRY" radius="0.023" height="0.001" 
     bottom="true" side="true"/>
   </Shape>
 
   <Transform  scale="1 0.2 1">
   <Shape >
      <Appearance >
         <Material USE="BUTMAT" />
      </Appearance>
     <Sphere radius="0.023" />
   </Shape>
   </Transform>

   <Transform  translation="0 -0.005 0">
       <Shape >
          <Appearance >
             <Material diffuseColor="1 0 0" transparency="1" />
             <FrictionalSurface />
          </Appearance>
         <Cylinder radius="0.023" height="0.008" 
         bottom="true" side="true"/>
       </Shape>
   </Transform>
 </Transform>
</ToggleGroup>
</Group>
""")
        self.add_child(targetNode)
        self.targetToggle = targetNode.find("TOGGLE")
        self.target = targetNode.find("TRANSFORM")
        self.targetMat = targetNode.find("BUTMAT") 
        
        self.targetToggle.graphicsOn = False
        self.targetToggle.hapticsOn = False
        
        self.shadowToggle = hgn.ToggleGroup(graphicsOn = False, hapticsOn = False)
        self.targetShadow = self.world.find("TargetShadow")
        self.targetShadow.reparent(self.shadowToggle)

        # Make target listen for forces exceeding TARGET_PRESSURE
        self.targetMesh = targetNode.find("GEOMETRY")
        self.forceListener = ForceListener(
            callbackObject = None,
            callback = self.press_target,
            hitForce = TARGET_PRESSURE
        )
        self.targetMesh.h3dNode.force.routeNoEvent(self.forceListener)

        self.targetLocked = False

        # Target order and positions
        self.targetIndices = TARGET_ORDER
        self.targetCoords = []
        self.targetCounter = 0

        for c in TARGET_COORDINATES:
            # Calibration Correction
            v = Vec3f(c[0], c[1], c[2])
            cv = v + Vec3f(0, 0, 0)
            self.targetCoords.append(
                cv
            )

    def build_starter(self):
        startButton = self.world.find("StartButton")
        self.startButtonToggle = hgn.ToggleGroup(graphicsOn = False, hapticsOn = False)
        startButton.reparent(self.startButtonToggle)
        
        self.startButtonListener = ForceListener(
            callbackObject = None,
            callback = self.start_button_press,
            hitForce = TARGET_PRESSURE
        )
        
        self.startButtonMesh = self.world.find("ME_StartButton")
        self.startButtonMesh.h3dNode.force.routeNoEvent(self.startButtonListener)
