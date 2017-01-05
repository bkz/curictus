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
hgt_object_names['BackgroundPlane'] = None
hgt_object_names['CircleEmpty.000'] = None
hgt_object_names['CircleEmpty.001'] = None
hgt_object_names['CircleEmpty.002'] = None
hgt_object_names['CircleEmpty.003'] = None
hgt_object_names['CircleEmpty.004'] = None
hgt_object_names['CircleEmpty.005'] = None
hgt_object_names['CircleEmpty.006'] = None
hgt_object_names['CircleEmpty.007'] = None
hgt_object_names['CircleEmpty.008'] = None
hgt_object_names['CircleEmpty.009'] = None
hgt_object_names['CircleEmpty.010'] = None
hgt_object_names['CircleEmpty.011'] = None
hgt_object_names['CircleEmpty.012'] = None
hgt_object_names['CircleEmpty.013'] = None
hgt_object_names['CircleEmpty.014'] = None
hgt_object_names['CircleEmpty.015'] = None
hgt_object_names['CircleEmpty.016'] = None
hgt_object_names['CircleEmpty.017'] = None
hgt_object_names['CircleEmpty.018'] = None
hgt_object_names['CircleEmpty.019'] = None
hgt_object_names['CircleEmpty.020'] = None
hgt_object_names['CircleEmpty.021'] = None
hgt_object_names['CircleEmpty.022'] = None
hgt_object_names['CircleEmpty.023'] = None
hgt_object_names['CircleEmpty.024'] = None
hgt_object_names['Message'] = None
hgt_object_names['Plane'] = None
hgt_object_names['Plane.001'] = None
hgt_object_names['Plane.002'] = None
hgt_object_names['Point'] = None
hgt_object_names['Point.001'] = None

hgt_objects = {}
hgt_objects['Appearance_BackgroundPlane'] = None
hgt_objects['Appearance_Message'] = None
hgt_objects['Appearance_Plane'] = None
hgt_objects['Appearance_Plane.001'] = None
hgt_objects['Appearance_Plane.002'] = None
hgt_objects['Coord_Plane.001'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_Plane.003'] = None
hgt_objects['Coord_Plane.004'] = None
hgt_objects['Material_BackgroundPlane'] = None
hgt_objects['Material_CorrectTarget'] = None
hgt_objects['Material_DefaultTarget'] = None
hgt_objects['Material_MessageLabel'] = None
hgt_objects['Material_WrongTarget'] = None
hgt_objects['Mesh_Plane.001'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_Plane.003'] = None
hgt_objects['Mesh_Plane.004'] = None
hgt_objects['PointLight_Point'] = None
hgt_objects['PointLight_Point.001'] = None
hgt_objects['Text_Message'] = None
hgt_objects['ToggleGroup_BackgroundPlane'] = None
hgt_objects['ToggleGroup_CircleEmpty.000'] = None
hgt_objects['ToggleGroup_CircleEmpty.001'] = None
hgt_objects['ToggleGroup_CircleEmpty.002'] = None
hgt_objects['ToggleGroup_CircleEmpty.003'] = None
hgt_objects['ToggleGroup_CircleEmpty.004'] = None
hgt_objects['ToggleGroup_CircleEmpty.005'] = None
hgt_objects['ToggleGroup_CircleEmpty.006'] = None
hgt_objects['ToggleGroup_CircleEmpty.007'] = None
hgt_objects['ToggleGroup_CircleEmpty.008'] = None
hgt_objects['ToggleGroup_CircleEmpty.009'] = None
hgt_objects['ToggleGroup_CircleEmpty.010'] = None
hgt_objects['ToggleGroup_CircleEmpty.011'] = None
hgt_objects['ToggleGroup_CircleEmpty.012'] = None
hgt_objects['ToggleGroup_CircleEmpty.013'] = None
hgt_objects['ToggleGroup_CircleEmpty.014'] = None
hgt_objects['ToggleGroup_CircleEmpty.015'] = None
hgt_objects['ToggleGroup_CircleEmpty.016'] = None
hgt_objects['ToggleGroup_CircleEmpty.017'] = None
hgt_objects['ToggleGroup_CircleEmpty.018'] = None
hgt_objects['ToggleGroup_CircleEmpty.019'] = None
hgt_objects['ToggleGroup_CircleEmpty.020'] = None
hgt_objects['ToggleGroup_CircleEmpty.021'] = None
hgt_objects['ToggleGroup_CircleEmpty.022'] = None
hgt_objects['ToggleGroup_CircleEmpty.023'] = None
hgt_objects['ToggleGroup_CircleEmpty.024'] = None
hgt_objects['ToggleGroup_Message'] = None
hgt_objects['ToggleGroup_Plane'] = None
hgt_objects['ToggleGroup_Plane.001'] = None
hgt_objects['ToggleGroup_Plane.002'] = None
hgt_objects['TransformInfo_BackgroundPlane'] = None
hgt_objects['TransformInfo_CircleEmpty.000'] = None
hgt_objects['TransformInfo_CircleEmpty.001'] = None
hgt_objects['TransformInfo_CircleEmpty.002'] = None
hgt_objects['TransformInfo_CircleEmpty.003'] = None
hgt_objects['TransformInfo_CircleEmpty.004'] = None
hgt_objects['TransformInfo_CircleEmpty.005'] = None
hgt_objects['TransformInfo_CircleEmpty.006'] = None
hgt_objects['TransformInfo_CircleEmpty.007'] = None
hgt_objects['TransformInfo_CircleEmpty.008'] = None
hgt_objects['TransformInfo_CircleEmpty.009'] = None
hgt_objects['TransformInfo_CircleEmpty.010'] = None
hgt_objects['TransformInfo_CircleEmpty.011'] = None
hgt_objects['TransformInfo_CircleEmpty.012'] = None
hgt_objects['TransformInfo_CircleEmpty.013'] = None
hgt_objects['TransformInfo_CircleEmpty.014'] = None
hgt_objects['TransformInfo_CircleEmpty.015'] = None
hgt_objects['TransformInfo_CircleEmpty.016'] = None
hgt_objects['TransformInfo_CircleEmpty.017'] = None
hgt_objects['TransformInfo_CircleEmpty.018'] = None
hgt_objects['TransformInfo_CircleEmpty.019'] = None
hgt_objects['TransformInfo_CircleEmpty.020'] = None
hgt_objects['TransformInfo_CircleEmpty.021'] = None
hgt_objects['TransformInfo_CircleEmpty.022'] = None
hgt_objects['TransformInfo_CircleEmpty.023'] = None
hgt_objects['TransformInfo_CircleEmpty.024'] = None
hgt_objects['TransformInfo_Message'] = None
hgt_objects['TransformInfo_Plane'] = None
hgt_objects['TransformInfo_Plane.001'] = None
hgt_objects['TransformInfo_Plane.002'] = None
hgt_objects['Transform_BackgroundPlane'] = None
hgt_objects['Transform_CircleEmpty.000'] = None
hgt_objects['Transform_CircleEmpty.001'] = None
hgt_objects['Transform_CircleEmpty.002'] = None
hgt_objects['Transform_CircleEmpty.003'] = None
hgt_objects['Transform_CircleEmpty.004'] = None
hgt_objects['Transform_CircleEmpty.005'] = None
hgt_objects['Transform_CircleEmpty.006'] = None
hgt_objects['Transform_CircleEmpty.007'] = None
hgt_objects['Transform_CircleEmpty.008'] = None
hgt_objects['Transform_CircleEmpty.009'] = None
hgt_objects['Transform_CircleEmpty.010'] = None
hgt_objects['Transform_CircleEmpty.011'] = None
hgt_objects['Transform_CircleEmpty.012'] = None
hgt_objects['Transform_CircleEmpty.013'] = None
hgt_objects['Transform_CircleEmpty.014'] = None
hgt_objects['Transform_CircleEmpty.015'] = None
hgt_objects['Transform_CircleEmpty.016'] = None
hgt_objects['Transform_CircleEmpty.017'] = None
hgt_objects['Transform_CircleEmpty.018'] = None
hgt_objects['Transform_CircleEmpty.019'] = None
hgt_objects['Transform_CircleEmpty.020'] = None
hgt_objects['Transform_CircleEmpty.021'] = None
hgt_objects['Transform_CircleEmpty.022'] = None
hgt_objects['Transform_CircleEmpty.023'] = None
hgt_objects['Transform_CircleEmpty.024'] = None
hgt_objects['Transform_Message'] = None
hgt_objects['Transform_Plane'] = None
hgt_objects['Transform_Plane.001'] = None
hgt_objects['Transform_Plane.002'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)
