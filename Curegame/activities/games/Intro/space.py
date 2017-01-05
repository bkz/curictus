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
hgt_object_names['Apple'] = None
hgt_object_names['AquariumGlass'] = None
hgt_object_names['AquariumGlassEmpty'] = None
hgt_object_names['AquariumLamp'] = None
hgt_object_names['Circle.001'] = None
hgt_object_names['Circle.002'] = None
hgt_object_names['Cube'] = None
hgt_object_names['Cube.001'] = None
hgt_object_names['Cube.002'] = None
hgt_object_names['Cylinder'] = None
hgt_object_names['Cylinder.001'] = None
hgt_object_names['EarthAxis'] = None
hgt_object_names['EarthAxisRod'] = None
hgt_object_names['EarthSea'] = None
hgt_object_names['Empty'] = None
hgt_object_names['Empty.003'] = None
hgt_object_names['Empty.004'] = None
hgt_object_names['Empty.005'] = None
hgt_object_names['ExitLamp'] = None
hgt_object_names['ExitSign'] = None
hgt_object_names['GrabReleaseSensor'] = None
hgt_object_names['GuideArrow'] = None
hgt_object_names['HapticGuide'] = None
hgt_object_names['LeftLamp'] = None
hgt_object_names['LightButton'] = None
hgt_object_names['Melon'] = None
hgt_object_names['Orange'] = None
hgt_object_names['Painting'] = None
hgt_object_names['Plane.002'] = None
hgt_object_names['Plane.003'] = None
hgt_object_names['Plane.004'] = None
hgt_object_names['RightLamp'] = None
hgt_object_names['RightLamp.001'] = None
hgt_object_names['Strawberry'] = None
hgt_object_names['Torus'] = None
hgt_object_names['UserMessage'] = None
hgt_object_names['UserMessage2'] = None
hgt_object_names['WallAndCorner'] = None
hgt_object_names['WallAndCorner.001'] = None
hgt_object_names['Wallpaper'] = None

hgt_objects = {}
hgt_objects['Appearance_Apple'] = None
hgt_objects['Appearance_AquariumGlass'] = None
hgt_objects['Appearance_Circle.001'] = None
hgt_objects['Appearance_Circle.002'] = None
hgt_objects['Appearance_Cube'] = None
hgt_objects['Appearance_Cube.001'] = None
hgt_objects['Appearance_Cube.002'] = None
hgt_objects['Appearance_Cylinder'] = None
hgt_objects['Appearance_Cylinder.001'] = None
hgt_objects['Appearance_EarthAxisRod'] = None
hgt_objects['Appearance_EarthSea'] = None
hgt_objects['Appearance_ExitSign'] = None
hgt_objects['Appearance_GrabReleaseSensor'] = None
hgt_objects['Appearance_GuideArrow'] = None
hgt_objects['Appearance_HapticGuide'] = None
hgt_objects['Appearance_LightButton'] = None
hgt_objects['Appearance_Melon'] = None
hgt_objects['Appearance_Orange'] = None
hgt_objects['Appearance_Painting'] = None
hgt_objects['Appearance_Plane.002'] = None
hgt_objects['Appearance_Plane.003'] = None
hgt_objects['Appearance_Plane.004'] = None
hgt_objects['Appearance_Strawberry'] = None
hgt_objects['Appearance_Torus'] = None
hgt_objects['Appearance_UserMessage'] = None
hgt_objects['Appearance_UserMessage2'] = None
hgt_objects['Appearance_WallAndCorner'] = None
hgt_objects['Appearance_WallAndCorner.001'] = None
hgt_objects['Appearance_Wallpaper'] = None
hgt_objects['Coord_Apple'] = None
hgt_objects['Coord_AquariumGlass'] = None
hgt_objects['Coord_Circle.001'] = None
hgt_objects['Coord_Circle.002'] = None
hgt_objects['Coord_Circle.004'] = None
hgt_objects['Coord_Circle.005'] = None
hgt_objects['Coord_Cube'] = None
hgt_objects['Coord_Cube.001'] = None
hgt_objects['Coord_Cube.002'] = None
hgt_objects['Coord_Cylinder'] = None
hgt_objects['Coord_Cylinder.001'] = None
hgt_objects['Coord_Cylinder.002'] = None
hgt_objects['Coord_EarthSea'] = None
hgt_objects['Coord_ExitSign'] = None
hgt_objects['Coord_GrabReleaseSensor'] = None
hgt_objects['Coord_HapticGuide'] = None
hgt_objects['Coord_LightButton'] = None
hgt_objects['Coord_Melon'] = None
hgt_objects['Coord_Orange'] = None
hgt_objects['Coord_Painting'] = None
hgt_objects['Coord_Plane'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_Plane.003'] = None
hgt_objects['Coord_Plane.005'] = None
hgt_objects['Coord_Plane.008'] = None
hgt_objects['Coord_Strawberry'] = None
hgt_objects['Coord_Torus'] = None
hgt_objects['ImageTexture_VanGogh_Bedroom_Arles'] = None
hgt_objects['ImageTexture_earthmap1k.jpg'] = None
hgt_objects['ImageTexture_exitsign.png'] = None
hgt_objects['ImageTexture_tabletop.jpg'] = None
hgt_objects['ImageTexture_wallpaper.jpg'] = None
hgt_objects['Material_Apple'] = None
hgt_objects['Material_AquariumGlass'] = None
hgt_objects['Material_AquariumInsideWall'] = None
hgt_objects['Material_Arrow'] = None
hgt_objects['Material_Brass'] = None
hgt_objects['Material_ButtonMaterial'] = None
hgt_objects['Material_EarthBlue'] = None
hgt_objects['Material_ExitBlock'] = None
hgt_objects['Material_ExitSign'] = None
hgt_objects['Material_GrabReleaseSensor'] = None
hgt_objects['Material_HapticGuide'] = None
hgt_objects['Material_LightButtonRim'] = None
hgt_objects['Material_LightRay'] = None
hgt_objects['Material_ListOfTheWall'] = None
hgt_objects['Material_Melon'] = None
hgt_objects['Material_Message'] = None
hgt_objects['Material_Orange'] = None
hgt_objects['Material_Painting'] = None
hgt_objects['Material_Picture Frame'] = None
hgt_objects['Material_Strawberry'] = None
hgt_objects['Material_Tabletop'] = None
hgt_objects['Material_WallOfHapticLimits'] = None
hgt_objects['Material_Wallpaper'] = None
hgt_objects['Mesh_Apple'] = None
hgt_objects['Mesh_AquariumGlass'] = None
hgt_objects['Mesh_Circle.001'] = None
hgt_objects['Mesh_Circle.002'] = None
hgt_objects['Mesh_Circle.004'] = None
hgt_objects['Mesh_Circle.005'] = None
hgt_objects['Mesh_Cube'] = None
hgt_objects['Mesh_Cube.001'] = None
hgt_objects['Mesh_Cube.002'] = None
hgt_objects['Mesh_Cylinder'] = None
hgt_objects['Mesh_Cylinder.001'] = None
hgt_objects['Mesh_Cylinder.002'] = None
hgt_objects['Mesh_EarthSea'] = None
hgt_objects['Mesh_ExitSign'] = None
hgt_objects['Mesh_GrabReleaseSensor'] = None
hgt_objects['Mesh_HapticGuide'] = None
hgt_objects['Mesh_LightButton'] = None
hgt_objects['Mesh_Melon'] = None
hgt_objects['Mesh_Orange'] = None
hgt_objects['Mesh_Painting'] = None
hgt_objects['Mesh_Plane'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_Plane.003'] = None
hgt_objects['Mesh_Plane.005'] = None
hgt_objects['Mesh_Plane.008'] = None
hgt_objects['Mesh_Strawberry'] = None
hgt_objects['Mesh_Torus'] = None
hgt_objects['PointLight_AquariumLamp'] = None
hgt_objects['PointLight_ExitLamp'] = None
hgt_objects['PointLight_LeftLamp'] = None
hgt_objects['PointLight_RightLamp'] = None
hgt_objects['PointLight_RightLamp.001'] = None
hgt_objects['Text_UserMessage'] = None
hgt_objects['Text_UserMessage2'] = None
hgt_objects['ToggleGroup_Apple'] = None
hgt_objects['ToggleGroup_AquariumGlass'] = None
hgt_objects['ToggleGroup_AquariumGlassEmpty'] = None
hgt_objects['ToggleGroup_Circle.001'] = None
hgt_objects['ToggleGroup_Circle.002'] = None
hgt_objects['ToggleGroup_Cube'] = None
hgt_objects['ToggleGroup_Cube.001'] = None
hgt_objects['ToggleGroup_Cube.002'] = None
hgt_objects['ToggleGroup_Cylinder'] = None
hgt_objects['ToggleGroup_Cylinder.001'] = None
hgt_objects['ToggleGroup_EarthAxis'] = None
hgt_objects['ToggleGroup_EarthAxisRod'] = None
hgt_objects['ToggleGroup_EarthSea'] = None
hgt_objects['ToggleGroup_Empty'] = None
hgt_objects['ToggleGroup_Empty.003'] = None
hgt_objects['ToggleGroup_Empty.004'] = None
hgt_objects['ToggleGroup_Empty.005'] = None
hgt_objects['ToggleGroup_ExitSign'] = None
hgt_objects['ToggleGroup_GrabReleaseSensor'] = None
hgt_objects['ToggleGroup_GuideArrow'] = None
hgt_objects['ToggleGroup_HapticGuide'] = None
hgt_objects['ToggleGroup_LightButton'] = None
hgt_objects['ToggleGroup_Melon'] = None
hgt_objects['ToggleGroup_Orange'] = None
hgt_objects['ToggleGroup_Painting'] = None
hgt_objects['ToggleGroup_Plane.002'] = None
hgt_objects['ToggleGroup_Plane.003'] = None
hgt_objects['ToggleGroup_Plane.004'] = None
hgt_objects['ToggleGroup_Strawberry'] = None
hgt_objects['ToggleGroup_Torus'] = None
hgt_objects['ToggleGroup_UserMessage'] = None
hgt_objects['ToggleGroup_UserMessage2'] = None
hgt_objects['ToggleGroup_WallAndCorner'] = None
hgt_objects['ToggleGroup_WallAndCorner.001'] = None
hgt_objects['ToggleGroup_Wallpaper'] = None
hgt_objects['TransformInfo_Apple'] = None
hgt_objects['TransformInfo_AquariumGlass'] = None
hgt_objects['TransformInfo_AquariumGlassEmpty'] = None
hgt_objects['TransformInfo_Circle.001'] = None
hgt_objects['TransformInfo_Circle.002'] = None
hgt_objects['TransformInfo_Cube'] = None
hgt_objects['TransformInfo_Cube.001'] = None
hgt_objects['TransformInfo_Cube.002'] = None
hgt_objects['TransformInfo_Cylinder'] = None
hgt_objects['TransformInfo_Cylinder.001'] = None
hgt_objects['TransformInfo_EarthAxis'] = None
hgt_objects['TransformInfo_EarthAxisRod'] = None
hgt_objects['TransformInfo_EarthSea'] = None
hgt_objects['TransformInfo_Empty'] = None
hgt_objects['TransformInfo_Empty.003'] = None
hgt_objects['TransformInfo_Empty.004'] = None
hgt_objects['TransformInfo_Empty.005'] = None
hgt_objects['TransformInfo_ExitSign'] = None
hgt_objects['TransformInfo_GrabReleaseSensor'] = None
hgt_objects['TransformInfo_GuideArrow'] = None
hgt_objects['TransformInfo_HapticGuide'] = None
hgt_objects['TransformInfo_LightButton'] = None
hgt_objects['TransformInfo_Melon'] = None
hgt_objects['TransformInfo_Orange'] = None
hgt_objects['TransformInfo_Painting'] = None
hgt_objects['TransformInfo_Plane.002'] = None
hgt_objects['TransformInfo_Plane.003'] = None
hgt_objects['TransformInfo_Plane.004'] = None
hgt_objects['TransformInfo_Strawberry'] = None
hgt_objects['TransformInfo_Torus'] = None
hgt_objects['TransformInfo_UserMessage'] = None
hgt_objects['TransformInfo_UserMessage2'] = None
hgt_objects['TransformInfo_WallAndCorner'] = None
hgt_objects['TransformInfo_WallAndCorner.001'] = None
hgt_objects['TransformInfo_Wallpaper'] = None
hgt_objects['Transform_Apple'] = None
hgt_objects['Transform_AquariumGlass'] = None
hgt_objects['Transform_AquariumGlassEmpty'] = None
hgt_objects['Transform_Circle.001'] = None
hgt_objects['Transform_Circle.002'] = None
hgt_objects['Transform_Cube'] = None
hgt_objects['Transform_Cube.001'] = None
hgt_objects['Transform_Cube.002'] = None
hgt_objects['Transform_Cylinder'] = None
hgt_objects['Transform_Cylinder.001'] = None
hgt_objects['Transform_EarthAxis'] = None
hgt_objects['Transform_EarthAxisRod'] = None
hgt_objects['Transform_EarthSea'] = None
hgt_objects['Transform_Empty'] = None
hgt_objects['Transform_Empty.003'] = None
hgt_objects['Transform_Empty.004'] = None
hgt_objects['Transform_Empty.005'] = None
hgt_objects['Transform_ExitSign'] = None
hgt_objects['Transform_GrabReleaseSensor'] = None
hgt_objects['Transform_GuideArrow'] = None
hgt_objects['Transform_HapticGuide'] = None
hgt_objects['Transform_LightButton'] = None
hgt_objects['Transform_Melon'] = None
hgt_objects['Transform_Orange'] = None
hgt_objects['Transform_Painting'] = None
hgt_objects['Transform_Plane.002'] = None
hgt_objects['Transform_Plane.003'] = None
hgt_objects['Transform_Plane.004'] = None
hgt_objects['Transform_Strawberry'] = None
hgt_objects['Transform_Torus'] = None
hgt_objects['Transform_UserMessage'] = None
hgt_objects['Transform_UserMessage2'] = None
hgt_objects['Transform_WallAndCorner'] = None
hgt_objects['Transform_WallAndCorner.001'] = None
hgt_objects['Transform_Wallpaper'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)