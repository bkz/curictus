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
hgt_object_names['Answer0'] = None
hgt_object_names['Answer1'] = None
hgt_object_names['Answer2'] = None
hgt_object_names['Answer3'] = None
hgt_object_names['AnswerPad0'] = None
hgt_object_names['AnswerPad1'] = None
hgt_object_names['AnswerPad2'] = None
hgt_object_names['AnswerPad3'] = None
hgt_object_names['Cube'] = None
hgt_object_names['Cylinder'] = None
hgt_object_names['Cylinder.001'] = None
hgt_object_names['Cylinder.002'] = None
hgt_object_names['EndLabel'] = None
hgt_object_names['FeedbackLabel'] = None
hgt_object_names['Hint'] = None
hgt_object_names['Plane'] = None
hgt_object_names['Plane.001'] = None
hgt_object_names['Plane.002'] = None
hgt_object_names['Plane.003'] = None
hgt_object_names['Point'] = None
hgt_object_names['Point.001'] = None
hgt_object_names['ProblemLine1'] = None
hgt_object_names['ProblemLine2'] = None
hgt_object_names['ProblemNumber'] = None
hgt_object_names['ProblemNumberLabel'] = None
hgt_object_names['Score'] = None
hgt_object_names['ScoreLabel'] = None
hgt_object_names['Solution'] = None

hgt_objects = {}
hgt_objects['Appearance_Answer0'] = None
hgt_objects['Appearance_Answer1'] = None
hgt_objects['Appearance_Answer2'] = None
hgt_objects['Appearance_Answer3'] = None
hgt_objects['Appearance_AnswerPad0'] = None
hgt_objects['Appearance_AnswerPad1'] = None
hgt_objects['Appearance_AnswerPad2'] = None
hgt_objects['Appearance_AnswerPad3'] = None
hgt_objects['Appearance_Cube'] = None
hgt_objects['Appearance_Cylinder'] = None
hgt_objects['Appearance_Cylinder.001'] = None
hgt_objects['Appearance_Cylinder.002'] = None
hgt_objects['Appearance_EndLabel'] = None
hgt_objects['Appearance_FeedbackLabel'] = None
hgt_objects['Appearance_Hint'] = None
hgt_objects['Appearance_Plane'] = None
hgt_objects['Appearance_Plane.001'] = None
hgt_objects['Appearance_Plane.002'] = None
hgt_objects['Appearance_Plane.003'] = None
hgt_objects['Appearance_ProblemLine1'] = None
hgt_objects['Appearance_ProblemLine2'] = None
hgt_objects['Appearance_ProblemNumber'] = None
hgt_objects['Appearance_ProblemNumberLabel'] = None
hgt_objects['Appearance_Score'] = None
hgt_objects['Appearance_ScoreLabel'] = None
hgt_objects['Appearance_Solution'] = None
hgt_objects['Coord_AnswerPad0'] = None
hgt_objects['Coord_AnswerPad1'] = None
hgt_objects['Coord_AnswerPad2'] = None
hgt_objects['Coord_AnswerPad3'] = None
hgt_objects['Coord_Chalkboard'] = None
hgt_objects['Coord_Cube'] = None
hgt_objects['Coord_Cylinder'] = None
hgt_objects['Coord_Cylinder.001'] = None
hgt_objects['Coord_Cylinder.002'] = None
hgt_objects['Coord_Plane'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_Plane.003'] = None
hgt_objects['FrictionalSurface_AnswerPad0'] = None
hgt_objects['FrictionalSurface_AnswerPad1'] = None
hgt_objects['FrictionalSurface_AnswerPad2'] = None
hgt_objects['FrictionalSurface_AnswerPad3'] = None
hgt_objects['FrictionalSurface_Plane.001'] = None
hgt_objects['ImageTexture_chalkboard.jpg'] = None
hgt_objects['ImageTexture_wood.jpg'] = None
hgt_objects['Material_Answer0'] = None
hgt_objects['Material_Answer1'] = None
hgt_objects['Material_Answer2'] = None
hgt_objects['Material_Answer3'] = None
hgt_objects['Material_Button'] = None
hgt_objects['Material_Chalk'] = None
hgt_objects['Material_Chalk2'] = None
hgt_objects['Material_Chalk3'] = None
hgt_objects['Material_Chalkboard'] = None
hgt_objects['Material_Chalky'] = None
hgt_objects['Material_Felt'] = None
hgt_objects['Material_Invisible'] = None
hgt_objects['Material_TexturedWood'] = None
hgt_objects['Material_Wood'] = None
hgt_objects['Material_YellowChalky'] = None
hgt_objects['Mesh_AnswerPad0'] = None
hgt_objects['Mesh_AnswerPad1'] = None
hgt_objects['Mesh_AnswerPad2'] = None
hgt_objects['Mesh_AnswerPad3'] = None
hgt_objects['Mesh_Chalkboard'] = None
hgt_objects['Mesh_Cube'] = None
hgt_objects['Mesh_Cylinder'] = None
hgt_objects['Mesh_Cylinder.001'] = None
hgt_objects['Mesh_Cylinder.002'] = None
hgt_objects['Mesh_Plane'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_Plane.003'] = None
hgt_objects['PointLight_Point'] = None
hgt_objects['PointLight_Point.001'] = None
hgt_objects['SmoothSurface_Plane'] = None
hgt_objects['SmoothSurface_Plane.002'] = None
hgt_objects['SmoothSurface_Plane.003'] = None
hgt_objects['Text_Answer0'] = None
hgt_objects['Text_Answer1'] = None
hgt_objects['Text_Answer2'] = None
hgt_objects['Text_Answer3'] = None
hgt_objects['Text_EndLabel'] = None
hgt_objects['Text_FeedbackLabel'] = None
hgt_objects['Text_Hint'] = None
hgt_objects['Text_ProblemLine1'] = None
hgt_objects['Text_ProblemLine2'] = None
hgt_objects['Text_ProblemNumber'] = None
hgt_objects['Text_ProblemNumberLabel'] = None
hgt_objects['Text_Score'] = None
hgt_objects['Text_ScoreLabel'] = None
hgt_objects['Text_Solution'] = None
hgt_objects['ToggleGroup_Answer0'] = None
hgt_objects['ToggleGroup_Answer1'] = None
hgt_objects['ToggleGroup_Answer2'] = None
hgt_objects['ToggleGroup_Answer3'] = None
hgt_objects['ToggleGroup_AnswerPad0'] = None
hgt_objects['ToggleGroup_AnswerPad1'] = None
hgt_objects['ToggleGroup_AnswerPad2'] = None
hgt_objects['ToggleGroup_AnswerPad3'] = None
hgt_objects['ToggleGroup_Cube'] = None
hgt_objects['ToggleGroup_Cylinder'] = None
hgt_objects['ToggleGroup_Cylinder.001'] = None
hgt_objects['ToggleGroup_Cylinder.002'] = None
hgt_objects['ToggleGroup_EndLabel'] = None
hgt_objects['ToggleGroup_FeedbackLabel'] = None
hgt_objects['ToggleGroup_Hint'] = None
hgt_objects['ToggleGroup_Plane'] = None
hgt_objects['ToggleGroup_Plane.001'] = None
hgt_objects['ToggleGroup_Plane.002'] = None
hgt_objects['ToggleGroup_Plane.003'] = None
hgt_objects['ToggleGroup_ProblemLine1'] = None
hgt_objects['ToggleGroup_ProblemLine2'] = None
hgt_objects['ToggleGroup_ProblemNumber'] = None
hgt_objects['ToggleGroup_ProblemNumberLabel'] = None
hgt_objects['ToggleGroup_Score'] = None
hgt_objects['ToggleGroup_ScoreLabel'] = None
hgt_objects['ToggleGroup_Solution'] = None
hgt_objects['TransformInfo_Answer0'] = None
hgt_objects['TransformInfo_Answer1'] = None
hgt_objects['TransformInfo_Answer2'] = None
hgt_objects['TransformInfo_Answer3'] = None
hgt_objects['TransformInfo_AnswerPad0'] = None
hgt_objects['TransformInfo_AnswerPad1'] = None
hgt_objects['TransformInfo_AnswerPad2'] = None
hgt_objects['TransformInfo_AnswerPad3'] = None
hgt_objects['TransformInfo_Cube'] = None
hgt_objects['TransformInfo_Cylinder'] = None
hgt_objects['TransformInfo_Cylinder.001'] = None
hgt_objects['TransformInfo_Cylinder.002'] = None
hgt_objects['TransformInfo_EndLabel'] = None
hgt_objects['TransformInfo_FeedbackLabel'] = None
hgt_objects['TransformInfo_Hint'] = None
hgt_objects['TransformInfo_Plane'] = None
hgt_objects['TransformInfo_Plane.001'] = None
hgt_objects['TransformInfo_Plane.002'] = None
hgt_objects['TransformInfo_Plane.003'] = None
hgt_objects['TransformInfo_ProblemLine1'] = None
hgt_objects['TransformInfo_ProblemLine2'] = None
hgt_objects['TransformInfo_ProblemNumber'] = None
hgt_objects['TransformInfo_ProblemNumberLabel'] = None
hgt_objects['TransformInfo_Score'] = None
hgt_objects['TransformInfo_ScoreLabel'] = None
hgt_objects['TransformInfo_Solution'] = None
hgt_objects['Transform_Answer0'] = None
hgt_objects['Transform_Answer1'] = None
hgt_objects['Transform_Answer2'] = None
hgt_objects['Transform_Answer3'] = None
hgt_objects['Transform_AnswerPad0'] = None
hgt_objects['Transform_AnswerPad1'] = None
hgt_objects['Transform_AnswerPad2'] = None
hgt_objects['Transform_AnswerPad3'] = None
hgt_objects['Transform_Cube'] = None
hgt_objects['Transform_Cylinder'] = None
hgt_objects['Transform_Cylinder.001'] = None
hgt_objects['Transform_Cylinder.002'] = None
hgt_objects['Transform_EndLabel'] = None
hgt_objects['Transform_FeedbackLabel'] = None
hgt_objects['Transform_Hint'] = None
hgt_objects['Transform_Plane'] = None
hgt_objects['Transform_Plane.001'] = None
hgt_objects['Transform_Plane.002'] = None
hgt_objects['Transform_Plane.003'] = None
hgt_objects['Transform_ProblemLine1'] = None
hgt_objects['Transform_ProblemLine2'] = None
hgt_objects['Transform_ProblemNumber'] = None
hgt_objects['Transform_ProblemNumberLabel'] = None
hgt_objects['Transform_Score'] = None
hgt_objects['Transform_ScoreLabel'] = None
hgt_objects['Transform_Solution'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)
