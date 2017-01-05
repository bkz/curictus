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

# This is an auto-generated file. Do not edit manually.
import hgt
from hgt.blenderhelpers import get_world_and_nodes
hgt_filename = 'space.hgt'

hgt_object_names = {}
hgt_object_names['Button.001'] = None
hgt_object_names['Button.002'] = None
hgt_object_names['Button.003'] = None
hgt_object_names['Button.004'] = None
hgt_object_names['Button.005'] = None
hgt_object_names['Button.006'] = None
hgt_object_names['Button.007'] = None
hgt_object_names['Button.008'] = None
hgt_object_names['Button.009'] = None
hgt_object_names['Button.010'] = None
hgt_object_names['Button.011'] = None
hgt_object_names['Button.012'] = None
hgt_object_names['ButtonGlow'] = None
hgt_object_names['Circle'] = None
hgt_object_names['Circle.001'] = None
hgt_object_names['Circle.002'] = None
hgt_object_names['Cup'] = None
hgt_object_names['Empty'] = None
hgt_object_names['Empty.001'] = None
hgt_object_names['Empty.002'] = None
hgt_object_names['Empty.003'] = None
hgt_object_names['Empty.004'] = None
hgt_object_names['Empty.005'] = None
hgt_object_names['Empty.006'] = None
hgt_object_names['Empty.008'] = None
hgt_object_names['Empty.009'] = None
hgt_object_names['Lamp.000'] = None
hgt_object_names['Lamp.001'] = None
hgt_object_names['LargeLabel'] = None
hgt_object_names['LengthLabel'] = None
hgt_object_names['LengthLabel.001'] = None
hgt_object_names['LengthLabel.002'] = None
hgt_object_names['MediumLabel'] = None
hgt_object_names['Plane.002'] = None
hgt_object_names['Plane.003'] = None
hgt_object_names['Plane.004'] = None
hgt_object_names['Plane.005'] = None
hgt_object_names['Plane.006'] = None
hgt_object_names['Plane.007'] = None
hgt_object_names['Plane.008'] = None
hgt_object_names['Plane.009'] = None
hgt_object_names['Sphere.001'] = None
hgt_object_names['Sphere.002'] = None
hgt_object_names['Sun'] = None
hgt_object_names['Table'] = None
hgt_object_names['Torus'] = None
hgt_object_names['Torus.001'] = None
hgt_object_names['Torus.002'] = None
hgt_object_names['Torus.003'] = None
hgt_object_names['Torus.004'] = None
hgt_object_names['Torus.005'] = None
hgt_object_names['Torus.006'] = None
hgt_object_names['Torus.007'] = None
hgt_object_names['Torus.008'] = None
hgt_object_names['Torus.009'] = None
hgt_object_names['Torus.010'] = None
hgt_object_names['Torus.011'] = None
hgt_object_names['Torus.013'] = None
hgt_object_names['Torus.014'] = None
hgt_object_names['TouchButton.001'] = None
hgt_object_names['TouchButton.002'] = None
hgt_object_names['TouchButton.003'] = None
hgt_object_names['TouchButton.004'] = None
hgt_object_names['TouchButton.005'] = None
hgt_object_names['TouchButton.006'] = None
hgt_object_names['TouchButton.007'] = None
hgt_object_names['TouchButton.008'] = None
hgt_object_names['TouchButton.009'] = None
hgt_object_names['TouchButton.010'] = None
hgt_object_names['TouchButton.011'] = None
hgt_object_names['TouchButton.012'] = None

hgt_objects = {}
hgt_objects['Appearance_Circle'] = None
hgt_objects['Appearance_Circle.001'] = None
hgt_objects['Appearance_Circle.002'] = None
hgt_objects['Appearance_LargeLabel'] = None
hgt_objects['Appearance_LengthLabel'] = None
hgt_objects['Appearance_LengthLabel.001'] = None
hgt_objects['Appearance_LengthLabel.002'] = None
hgt_objects['Appearance_MediumLabel'] = None
hgt_objects['Appearance_Plane.002'] = None
hgt_objects['Appearance_Plane.003'] = None
hgt_objects['Appearance_Plane.004'] = None
hgt_objects['Appearance_Plane.005'] = None
hgt_objects['Appearance_Plane.006'] = None
hgt_objects['Appearance_Plane.007'] = None
hgt_objects['Appearance_Plane.008'] = None
hgt_objects['Appearance_Plane.009'] = None
hgt_objects['Appearance_Sphere.001'] = None
hgt_objects['Appearance_Sphere.002'] = None
hgt_objects['Appearance_Table'] = None
hgt_objects['Appearance_Torus'] = None
hgt_objects['Appearance_Torus.001'] = None
hgt_objects['Appearance_Torus.002'] = None
hgt_objects['Appearance_Torus.003'] = None
hgt_objects['Appearance_Torus.004'] = None
hgt_objects['Appearance_Torus.005'] = None
hgt_objects['Appearance_Torus.006'] = None
hgt_objects['Appearance_Torus.007'] = None
hgt_objects['Appearance_Torus.008'] = None
hgt_objects['Appearance_Torus.009'] = None
hgt_objects['Appearance_Torus.010'] = None
hgt_objects['Appearance_Torus.011'] = None
hgt_objects['Appearance_Torus.013'] = None
hgt_objects['Appearance_Torus.014'] = None
hgt_objects['Appearance_TouchButton.001'] = None
hgt_objects['Appearance_TouchButton.002'] = None
hgt_objects['Appearance_TouchButton.003'] = None
hgt_objects['Appearance_TouchButton.004'] = None
hgt_objects['Appearance_TouchButton.005'] = None
hgt_objects['Appearance_TouchButton.006'] = None
hgt_objects['Appearance_TouchButton.007'] = None
hgt_objects['Appearance_TouchButton.008'] = None
hgt_objects['Appearance_TouchButton.009'] = None
hgt_objects['Appearance_TouchButton.010'] = None
hgt_objects['Appearance_TouchButton.011'] = None
hgt_objects['Appearance_TouchButton.012'] = None
hgt_objects['Coord_Button.001'] = None
hgt_objects['Coord_Button.002'] = None
hgt_objects['Coord_Button.003'] = None
hgt_objects['Coord_Button.004'] = None
hgt_objects['Coord_Button.005'] = None
hgt_objects['Coord_Button.006'] = None
hgt_objects['Coord_Button.007'] = None
hgt_objects['Coord_Button.008'] = None
hgt_objects['Coord_Button.009'] = None
hgt_objects['Coord_Button.010'] = None
hgt_objects['Coord_Button.011'] = None
hgt_objects['Coord_Button.012'] = None
hgt_objects['Coord_Circle.001'] = None
hgt_objects['Coord_Circle.002'] = None
hgt_objects['Coord_Circle.003'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_Plane.003'] = None
hgt_objects['Coord_Plane.004'] = None
hgt_objects['Coord_Plane.005'] = None
hgt_objects['Coord_Plane.006'] = None
hgt_objects['Coord_Plane.007'] = None
hgt_objects['Coord_Plane.008'] = None
hgt_objects['Coord_Plane.009'] = None
hgt_objects['Coord_Plane.010'] = None
hgt_objects['Coord_Sphere.001'] = None
hgt_objects['Coord_Sphere.002'] = None
hgt_objects['Coord_Torus.001'] = None
hgt_objects['Coord_Torus.002'] = None
hgt_objects['Coord_TorusMeshThingy'] = None
hgt_objects['DirectionalLight_Sun'] = None
hgt_objects['DynamicTransform_Cup'] = None
hgt_objects['FrictionalSurface_Circle'] = None
hgt_objects['FrictionalSurface_Circle.001'] = None
hgt_objects['ImageTexture_leather.jpg'] = None
hgt_objects['ImageTexture_tabletop.jpg'] = None
hgt_objects['Material_Button.001'] = None
hgt_objects['Material_Button.002'] = None
hgt_objects['Material_Button.003'] = None
hgt_objects['Material_Button.004'] = None
hgt_objects['Material_Button.005'] = None
hgt_objects['Material_Button.006'] = None
hgt_objects['Material_Button.007'] = None
hgt_objects['Material_Button.008'] = None
hgt_objects['Material_Button.009'] = None
hgt_objects['Material_Button.010'] = None
hgt_objects['Material_Button.011'] = None
hgt_objects['Material_Button.012'] = None
hgt_objects['Material_Chrome'] = None
hgt_objects['Material_DarkMaterial'] = None
hgt_objects['Material_HolderThingy'] = None
hgt_objects['Material_LED1'] = None
hgt_objects['Material_LED2'] = None
hgt_objects['Material_Label'] = None
hgt_objects['Material_LedBezel'] = None
hgt_objects['Material_RewardCup'] = None
hgt_objects['Material_Rubber'] = None
hgt_objects['Material_Table'] = None
hgt_objects['Mesh_Button.001'] = None
hgt_objects['Mesh_Button.002'] = None
hgt_objects['Mesh_Button.003'] = None
hgt_objects['Mesh_Button.004'] = None
hgt_objects['Mesh_Button.005'] = None
hgt_objects['Mesh_Button.006'] = None
hgt_objects['Mesh_Button.007'] = None
hgt_objects['Mesh_Button.008'] = None
hgt_objects['Mesh_Button.009'] = None
hgt_objects['Mesh_Button.010'] = None
hgt_objects['Mesh_Button.011'] = None
hgt_objects['Mesh_Button.012'] = None
hgt_objects['Mesh_Circle.001'] = None
hgt_objects['Mesh_Circle.002'] = None
hgt_objects['Mesh_Circle.003'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_Plane.003'] = None
hgt_objects['Mesh_Plane.004'] = None
hgt_objects['Mesh_Plane.005'] = None
hgt_objects['Mesh_Plane.006'] = None
hgt_objects['Mesh_Plane.007'] = None
hgt_objects['Mesh_Plane.008'] = None
hgt_objects['Mesh_Plane.009'] = None
hgt_objects['Mesh_Plane.010'] = None
hgt_objects['Mesh_Sphere.001'] = None
hgt_objects['Mesh_Sphere.002'] = None
hgt_objects['Mesh_Torus.001'] = None
hgt_objects['Mesh_Torus.002'] = None
hgt_objects['Mesh_TorusMeshThingy'] = None
hgt_objects['PointLight_ButtonGlow'] = None
hgt_objects['PointLight_Lamp.000'] = None
hgt_objects['PointLight_Lamp.001'] = None
hgt_objects['SmoothSurface_Circle.002'] = None
hgt_objects['SmoothSurface_Plane.002'] = None
hgt_objects['SmoothSurface_Plane.003'] = None
hgt_objects['SmoothSurface_Table'] = None
hgt_objects['SmoothSurface_Torus'] = None
hgt_objects['SmoothSurface_Torus.001'] = None
hgt_objects['SmoothSurface_Torus.002'] = None
hgt_objects['SmoothSurface_Torus.003'] = None
hgt_objects['SmoothSurface_Torus.004'] = None
hgt_objects['SmoothSurface_Torus.005'] = None
hgt_objects['SmoothSurface_Torus.006'] = None
hgt_objects['SmoothSurface_Torus.007'] = None
hgt_objects['SmoothSurface_Torus.008'] = None
hgt_objects['SmoothSurface_Torus.009'] = None
hgt_objects['SmoothSurface_Torus.010'] = None
hgt_objects['SmoothSurface_Torus.011'] = None
hgt_objects['SmoothSurface_TouchButton.001'] = None
hgt_objects['SmoothSurface_TouchButton.002'] = None
hgt_objects['SmoothSurface_TouchButton.003'] = None
hgt_objects['SmoothSurface_TouchButton.004'] = None
hgt_objects['SmoothSurface_TouchButton.005'] = None
hgt_objects['SmoothSurface_TouchButton.006'] = None
hgt_objects['SmoothSurface_TouchButton.007'] = None
hgt_objects['SmoothSurface_TouchButton.008'] = None
hgt_objects['SmoothSurface_TouchButton.009'] = None
hgt_objects['SmoothSurface_TouchButton.010'] = None
hgt_objects['SmoothSurface_TouchButton.011'] = None
hgt_objects['SmoothSurface_TouchButton.012'] = None
hgt_objects['Text_LargeLabel'] = None
hgt_objects['Text_LengthLabel'] = None
hgt_objects['Text_LengthLabel.001'] = None
hgt_objects['Text_LengthLabel.002'] = None
hgt_objects['Text_MediumLabel'] = None
hgt_objects['ToggleGroup_Button.001'] = None
hgt_objects['ToggleGroup_Button.002'] = None
hgt_objects['ToggleGroup_Button.003'] = None
hgt_objects['ToggleGroup_Button.004'] = None
hgt_objects['ToggleGroup_Button.005'] = None
hgt_objects['ToggleGroup_Button.006'] = None
hgt_objects['ToggleGroup_Button.007'] = None
hgt_objects['ToggleGroup_Button.008'] = None
hgt_objects['ToggleGroup_Button.009'] = None
hgt_objects['ToggleGroup_Button.010'] = None
hgt_objects['ToggleGroup_Button.011'] = None
hgt_objects['ToggleGroup_Button.012'] = None
hgt_objects['ToggleGroup_Circle'] = None
hgt_objects['ToggleGroup_Circle.001'] = None
hgt_objects['ToggleGroup_Circle.002'] = None
hgt_objects['ToggleGroup_Cup'] = None
hgt_objects['ToggleGroup_Empty'] = None
hgt_objects['ToggleGroup_Empty.001'] = None
hgt_objects['ToggleGroup_Empty.002'] = None
hgt_objects['ToggleGroup_Empty.003'] = None
hgt_objects['ToggleGroup_Empty.004'] = None
hgt_objects['ToggleGroup_Empty.005'] = None
hgt_objects['ToggleGroup_Empty.006'] = None
hgt_objects['ToggleGroup_Empty.008'] = None
hgt_objects['ToggleGroup_Empty.009'] = None
hgt_objects['ToggleGroup_LargeLabel'] = None
hgt_objects['ToggleGroup_LengthLabel'] = None
hgt_objects['ToggleGroup_LengthLabel.001'] = None
hgt_objects['ToggleGroup_LengthLabel.002'] = None
hgt_objects['ToggleGroup_MediumLabel'] = None
hgt_objects['ToggleGroup_Plane.002'] = None
hgt_objects['ToggleGroup_Plane.003'] = None
hgt_objects['ToggleGroup_Plane.004'] = None
hgt_objects['ToggleGroup_Plane.005'] = None
hgt_objects['ToggleGroup_Plane.006'] = None
hgt_objects['ToggleGroup_Plane.007'] = None
hgt_objects['ToggleGroup_Plane.008'] = None
hgt_objects['ToggleGroup_Plane.009'] = None
hgt_objects['ToggleGroup_Sphere.001'] = None
hgt_objects['ToggleGroup_Sphere.002'] = None
hgt_objects['ToggleGroup_Table'] = None
hgt_objects['ToggleGroup_Torus'] = None
hgt_objects['ToggleGroup_Torus.001'] = None
hgt_objects['ToggleGroup_Torus.002'] = None
hgt_objects['ToggleGroup_Torus.003'] = None
hgt_objects['ToggleGroup_Torus.004'] = None
hgt_objects['ToggleGroup_Torus.005'] = None
hgt_objects['ToggleGroup_Torus.006'] = None
hgt_objects['ToggleGroup_Torus.007'] = None
hgt_objects['ToggleGroup_Torus.008'] = None
hgt_objects['ToggleGroup_Torus.009'] = None
hgt_objects['ToggleGroup_Torus.010'] = None
hgt_objects['ToggleGroup_Torus.011'] = None
hgt_objects['ToggleGroup_Torus.013'] = None
hgt_objects['ToggleGroup_Torus.014'] = None
hgt_objects['ToggleGroup_TouchButton.001'] = None
hgt_objects['ToggleGroup_TouchButton.002'] = None
hgt_objects['ToggleGroup_TouchButton.003'] = None
hgt_objects['ToggleGroup_TouchButton.004'] = None
hgt_objects['ToggleGroup_TouchButton.005'] = None
hgt_objects['ToggleGroup_TouchButton.006'] = None
hgt_objects['ToggleGroup_TouchButton.007'] = None
hgt_objects['ToggleGroup_TouchButton.008'] = None
hgt_objects['ToggleGroup_TouchButton.009'] = None
hgt_objects['ToggleGroup_TouchButton.010'] = None
hgt_objects['ToggleGroup_TouchButton.011'] = None
hgt_objects['ToggleGroup_TouchButton.012'] = None
hgt_objects['TransformInfo_Button.001'] = None
hgt_objects['TransformInfo_Button.002'] = None
hgt_objects['TransformInfo_Button.003'] = None
hgt_objects['TransformInfo_Button.004'] = None
hgt_objects['TransformInfo_Button.005'] = None
hgt_objects['TransformInfo_Button.006'] = None
hgt_objects['TransformInfo_Button.007'] = None
hgt_objects['TransformInfo_Button.008'] = None
hgt_objects['TransformInfo_Button.009'] = None
hgt_objects['TransformInfo_Button.010'] = None
hgt_objects['TransformInfo_Button.011'] = None
hgt_objects['TransformInfo_Button.012'] = None
hgt_objects['TransformInfo_Circle'] = None
hgt_objects['TransformInfo_Circle.001'] = None
hgt_objects['TransformInfo_Circle.002'] = None
hgt_objects['TransformInfo_Cup'] = None
hgt_objects['TransformInfo_Empty'] = None
hgt_objects['TransformInfo_Empty.001'] = None
hgt_objects['TransformInfo_Empty.002'] = None
hgt_objects['TransformInfo_Empty.003'] = None
hgt_objects['TransformInfo_Empty.004'] = None
hgt_objects['TransformInfo_Empty.005'] = None
hgt_objects['TransformInfo_Empty.006'] = None
hgt_objects['TransformInfo_Empty.008'] = None
hgt_objects['TransformInfo_Empty.009'] = None
hgt_objects['TransformInfo_LargeLabel'] = None
hgt_objects['TransformInfo_LengthLabel'] = None
hgt_objects['TransformInfo_LengthLabel.001'] = None
hgt_objects['TransformInfo_LengthLabel.002'] = None
hgt_objects['TransformInfo_MediumLabel'] = None
hgt_objects['TransformInfo_Plane.002'] = None
hgt_objects['TransformInfo_Plane.003'] = None
hgt_objects['TransformInfo_Plane.004'] = None
hgt_objects['TransformInfo_Plane.005'] = None
hgt_objects['TransformInfo_Plane.006'] = None
hgt_objects['TransformInfo_Plane.007'] = None
hgt_objects['TransformInfo_Plane.008'] = None
hgt_objects['TransformInfo_Plane.009'] = None
hgt_objects['TransformInfo_Sphere.001'] = None
hgt_objects['TransformInfo_Sphere.002'] = None
hgt_objects['TransformInfo_Table'] = None
hgt_objects['TransformInfo_Torus'] = None
hgt_objects['TransformInfo_Torus.001'] = None
hgt_objects['TransformInfo_Torus.002'] = None
hgt_objects['TransformInfo_Torus.003'] = None
hgt_objects['TransformInfo_Torus.004'] = None
hgt_objects['TransformInfo_Torus.005'] = None
hgt_objects['TransformInfo_Torus.006'] = None
hgt_objects['TransformInfo_Torus.007'] = None
hgt_objects['TransformInfo_Torus.008'] = None
hgt_objects['TransformInfo_Torus.009'] = None
hgt_objects['TransformInfo_Torus.010'] = None
hgt_objects['TransformInfo_Torus.011'] = None
hgt_objects['TransformInfo_Torus.013'] = None
hgt_objects['TransformInfo_Torus.014'] = None
hgt_objects['TransformInfo_TouchButton.001'] = None
hgt_objects['TransformInfo_TouchButton.002'] = None
hgt_objects['TransformInfo_TouchButton.003'] = None
hgt_objects['TransformInfo_TouchButton.004'] = None
hgt_objects['TransformInfo_TouchButton.005'] = None
hgt_objects['TransformInfo_TouchButton.006'] = None
hgt_objects['TransformInfo_TouchButton.007'] = None
hgt_objects['TransformInfo_TouchButton.008'] = None
hgt_objects['TransformInfo_TouchButton.009'] = None
hgt_objects['TransformInfo_TouchButton.010'] = None
hgt_objects['TransformInfo_TouchButton.011'] = None
hgt_objects['TransformInfo_TouchButton.012'] = None
hgt_objects['Transform_Button.001'] = None
hgt_objects['Transform_Button.002'] = None
hgt_objects['Transform_Button.003'] = None
hgt_objects['Transform_Button.004'] = None
hgt_objects['Transform_Button.005'] = None
hgt_objects['Transform_Button.006'] = None
hgt_objects['Transform_Button.007'] = None
hgt_objects['Transform_Button.008'] = None
hgt_objects['Transform_Button.009'] = None
hgt_objects['Transform_Button.010'] = None
hgt_objects['Transform_Button.011'] = None
hgt_objects['Transform_Button.012'] = None
hgt_objects['Transform_Circle'] = None
hgt_objects['Transform_Circle.001'] = None
hgt_objects['Transform_Circle.002'] = None
hgt_objects['Transform_Cup'] = None
hgt_objects['Transform_Empty'] = None
hgt_objects['Transform_Empty.001'] = None
hgt_objects['Transform_Empty.002'] = None
hgt_objects['Transform_Empty.003'] = None
hgt_objects['Transform_Empty.004'] = None
hgt_objects['Transform_Empty.005'] = None
hgt_objects['Transform_Empty.006'] = None
hgt_objects['Transform_Empty.008'] = None
hgt_objects['Transform_Empty.009'] = None
hgt_objects['Transform_LargeLabel'] = None
hgt_objects['Transform_LengthLabel'] = None
hgt_objects['Transform_LengthLabel.001'] = None
hgt_objects['Transform_LengthLabel.002'] = None
hgt_objects['Transform_MediumLabel'] = None
hgt_objects['Transform_Plane.002'] = None
hgt_objects['Transform_Plane.003'] = None
hgt_objects['Transform_Plane.004'] = None
hgt_objects['Transform_Plane.005'] = None
hgt_objects['Transform_Plane.006'] = None
hgt_objects['Transform_Plane.007'] = None
hgt_objects['Transform_Plane.008'] = None
hgt_objects['Transform_Plane.009'] = None
hgt_objects['Transform_Sphere.001'] = None
hgt_objects['Transform_Sphere.002'] = None
hgt_objects['Transform_Table'] = None
hgt_objects['Transform_Torus'] = None
hgt_objects['Transform_Torus.001'] = None
hgt_objects['Transform_Torus.002'] = None
hgt_objects['Transform_Torus.003'] = None
hgt_objects['Transform_Torus.004'] = None
hgt_objects['Transform_Torus.005'] = None
hgt_objects['Transform_Torus.006'] = None
hgt_objects['Transform_Torus.007'] = None
hgt_objects['Transform_Torus.008'] = None
hgt_objects['Transform_Torus.009'] = None
hgt_objects['Transform_Torus.010'] = None
hgt_objects['Transform_Torus.011'] = None
hgt_objects['Transform_Torus.013'] = None
hgt_objects['Transform_Torus.014'] = None
hgt_objects['Transform_TouchButton.001'] = None
hgt_objects['Transform_TouchButton.002'] = None
hgt_objects['Transform_TouchButton.003'] = None
hgt_objects['Transform_TouchButton.004'] = None
hgt_objects['Transform_TouchButton.005'] = None
hgt_objects['Transform_TouchButton.006'] = None
hgt_objects['Transform_TouchButton.007'] = None
hgt_objects['Transform_TouchButton.008'] = None
hgt_objects['Transform_TouchButton.009'] = None
hgt_objects['Transform_TouchButton.010'] = None
hgt_objects['Transform_TouchButton.011'] = None
hgt_objects['Transform_TouchButton.012'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)