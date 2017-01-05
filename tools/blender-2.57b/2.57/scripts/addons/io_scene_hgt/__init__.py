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

bl_info = {
    "name": "HGT format",
    "author": "Daniel Goude",
    "blender": (2, 5, 7),
    "api": 35622,
    "location": "File > Import-Export",
    "description": "Export HGT",
    "warning": "",
    "wiki_url": "http://curictus.com",
    "tracker_url": "",
    #"support": 'OFFICIAL',
    "category": "Import-Export"
}

if "bpy" in locals():
    import imp
    if "export_hgt" in locals():
        imp.reload(export_hgt)

import bpy
from bpy.props import BoolProperty
from io_utils import ExportHelper

class ExportHGT(bpy.types.Operator, ExportHelper):
    """Export selection to HGT file (.hgt)"""
    bl_idname = "export_scene.hgt"
    bl_label = 'Export HGT'

    filename_ext = ".hgt"
    #filter_glob = StringProperty(default="*.hgt", options={'HIDDEN'}

    use_sidecar = BoolProperty(name = "Write sidecar file", description = "Write a sidecar .py file", default = True)
    is_stylus = BoolProperty(name = "Export as stylus", description = "Export as an hgt stylus", default = False)
    nosave = BoolProperty(name = "Don't save original file", description = "Disable saving for testing", default = False)

    def execute(self, context):
        from . import export_hgt
        import imp
        imp.reload(export_hgt)
        return export_hgt.save(self, context, **self.as_keywords(ignore=("check_existing", "filter_glob")))
        """
        import io_scene_hgt.export_hgt
        import imp
        imp.reload(io_scene_hgt.export_hgt)
        return io_scene_hgt.export_hgt.save(self, context, **self.as_keywords())
        """

def menu_func_export(self, context):
    self.layout.operator(ExportHGT.bl_idname, text="HGT (.hgt)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
