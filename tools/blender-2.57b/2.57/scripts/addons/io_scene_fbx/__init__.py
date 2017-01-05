# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "Autodesk FBX format",
    "author": "Campbell Barton",
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "File > Import-Export",
    "description": "Import-Export FBX meshes, UV's, vertex colors, materials, textures, cameras and lamps",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"\
        "Scripts/Import-Export/Autodesk_FBX",
    "tracker_url": "",
    "support": 'OFFICIAL',
    "category": "Import-Export"}

# To support reload properly, try to access a package var, if it's there, reload everything
if "bpy" in locals():
    import imp
    if "export_fbx" in locals():
        imp.reload(export_fbx)


import bpy
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty
import io_utils
from io_utils import ExportHelper


class ExportFBX(bpy.types.Operator, ExportHelper):
    '''Selection to an ASCII Autodesk FBX'''
    bl_idname = "export_scene.fbx"
    bl_label = "Export FBX"
    bl_options = {'PRESET'}

    filename_ext = ".fbx"
    filter_glob = StringProperty(default="*.fbx", options={'HIDDEN'})

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.

    use_selection = BoolProperty(name="Selected Objects", description="Export selected objects on visible layers", default=True)
# 	EXP_OBS_SCENE = BoolProperty(name="Scene Objects", description="Export all objects in this scene", default=True)
    global_scale = FloatProperty(name="Scale", description="Scale all data, (Note! some imports dont support scaled armatures)", min=0.01, max=1000.0, soft_min=0.01, soft_max=1000.0, default=1.0)

    global_rotate = EnumProperty(
            name="Rotate",
            options={'ENUM_FLAG'},
            items=(('X_90', "X 90", ""),
                   ('Y_90', "Y 90", ""),
                   ('Z_90', "Z 90", ""),
                   ),
            default={'X_90'},
            description="Global rotation to apply to the exported scene",
            )

    object_types = EnumProperty(
            name="Object Types",
            options={'ENUM_FLAG'},
            items=(('EMPTY', "Empty", ""),
                   ('CAMERA', "Camera", ""),
                   ('LAMP', "Lamp", ""),
                   ('ARMATURE', "Armature", ""),
                   ('MESH', "Mesh", ""),
                   ),
            default={'EMPTY', 'CAMERA', 'LAMP', 'ARMATURE', 'MESH'},
            )

    mesh_apply_modifiers = BoolProperty(name="Modifiers", description="Apply modifiers to mesh objects", default=True)

    mesh_smooth_type = EnumProperty(
            name="Smoothing",
            items=(('OFF', "Off", "Don't write smoothing"),
                   ('FACE', "Face", "Write face smoothing"),
                   ('EDGE', "Edge", "Write edge smoothing"),
                   ),
            default='FACE',
            )

#    EXP_MESH_HQ_NORMALS = BoolProperty(name="HQ Normals", description="Generate high quality normals", default=True)
    # armature animation
    ANIM_ENABLE = BoolProperty(name="Enable Animation", description="Export keyframe animation", default=True)
    ANIM_OPTIMIZE = BoolProperty(name="Optimize Keyframes", description="Remove double keyframes", default=True)
    ANIM_OPTIMIZE_PRECISSION = FloatProperty(name="Precision", description="Tolerence for comparing double keyframes (higher for greater accuracy)", min=1, max=16, soft_min=1, soft_max=16, default=6.0)
# 	ANIM_ACTION_ALL = BoolProperty(name="Current Action", description="Use actions currently applied to the armatures (use scene start/end frame)", default=True)
    ANIM_ACTION_ALL = BoolProperty(name="All Actions", description="Use all actions for armatures, if false, use current action", default=False)

    batch_mode = EnumProperty(
            name="Batch Mode",
            items=(('OFF', "Off", "Active scene to file"),
                   ('SCENE', "Scene", "Each scene as a file"),
                   ('GROUP', "Group", "Each group as a file"),
                   ),
            )

    BATCH_OWN_DIR = BoolProperty(name="Own Dir", description="Create a dir for each exported file", default=True)
    use_metadata = BoolProperty(name="Use Metadata", default=True, options={'HIDDEN'})

    path_mode = io_utils.path_reference_mode

    @property
    def check_extension(self):
        return self.batch_mode == 'OFF'

    def execute(self, context):
        import math
        from mathutils import Matrix
        if not self.filepath:
            raise Exception("filepath not set")

        mtx4_x90n = Matrix.Rotation(-math.pi / 2.0, 4, 'X')
        mtx4_y90n = Matrix.Rotation(-math.pi / 2.0, 4, 'Y')
        mtx4_z90n = Matrix.Rotation(-math.pi / 2.0, 4, 'Z')

        GLOBAL_MATRIX = Matrix()
        GLOBAL_MATRIX[0][0] = GLOBAL_MATRIX[1][1] = GLOBAL_MATRIX[2][2] = self.global_scale
        if 'X_90' in self.global_rotate:
            GLOBAL_MATRIX = mtx4_x90n * GLOBAL_MATRIX
        if 'Y_90' in self.global_rotate:
            GLOBAL_MATRIX = mtx4_y90n * GLOBAL_MATRIX
        if 'Z_90' in self.global_rotate:
            GLOBAL_MATRIX = mtx4_z90n * GLOBAL_MATRIX

        keywords = self.as_keywords(ignore=("global_rotate", "global_scale", "check_existing", "filter_glob"))
        keywords["GLOBAL_MATRIX"] = GLOBAL_MATRIX

        from . import export_fbx
        return export_fbx.save(self, context, **keywords)


def menu_func(self, context):
    self.layout.operator(ExportFBX.bl_idname, text="Autodesk FBX (.fbx)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
