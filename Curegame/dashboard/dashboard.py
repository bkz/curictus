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

from H3DInterface import *

###########################################################################
# Helper field classes.
###########################################################################

class ContactTexCoord( TypedField( SFVec3f, MFVec3f ) ):
  """
  Helper field which filters out the contact texture coords from the first
  device and also record the values to the class variables `x` and `y`.
  """
  x = 0.0
  y = 0.0
  def update( self, event ):
    tex_coords = event.getValue()
    if( len(tex_coords) > 0 ):
      self.x = tex_coords[0].x
      self.y = tex_coords[0].y
      return tex_coords[0]
    else:
      return Vec3f( 0, 0, 0 )

class Force( TypedField( SFVec3f, MFVec3f ) ):
  """
  Helper field which filters out the force vector from the first device.
  """
  def update( self, event ):
    f = event.getValue()
    if( len(f) > 0 ):
      return f[0]
    else:
      return Vec3f( 0, 0, 0 )

class IsTouched( TypedField( SFBool, MFBool ) ):
  """
  Helper field which filters out the touched property from the first device.
  """
  def update( self, event ):
    values = event.getValue()
    if( len(values) > 0 ):
      return values[0]
    else:
      return False

class ToggleHaptics( TypedField( SFBool, SFVec3f ) ):
  """
  Field which is used toggle haptics on/off depending on the tracker
  position. We use it to simulate a haptic hole/well in the lower area
  of the geometry which disable haptics as soon as you enter the area. Leaving
  the area results in haptics being turned on again.
  """
  insideHole = False
  def update( self, event ):
    pos = event.getValue()
    if( pos ):
      if pos.z > 0.03:
          self.insideHole = False
          return True
      else:
          if pos.z <= 0.0 and contactTexCoord.y < 0.17:
            self.insideHole = True
            return False
          else:
            self.insideHole = False
            return True
    else:
      return True

class ToggleTransparency( TypedField( SFFloat, SFVec3f ) ):
  """
  Field which is used together with ToggleHaptics node to toggle transparency
  of X3D nodes when the tracker enters "haptic hole/well".
  """
  def update( self, event ):
    pos = event.getValue()
    if( pos ):
      if toggleHaptics.insideHole and pos.z <= -0.02:
        return 0.25
      else:
        return 0.0
    else:
      return 0.0

class ShadowTranslation( TypedField( SFVec3f, SFVec3f ) ):
  """
  Set shadow position based on tracker.
  """
  def update( self, event ):
    pos = event.getValue()
    if pos.z < 0:
        return Vec3f(-10, -10, 0)
    else:
        pos.z = 0.001
        return pos

class ShadowRadius( TypedField( SFFloat, SFVec3f ) ):
  """
  Set shadow radius based on tracker.
  """
  def update( self, event ):
    pos = event.getValue()
    return 0.0075 + pos.z * 0.03

class ShadowTransparency( TypedField( SFFloat, SFVec3f ) ):
  """
  Set shadow transparency based on tracker.
  """
  def update( self, event ):
    pos = event.getValue()
    return min(1.0, 0.5 + pos.z)

###########################################################################
# Expose fields to H3D.
###########################################################################

force = Force()
isTouched = IsTouched()
contactTexCoord = ContactTexCoord()
toggleHaptics = ToggleHaptics()
toggleTransparency = ToggleTransparency()
shadowTranslation = ShadowTranslation()
shadowTransparency = ShadowTransparency()
shadowRadius = ShadowRadius()

###########################################################################
# The End.
###########################################################################
