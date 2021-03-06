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
hgt_object_names['BezierCircle.001'] = None
hgt_object_names['BezierCircle.002'] = None
hgt_object_names['Circle.001'] = None
hgt_object_names['Circle.002'] = None
hgt_object_names['Cube'] = None
hgt_object_names['Cube.002'] = None
hgt_object_names['Curtain'] = None
hgt_object_names['Curtain.001'] = None
hgt_object_names['Dropbox'] = None
hgt_object_names['Dropbox2'] = None
hgt_object_names['Enemy.000'] = None
hgt_object_names['Enemy.001'] = None
hgt_object_names['Enemy.002'] = None
hgt_object_names['EnemyEmpty.000'] = None
hgt_object_names['EnemyEmpty.001'] = None
hgt_object_names['EnemyEmpty.002'] = None
hgt_object_names['EnemyShadow.000'] = None
hgt_object_names['EnemyShadow.001'] = None
hgt_object_names['EnemyShadow.002'] = None
hgt_object_names['EnemySphere.000'] = None
hgt_object_names['EnemySphere.001'] = None
hgt_object_names['EnemySphere.002'] = None
hgt_object_names['FeedbackLabel'] = None
hgt_object_names['FeedbackLabel2'] = None
hgt_object_names['FishBox'] = None
hgt_object_names['GuideArrow'] = None
hgt_object_names['InnerAquariumGlass'] = None
hgt_object_names['LeftBucket'] = None
hgt_object_names['Level'] = None
hgt_object_names['OuterAquariumGlass'] = None
hgt_object_names['Plane'] = None
hgt_object_names['Plane.001'] = None
hgt_object_names['Point'] = None
hgt_object_names['Point.001'] = None
hgt_object_names['Point.002'] = None
hgt_object_names['Point.003'] = None
hgt_object_names['RightBucket'] = None
hgt_object_names['SandBox'] = None
hgt_object_names['Score'] = None
hgt_object_names['Water'] = None

hgt_objects = {}
hgt_objects['Appearance_BezierCircle.001'] = None
hgt_objects['Appearance_BezierCircle.002'] = None
hgt_objects['Appearance_Circle.001'] = None
hgt_objects['Appearance_Circle.002'] = None
hgt_objects['Appearance_Cube'] = None
hgt_objects['Appearance_Cube.002'] = None
hgt_objects['Appearance_Curtain'] = None
hgt_objects['Appearance_Curtain.001'] = None
hgt_objects['Appearance_Dropbox'] = None
hgt_objects['Appearance_Dropbox2'] = None
hgt_objects['Appearance_Enemy.000'] = None
hgt_objects['Appearance_Enemy.001'] = None
hgt_objects['Appearance_Enemy.002'] = None
hgt_objects['Appearance_EnemyShadow.000'] = None
hgt_objects['Appearance_EnemyShadow.001'] = None
hgt_objects['Appearance_EnemyShadow.002'] = None
hgt_objects['Appearance_EnemySphere.000'] = None
hgt_objects['Appearance_EnemySphere.001'] = None
hgt_objects['Appearance_EnemySphere.002'] = None
hgt_objects['Appearance_FeedbackLabel'] = None
hgt_objects['Appearance_FeedbackLabel2'] = None
hgt_objects['Appearance_FishBox'] = None
hgt_objects['Appearance_GuideArrow'] = None
hgt_objects['Appearance_InnerAquariumGlass'] = None
hgt_objects['Appearance_LeftBucket'] = None
hgt_objects['Appearance_Level'] = None
hgt_objects['Appearance_OuterAquariumGlass'] = None
hgt_objects['Appearance_Plane'] = None
hgt_objects['Appearance_Plane.001'] = None
hgt_objects['Appearance_RightBucket'] = None
hgt_objects['Appearance_SandBox'] = None
hgt_objects['Appearance_Score'] = None
hgt_objects['Appearance_Water'] = None
hgt_objects['Coord_Bucket'] = None
hgt_objects['Coord_Bucket.002'] = None
hgt_objects['Coord_Circle'] = None
hgt_objects['Coord_Circle.001'] = None
hgt_objects['Coord_Circle.002'] = None
hgt_objects['Coord_Circle.007'] = None
hgt_objects['Coord_Circle.008'] = None
hgt_objects['Coord_Cube'] = None
hgt_objects['Coord_Cube.002'] = None
hgt_objects['Coord_Cube.003'] = None
hgt_objects['Coord_Cube.004'] = None
hgt_objects['Coord_Cube.005'] = None
hgt_objects['Coord_Cube.008'] = None
hgt_objects['Coord_Curtain'] = None
hgt_objects['Coord_Enemy.000'] = None
hgt_objects['Coord_Enemy.001'] = None
hgt_objects['Coord_Enemy.002'] = None
hgt_objects['Coord_EnemySphere.000'] = None
hgt_objects['Coord_EnemySphere.001'] = None
hgt_objects['Coord_EnemySphere.002'] = None
hgt_objects['Coord_InnerAquariumGlass'] = None
hgt_objects['Coord_Mesh.022'] = None
hgt_objects['Coord_Mesh.1350'] = None
hgt_objects['Coord_OuterAquariumGlass'] = None
hgt_objects['Coord_Plane'] = None
hgt_objects['Coord_Plane.001'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_SandBox'] = None
hgt_objects['DynamicTransform_Water'] = None
hgt_objects['FrictionalSurface_SandBox'] = None
hgt_objects['ImageTexture_landscape.jpg'] = None
hgt_objects['ImageTexture_sand.jpg'] = None
hgt_objects['ImageTexture_sand.jpg.001'] = None
hgt_objects['ImageTexture_tabletop.jpg'] = None
hgt_objects['Material_BucketHandle'] = None
hgt_objects['Material_BucketWater'] = None
hgt_objects['Material_Curtain'] = None
hgt_objects['Material_Enemy.000'] = None
hgt_objects['Material_Enemy.001'] = None
hgt_objects['Material_Enemy.002'] = None
hgt_objects['Material_FeedbackLabel'] = None
hgt_objects['Material_FeedbackLabel2'] = None
hgt_objects['Material_FishTankFrame'] = None
hgt_objects['Material_ForestView'] = None
hgt_objects['Material_Glass'] = None
hgt_objects['Material_GuideArrow'] = None
hgt_objects['Material_Invisible'] = None
hgt_objects['Material_LeftBucket'] = None
hgt_objects['Material_Material'] = None
hgt_objects['Material_OuterGlass'] = None
hgt_objects['Material_RightBucket'] = None
hgt_objects['Material_Sand'] = None
hgt_objects['Material_Shadow'] = None
hgt_objects['Material_Shadow.001'] = None
hgt_objects['Material_Shadow.002'] = None
hgt_objects['Material_TextMaterial'] = None
hgt_objects['Material_Water'] = None
hgt_objects['Material_WindowSill'] = None
hgt_objects['Mesh_Bucket'] = None
hgt_objects['Mesh_Bucket.002'] = None
hgt_objects['Mesh_Circle'] = None
hgt_objects['Mesh_Circle.001'] = None
hgt_objects['Mesh_Circle.002'] = None
hgt_objects['Mesh_Circle.007'] = None
hgt_objects['Mesh_Circle.008'] = None
hgt_objects['Mesh_Cube'] = None
hgt_objects['Mesh_Cube.002'] = None
hgt_objects['Mesh_Cube.003'] = None
hgt_objects['Mesh_Cube.004'] = None
hgt_objects['Mesh_Cube.005'] = None
hgt_objects['Mesh_Cube.008'] = None
hgt_objects['Mesh_Curtain'] = None
hgt_objects['Mesh_Enemy.000'] = None
hgt_objects['Mesh_Enemy.001'] = None
hgt_objects['Mesh_Enemy.002'] = None
hgt_objects['Mesh_EnemySphere.000'] = None
hgt_objects['Mesh_EnemySphere.001'] = None
hgt_objects['Mesh_EnemySphere.002'] = None
hgt_objects['Mesh_InnerAquariumGlass'] = None
hgt_objects['Mesh_Mesh.022'] = None
hgt_objects['Mesh_Mesh.1350'] = None
hgt_objects['Mesh_OuterAquariumGlass'] = None
hgt_objects['Mesh_Plane'] = None
hgt_objects['Mesh_Plane.001'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_SandBox'] = None
hgt_objects['PointLight_Point'] = None
hgt_objects['PointLight_Point.001'] = None
hgt_objects['PointLight_Point.002'] = None
hgt_objects['PointLight_Point.003'] = None
hgt_objects['SmoothSurface_EnemySphere.000'] = None
hgt_objects['SmoothSurface_EnemySphere.001'] = None
hgt_objects['SmoothSurface_EnemySphere.002'] = None
hgt_objects['SmoothSurface_InnerAquariumGlass'] = None
hgt_objects['SmoothSurface_LeftBucket'] = None
hgt_objects['SmoothSurface_OuterAquariumGlass'] = None
hgt_objects['SmoothSurface_Plane'] = None
hgt_objects['SmoothSurface_RightBucket'] = None
hgt_objects['Text_FeedbackLabel'] = None
hgt_objects['Text_FeedbackLabel2'] = None
hgt_objects['Text_Level'] = None
hgt_objects['Text_Score'] = None
hgt_objects['ToggleGroup_BezierCircle.001'] = None
hgt_objects['ToggleGroup_BezierCircle.002'] = None
hgt_objects['ToggleGroup_Circle.001'] = None
hgt_objects['ToggleGroup_Circle.002'] = None
hgt_objects['ToggleGroup_Cube'] = None
hgt_objects['ToggleGroup_Cube.002'] = None
hgt_objects['ToggleGroup_Curtain'] = None
hgt_objects['ToggleGroup_Curtain.001'] = None
hgt_objects['ToggleGroup_Dropbox'] = None
hgt_objects['ToggleGroup_Dropbox2'] = None
hgt_objects['ToggleGroup_Enemy.000'] = None
hgt_objects['ToggleGroup_Enemy.001'] = None
hgt_objects['ToggleGroup_Enemy.002'] = None
hgt_objects['ToggleGroup_EnemyEmpty.000'] = None
hgt_objects['ToggleGroup_EnemyEmpty.001'] = None
hgt_objects['ToggleGroup_EnemyEmpty.002'] = None
hgt_objects['ToggleGroup_EnemyShadow.000'] = None
hgt_objects['ToggleGroup_EnemyShadow.001'] = None
hgt_objects['ToggleGroup_EnemyShadow.002'] = None
hgt_objects['ToggleGroup_EnemySphere.000'] = None
hgt_objects['ToggleGroup_EnemySphere.001'] = None
hgt_objects['ToggleGroup_EnemySphere.002'] = None
hgt_objects['ToggleGroup_FeedbackLabel'] = None
hgt_objects['ToggleGroup_FeedbackLabel2'] = None
hgt_objects['ToggleGroup_FishBox'] = None
hgt_objects['ToggleGroup_GuideArrow'] = None
hgt_objects['ToggleGroup_InnerAquariumGlass'] = None
hgt_objects['ToggleGroup_LeftBucket'] = None
hgt_objects['ToggleGroup_Level'] = None
hgt_objects['ToggleGroup_OuterAquariumGlass'] = None
hgt_objects['ToggleGroup_Plane'] = None
hgt_objects['ToggleGroup_Plane.001'] = None
hgt_objects['ToggleGroup_RightBucket'] = None
hgt_objects['ToggleGroup_SandBox'] = None
hgt_objects['ToggleGroup_Score'] = None
hgt_objects['ToggleGroup_Water'] = None
hgt_objects['TransformInfo_BezierCircle.001'] = None
hgt_objects['TransformInfo_BezierCircle.002'] = None
hgt_objects['TransformInfo_Circle.001'] = None
hgt_objects['TransformInfo_Circle.002'] = None
hgt_objects['TransformInfo_Cube'] = None
hgt_objects['TransformInfo_Cube.002'] = None
hgt_objects['TransformInfo_Curtain'] = None
hgt_objects['TransformInfo_Curtain.001'] = None
hgt_objects['TransformInfo_Dropbox'] = None
hgt_objects['TransformInfo_Dropbox2'] = None
hgt_objects['TransformInfo_Enemy.000'] = None
hgt_objects['TransformInfo_Enemy.001'] = None
hgt_objects['TransformInfo_Enemy.002'] = None
hgt_objects['TransformInfo_EnemyEmpty.000'] = None
hgt_objects['TransformInfo_EnemyEmpty.001'] = None
hgt_objects['TransformInfo_EnemyEmpty.002'] = None
hgt_objects['TransformInfo_EnemyShadow.000'] = None
hgt_objects['TransformInfo_EnemyShadow.001'] = None
hgt_objects['TransformInfo_EnemyShadow.002'] = None
hgt_objects['TransformInfo_EnemySphere.000'] = None
hgt_objects['TransformInfo_EnemySphere.001'] = None
hgt_objects['TransformInfo_EnemySphere.002'] = None
hgt_objects['TransformInfo_FeedbackLabel'] = None
hgt_objects['TransformInfo_FeedbackLabel2'] = None
hgt_objects['TransformInfo_FishBox'] = None
hgt_objects['TransformInfo_GuideArrow'] = None
hgt_objects['TransformInfo_InnerAquariumGlass'] = None
hgt_objects['TransformInfo_LeftBucket'] = None
hgt_objects['TransformInfo_Level'] = None
hgt_objects['TransformInfo_OuterAquariumGlass'] = None
hgt_objects['TransformInfo_Plane'] = None
hgt_objects['TransformInfo_Plane.001'] = None
hgt_objects['TransformInfo_RightBucket'] = None
hgt_objects['TransformInfo_SandBox'] = None
hgt_objects['TransformInfo_Score'] = None
hgt_objects['TransformInfo_Water'] = None
hgt_objects['Transform_BezierCircle.001'] = None
hgt_objects['Transform_BezierCircle.002'] = None
hgt_objects['Transform_Circle.001'] = None
hgt_objects['Transform_Circle.002'] = None
hgt_objects['Transform_Cube'] = None
hgt_objects['Transform_Cube.002'] = None
hgt_objects['Transform_Curtain'] = None
hgt_objects['Transform_Curtain.001'] = None
hgt_objects['Transform_Dropbox'] = None
hgt_objects['Transform_Dropbox2'] = None
hgt_objects['Transform_Enemy.000'] = None
hgt_objects['Transform_Enemy.001'] = None
hgt_objects['Transform_Enemy.002'] = None
hgt_objects['Transform_EnemyEmpty.000'] = None
hgt_objects['Transform_EnemyEmpty.001'] = None
hgt_objects['Transform_EnemyEmpty.002'] = None
hgt_objects['Transform_EnemyShadow.000'] = None
hgt_objects['Transform_EnemyShadow.001'] = None
hgt_objects['Transform_EnemyShadow.002'] = None
hgt_objects['Transform_EnemySphere.000'] = None
hgt_objects['Transform_EnemySphere.001'] = None
hgt_objects['Transform_EnemySphere.002'] = None
hgt_objects['Transform_FeedbackLabel'] = None
hgt_objects['Transform_FeedbackLabel2'] = None
hgt_objects['Transform_FishBox'] = None
hgt_objects['Transform_GuideArrow'] = None
hgt_objects['Transform_InnerAquariumGlass'] = None
hgt_objects['Transform_LeftBucket'] = None
hgt_objects['Transform_Level'] = None
hgt_objects['Transform_OuterAquariumGlass'] = None
hgt_objects['Transform_Plane'] = None
hgt_objects['Transform_Plane.001'] = None
hgt_objects['Transform_RightBucket'] = None
hgt_objects['Transform_SandBox'] = None
hgt_objects['Transform_Score'] = None
hgt_objects['Transform_Water'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)
