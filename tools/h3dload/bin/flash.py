from H3DInterface import *

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
  position. We use it to simulate a haptic hole/well in the middle lower area
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
          if pos.z <= 0.0 and (contactTexCoord.x > 0.45 and contactTexCoord.x < 0.55 and contactTexCoord.y < 0.25):
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
      if toggleHaptics.insideHole and pos.z < -0.06:
        return 0.15 
      else:
        return 0.0
    else:
      return 0.0

force = Force()
isTouched = IsTouched()
contactTexCoord = ContactTexCoord()
toggleHaptics = ToggleHaptics()
toggleTransparency = ToggleTransparency()
