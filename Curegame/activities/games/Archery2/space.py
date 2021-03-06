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
hgt_object_names['Aim'] = None
hgt_object_names['Arrow'] = None
hgt_object_names['ArrowCounter'] = None
hgt_object_names['ArrowFeathers'] = None
hgt_object_names['ArrowLabel'] = None
hgt_object_names['ArrowStick'] = None
hgt_object_names['BottomPoint'] = None
hgt_object_names['Bow'] = None
hgt_object_names['Circle'] = None
hgt_object_names['Circle.006'] = None
hgt_object_names['Circle.007'] = None
hgt_object_names['Empty'] = None
hgt_object_names['Empty.001'] = None
hgt_object_names['FeedbackLabel'] = None
hgt_object_names['FinalScore'] = None
hgt_object_names['FlyingArrow'] = None
hgt_object_names['GuideArrow'] = None
hgt_object_names['Marker1'] = None
hgt_object_names['Marker2'] = None
hgt_object_names['MidPoint'] = None
hgt_object_names['Nail'] = None
hgt_object_names['Plane'] = None
hgt_object_names['Plane.001'] = None
hgt_object_names['Plane.002'] = None
hgt_object_names['Plane.003'] = None
hgt_object_names['Plane.006'] = None
hgt_object_names['Plane.013'] = None
hgt_object_names['Plane.014'] = None
hgt_object_names['Point'] = None
hgt_object_names['Point.001'] = None
hgt_object_names['PullPoint'] = None
hgt_object_names['Quiver'] = None
hgt_object_names['ReloadArrow'] = None
hgt_object_names['Score'] = None
hgt_object_names['ScoreLabel'] = None
hgt_object_names['Sky'] = None
hgt_object_names['StringPoint'] = None
hgt_object_names['Target.000'] = None
hgt_object_names['Target.001'] = None
hgt_object_names['Target.002'] = None
hgt_object_names['TargetImage.000'] = None
hgt_object_names['TargetImage.001'] = None
hgt_object_names['TargetImage.002'] = None
hgt_object_names['TopPoint'] = None
hgt_object_names['WoodTarget.000'] = None
hgt_object_names['WoodTarget.001'] = None
hgt_object_names['WoodTarget.002'] = None

hgt_objects = {}
hgt_objects['Appearance_ArrowFeathers'] = None
hgt_objects['Appearance_ArrowStick'] = None
hgt_objects['Appearance_Bow'] = None
hgt_objects['Appearance_Circle'] = None
hgt_objects['Appearance_Circle.006'] = None
hgt_objects['Appearance_Circle.007'] = None
hgt_objects['Appearance_GuideArrow'] = None
hgt_objects['Appearance_Marker1'] = None
hgt_objects['Appearance_Marker2'] = None
hgt_objects['Appearance_Nail'] = None
hgt_objects['Appearance_Plane'] = None
hgt_objects['Appearance_Plane.001'] = None
hgt_objects['Appearance_Plane.002'] = None
hgt_objects['Appearance_Plane.003'] = None
hgt_objects['Appearance_Plane.006'] = None
hgt_objects['Appearance_Plane.013'] = None
hgt_objects['Appearance_Plane.014'] = None
hgt_objects['Appearance_Quiver'] = None
hgt_objects['Appearance_Sky'] = None
hgt_objects['Appearance_TargetImage.000'] = None
hgt_objects['Appearance_TargetImage.001'] = None
hgt_objects['Appearance_TargetImage.002'] = None
hgt_objects['Appearance_WoodTarget.000'] = None
hgt_objects['Appearance_WoodTarget.001'] = None
hgt_objects['Appearance_WoodTarget.002'] = None
hgt_objects['Coord_ArrowFeathers'] = None
hgt_objects['Coord_ArrowStick'] = None
hgt_objects['Coord_Circle'] = None
hgt_objects['Coord_Circle.001'] = None
hgt_objects['Coord_Circle.002'] = None
hgt_objects['Coord_Circle.003'] = None
hgt_objects['Coord_Circle.008'] = None
hgt_objects['Coord_Circle.009'] = None
hgt_objects['Coord_Cube'] = None
hgt_objects['Coord_Cube.001'] = None
hgt_objects['Coord_Cylinder'] = None
hgt_objects['Coord_Cylinder.001'] = None
hgt_objects['Coord_Cylinder.002'] = None
hgt_objects['Coord_Cylinder.003'] = None
hgt_objects['Coord_Plane'] = None
hgt_objects['Coord_Plane.001'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_Plane.003'] = None
hgt_objects['Coord_Plane.004'] = None
hgt_objects['Coord_Plane.005'] = None
hgt_objects['Coord_Plane.007'] = None
hgt_objects['Coord_Plane.014'] = None
hgt_objects['Coord_Plane.015'] = None
hgt_objects['Coord_Plane.016'] = None
hgt_objects['Coord_Quiver'] = None
hgt_objects['DirectionalLight_Point.001'] = None
hgt_objects['DynamicTransform_Sky'] = None
hgt_objects['ImageTexture_grass.jpg'] = None
hgt_objects['ImageTexture_paper.jpg'] = None
hgt_objects['ImageTexture_sky.jpg'] = None
hgt_objects['ImageTexture_target.jpg'] = None
hgt_objects['Material_Arrow'] = None
hgt_objects['Material_ArrowFeather'] = None
hgt_objects['Material_ArrowHead'] = None
hgt_objects['Material_Bow'] = None
hgt_objects['Material_FeedbackLabel'] = None
hgt_objects['Material_FinalScore'] = None
hgt_objects['Material_Grass'] = None
hgt_objects['Material_GuideArrow'] = None
hgt_objects['Material_Marker1'] = None
hgt_objects['Material_Marker2'] = None
hgt_objects['Material_Nail'] = None
hgt_objects['Material_Paper'] = None
hgt_objects['Material_Quiver'] = None
hgt_objects['Material_Sky'] = None
hgt_objects['Material_Target'] = None
hgt_objects['Material_Text'] = None
hgt_objects['Material_TreeTrunk'] = None
hgt_objects['Material_Wood'] = None
hgt_objects['Mesh_ArrowFeathers'] = None
hgt_objects['Mesh_ArrowStick'] = None
hgt_objects['Mesh_Circle'] = None
hgt_objects['Mesh_Circle.001'] = None
hgt_objects['Mesh_Circle.002'] = None
hgt_objects['Mesh_Circle.003'] = None
hgt_objects['Mesh_Circle.008'] = None
hgt_objects['Mesh_Circle.009'] = None
hgt_objects['Mesh_Cube'] = None
hgt_objects['Mesh_Cube.001'] = None
hgt_objects['Mesh_Cylinder'] = None
hgt_objects['Mesh_Cylinder.001'] = None
hgt_objects['Mesh_Cylinder.002'] = None
hgt_objects['Mesh_Cylinder.003'] = None
hgt_objects['Mesh_Plane'] = None
hgt_objects['Mesh_Plane.001'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_Plane.003'] = None
hgt_objects['Mesh_Plane.004'] = None
hgt_objects['Mesh_Plane.005'] = None
hgt_objects['Mesh_Plane.007'] = None
hgt_objects['Mesh_Plane.014'] = None
hgt_objects['Mesh_Plane.015'] = None
hgt_objects['Mesh_Plane.016'] = None
hgt_objects['Mesh_Quiver'] = None
hgt_objects['PointLight_Point'] = None
hgt_objects['Text_ArrowCounter'] = None
hgt_objects['Text_ArrowLabel'] = None
hgt_objects['Text_FeedbackLabel'] = None
hgt_objects['Text_FinalScore'] = None
hgt_objects['Text_Score'] = None
hgt_objects['Text_ScoreLabel'] = None
hgt_objects['ToggleGroup_Aim'] = None
hgt_objects['ToggleGroup_Arrow'] = None
hgt_objects['ToggleGroup_ArrowCounter'] = None
hgt_objects['ToggleGroup_ArrowFeathers'] = None
hgt_objects['ToggleGroup_ArrowLabel'] = None
hgt_objects['ToggleGroup_ArrowStick'] = None
hgt_objects['ToggleGroup_BottomPoint'] = None
hgt_objects['ToggleGroup_Bow'] = None
hgt_objects['ToggleGroup_Circle'] = None
hgt_objects['ToggleGroup_Circle.006'] = None
hgt_objects['ToggleGroup_Circle.007'] = None
hgt_objects['ToggleGroup_Empty'] = None
hgt_objects['ToggleGroup_Empty.001'] = None
hgt_objects['ToggleGroup_FeedbackLabel'] = None
hgt_objects['ToggleGroup_FinalScore'] = None
hgt_objects['ToggleGroup_FlyingArrow'] = None
hgt_objects['ToggleGroup_GuideArrow'] = None
hgt_objects['ToggleGroup_Marker1'] = None
hgt_objects['ToggleGroup_Marker2'] = None
hgt_objects['ToggleGroup_MidPoint'] = None
hgt_objects['ToggleGroup_Nail'] = None
hgt_objects['ToggleGroup_Plane'] = None
hgt_objects['ToggleGroup_Plane.001'] = None
hgt_objects['ToggleGroup_Plane.002'] = None
hgt_objects['ToggleGroup_Plane.003'] = None
hgt_objects['ToggleGroup_Plane.006'] = None
hgt_objects['ToggleGroup_Plane.013'] = None
hgt_objects['ToggleGroup_Plane.014'] = None
hgt_objects['ToggleGroup_PullPoint'] = None
hgt_objects['ToggleGroup_Quiver'] = None
hgt_objects['ToggleGroup_ReloadArrow'] = None
hgt_objects['ToggleGroup_Score'] = None
hgt_objects['ToggleGroup_ScoreLabel'] = None
hgt_objects['ToggleGroup_Sky'] = None
hgt_objects['ToggleGroup_StringPoint'] = None
hgt_objects['ToggleGroup_Target.000'] = None
hgt_objects['ToggleGroup_Target.001'] = None
hgt_objects['ToggleGroup_Target.002'] = None
hgt_objects['ToggleGroup_TargetImage.000'] = None
hgt_objects['ToggleGroup_TargetImage.001'] = None
hgt_objects['ToggleGroup_TargetImage.002'] = None
hgt_objects['ToggleGroup_TopPoint'] = None
hgt_objects['ToggleGroup_WoodTarget.000'] = None
hgt_objects['ToggleGroup_WoodTarget.001'] = None
hgt_objects['ToggleGroup_WoodTarget.002'] = None
hgt_objects['TransformInfo_Aim'] = None
hgt_objects['TransformInfo_Arrow'] = None
hgt_objects['TransformInfo_ArrowCounter'] = None
hgt_objects['TransformInfo_ArrowFeathers'] = None
hgt_objects['TransformInfo_ArrowLabel'] = None
hgt_objects['TransformInfo_ArrowStick'] = None
hgt_objects['TransformInfo_BottomPoint'] = None
hgt_objects['TransformInfo_Bow'] = None
hgt_objects['TransformInfo_Circle'] = None
hgt_objects['TransformInfo_Circle.006'] = None
hgt_objects['TransformInfo_Circle.007'] = None
hgt_objects['TransformInfo_Empty'] = None
hgt_objects['TransformInfo_Empty.001'] = None
hgt_objects['TransformInfo_FeedbackLabel'] = None
hgt_objects['TransformInfo_FinalScore'] = None
hgt_objects['TransformInfo_FlyingArrow'] = None
hgt_objects['TransformInfo_GuideArrow'] = None
hgt_objects['TransformInfo_Marker1'] = None
hgt_objects['TransformInfo_Marker2'] = None
hgt_objects['TransformInfo_MidPoint'] = None
hgt_objects['TransformInfo_Nail'] = None
hgt_objects['TransformInfo_Plane'] = None
hgt_objects['TransformInfo_Plane.001'] = None
hgt_objects['TransformInfo_Plane.002'] = None
hgt_objects['TransformInfo_Plane.003'] = None
hgt_objects['TransformInfo_Plane.006'] = None
hgt_objects['TransformInfo_Plane.013'] = None
hgt_objects['TransformInfo_Plane.014'] = None
hgt_objects['TransformInfo_PullPoint'] = None
hgt_objects['TransformInfo_Quiver'] = None
hgt_objects['TransformInfo_ReloadArrow'] = None
hgt_objects['TransformInfo_Score'] = None
hgt_objects['TransformInfo_ScoreLabel'] = None
hgt_objects['TransformInfo_Sky'] = None
hgt_objects['TransformInfo_StringPoint'] = None
hgt_objects['TransformInfo_Target.000'] = None
hgt_objects['TransformInfo_Target.001'] = None
hgt_objects['TransformInfo_Target.002'] = None
hgt_objects['TransformInfo_TargetImage.000'] = None
hgt_objects['TransformInfo_TargetImage.001'] = None
hgt_objects['TransformInfo_TargetImage.002'] = None
hgt_objects['TransformInfo_TopPoint'] = None
hgt_objects['TransformInfo_WoodTarget.000'] = None
hgt_objects['TransformInfo_WoodTarget.001'] = None
hgt_objects['TransformInfo_WoodTarget.002'] = None
hgt_objects['Transform_Aim'] = None
hgt_objects['Transform_Arrow'] = None
hgt_objects['Transform_ArrowCounter'] = None
hgt_objects['Transform_ArrowFeathers'] = None
hgt_objects['Transform_ArrowLabel'] = None
hgt_objects['Transform_ArrowStick'] = None
hgt_objects['Transform_BottomPoint'] = None
hgt_objects['Transform_Bow'] = None
hgt_objects['Transform_Circle'] = None
hgt_objects['Transform_Circle.006'] = None
hgt_objects['Transform_Circle.007'] = None
hgt_objects['Transform_Empty'] = None
hgt_objects['Transform_Empty.001'] = None
hgt_objects['Transform_FeedbackLabel'] = None
hgt_objects['Transform_FinalScore'] = None
hgt_objects['Transform_FlyingArrow'] = None
hgt_objects['Transform_GuideArrow'] = None
hgt_objects['Transform_Marker1'] = None
hgt_objects['Transform_Marker2'] = None
hgt_objects['Transform_MidPoint'] = None
hgt_objects['Transform_Nail'] = None
hgt_objects['Transform_Plane'] = None
hgt_objects['Transform_Plane.001'] = None
hgt_objects['Transform_Plane.002'] = None
hgt_objects['Transform_Plane.003'] = None
hgt_objects['Transform_Plane.006'] = None
hgt_objects['Transform_Plane.013'] = None
hgt_objects['Transform_Plane.014'] = None
hgt_objects['Transform_PullPoint'] = None
hgt_objects['Transform_Quiver'] = None
hgt_objects['Transform_ReloadArrow'] = None
hgt_objects['Transform_Score'] = None
hgt_objects['Transform_ScoreLabel'] = None
hgt_objects['Transform_Sky'] = None
hgt_objects['Transform_StringPoint'] = None
hgt_objects['Transform_Target.000'] = None
hgt_objects['Transform_Target.001'] = None
hgt_objects['Transform_Target.002'] = None
hgt_objects['Transform_TargetImage.000'] = None
hgt_objects['Transform_TargetImage.001'] = None
hgt_objects['Transform_TargetImage.002'] = None
hgt_objects['Transform_TopPoint'] = None
hgt_objects['Transform_WoodTarget.000'] = None
hgt_objects['Transform_WoodTarget.001'] = None
hgt_objects['Transform_WoodTarget.002'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)
