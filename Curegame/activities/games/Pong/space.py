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
hgt_object_names['BALL'] = None
hgt_object_names['Center'] = None
hgt_object_names['Cube'] = None
hgt_object_names['Cylinder'] = None
hgt_object_names['LASER'] = None
hgt_object_names['Lamp'] = None
hgt_object_names['Lamp.001'] = None
hgt_object_names['Lamp.002'] = None
hgt_object_names['Lamp.003'] = None
hgt_object_names['Life0'] = None
hgt_object_names['Life0.003'] = None
hgt_object_names['Life2'] = None
hgt_object_names['Life2.001'] = None
hgt_object_names['MSG'] = None
hgt_object_names['Plane'] = None
hgt_object_names['Plane.001'] = None
hgt_object_names['Plane.002'] = None
hgt_object_names['Plane.003'] = None
hgt_object_names['Plane.004'] = None
hgt_object_names['Plane.005'] = None
hgt_object_names['Plane.006'] = None
hgt_object_names['Plane.007'] = None
hgt_object_names['SCORE'] = None
hgt_object_names['Sphere'] = None
hgt_object_names['Sphere.001'] = None

hgt_objects = {}
hgt_objects['Coord_BALL'] = None
hgt_objects['Coord_Cube.002'] = None
hgt_objects['Coord_Cylinder'] = None
hgt_objects['Coord_LASER'] = None
hgt_objects['Coord_Plane'] = None
hgt_objects['Coord_Plane.001'] = None
hgt_objects['Coord_Plane.002'] = None
hgt_objects['Coord_Plane.003'] = None
hgt_objects['Coord_Plane.004'] = None
hgt_objects['Coord_Plane.005'] = None
hgt_objects['Coord_Plane.006'] = None
hgt_objects['Coord_Plane.007'] = None
hgt_objects['Coord_Sphere'] = None
hgt_objects['Coord_Sphere.001'] = None
hgt_objects['Coord_Sphere.002'] = None
hgt_objects['Coord_Sphere.005'] = None
hgt_objects['Coord_Sphere.006'] = None
hgt_objects['Coord_Sphere.007'] = None
hgt_objects['Material_BackSphere'] = None
hgt_objects['Material_Ball'] = None
hgt_objects['Material_BallMarker1'] = None
hgt_objects['Material_BallMarker2'] = None
hgt_objects['Material_CourtWalls'] = None
hgt_objects['Material_DarkStuff'] = None
hgt_objects['Material_FloorCylinder'] = None
hgt_objects['Material_GoldRim'] = None
hgt_objects['Material_Laser'] = None
hgt_objects['Material_MSG'] = None
hgt_objects['Material_OpponentMarker'] = None
hgt_objects['Material_OtherDarkStuff'] = None
hgt_objects['Material_PlayerMarker'] = None
hgt_objects['Material_SCORE'] = None
hgt_objects['Material_ScorePlate'] = None
hgt_objects['Mesh_BALL'] = None
hgt_objects['Mesh_Cube.002'] = None
hgt_objects['Mesh_Cylinder'] = None
hgt_objects['Mesh_LASER'] = None
hgt_objects['Mesh_Plane'] = None
hgt_objects['Mesh_Plane.001'] = None
hgt_objects['Mesh_Plane.002'] = None
hgt_objects['Mesh_Plane.003'] = None
hgt_objects['Mesh_Plane.004'] = None
hgt_objects['Mesh_Plane.005'] = None
hgt_objects['Mesh_Plane.006'] = None
hgt_objects['Mesh_Plane.007'] = None
hgt_objects['Mesh_Sphere'] = None
hgt_objects['Mesh_Sphere.001'] = None
hgt_objects['Mesh_Sphere.002'] = None
hgt_objects['Mesh_Sphere.005'] = None
hgt_objects['Mesh_Sphere.006'] = None
hgt_objects['Mesh_Sphere.007'] = None
hgt_objects['PointLight_Lamp'] = None
hgt_objects['PointLight_Lamp.001'] = None
hgt_objects['PointLight_Lamp.002'] = None
hgt_objects['PointLight_Lamp.003'] = None
hgt_objects['Text_MSG'] = None
hgt_objects['Text_SCORE'] = None
hgt_objects['ToggleGroup_BALL'] = None
hgt_objects['ToggleGroup_Center'] = None
hgt_objects['ToggleGroup_Cube'] = None
hgt_objects['ToggleGroup_Cylinder'] = None
hgt_objects['ToggleGroup_LASER'] = None
hgt_objects['ToggleGroup_Life0'] = None
hgt_objects['ToggleGroup_Life0.003'] = None
hgt_objects['ToggleGroup_Life2'] = None
hgt_objects['ToggleGroup_Life2.001'] = None
hgt_objects['ToggleGroup_MSG'] = None
hgt_objects['ToggleGroup_Plane'] = None
hgt_objects['ToggleGroup_Plane.001'] = None
hgt_objects['ToggleGroup_Plane.002'] = None
hgt_objects['ToggleGroup_Plane.003'] = None
hgt_objects['ToggleGroup_Plane.004'] = None
hgt_objects['ToggleGroup_Plane.005'] = None
hgt_objects['ToggleGroup_Plane.006'] = None
hgt_objects['ToggleGroup_Plane.007'] = None
hgt_objects['ToggleGroup_SCORE'] = None
hgt_objects['ToggleGroup_Sphere'] = None
hgt_objects['ToggleGroup_Sphere.001'] = None
hgt_objects['TransformInfo_BALL'] = None
hgt_objects['TransformInfo_Center'] = None
hgt_objects['TransformInfo_Cube'] = None
hgt_objects['TransformInfo_Cylinder'] = None
hgt_objects['TransformInfo_LASER'] = None
hgt_objects['TransformInfo_Life0'] = None
hgt_objects['TransformInfo_Life0.003'] = None
hgt_objects['TransformInfo_Life2'] = None
hgt_objects['TransformInfo_Life2.001'] = None
hgt_objects['TransformInfo_MSG'] = None
hgt_objects['TransformInfo_Plane'] = None
hgt_objects['TransformInfo_Plane.001'] = None
hgt_objects['TransformInfo_Plane.002'] = None
hgt_objects['TransformInfo_Plane.003'] = None
hgt_objects['TransformInfo_Plane.004'] = None
hgt_objects['TransformInfo_Plane.005'] = None
hgt_objects['TransformInfo_Plane.006'] = None
hgt_objects['TransformInfo_Plane.007'] = None
hgt_objects['TransformInfo_SCORE'] = None
hgt_objects['TransformInfo_Sphere'] = None
hgt_objects['TransformInfo_Sphere.001'] = None
hgt_objects['Transform_BALL'] = None
hgt_objects['Transform_Center'] = None
hgt_objects['Transform_Cube'] = None
hgt_objects['Transform_Cylinder'] = None
hgt_objects['Transform_LASER'] = None
hgt_objects['Transform_Life0'] = None
hgt_objects['Transform_Life0.003'] = None
hgt_objects['Transform_Life2'] = None
hgt_objects['Transform_Life2.001'] = None
hgt_objects['Transform_MSG'] = None
hgt_objects['Transform_Plane'] = None
hgt_objects['Transform_Plane.001'] = None
hgt_objects['Transform_Plane.002'] = None
hgt_objects['Transform_Plane.003'] = None
hgt_objects['Transform_Plane.004'] = None
hgt_objects['Transform_Plane.005'] = None
hgt_objects['Transform_Plane.006'] = None
hgt_objects['Transform_Plane.007'] = None
hgt_objects['Transform_SCORE'] = None
hgt_objects['Transform_Sphere'] = None
hgt_objects['Transform_Sphere.001'] = None
(world, nodes) = get_world_and_nodes(hgt_filename, hgt_objects)
