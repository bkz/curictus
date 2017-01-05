# Copyright Curictus AB

bl_info = {
    "name": "HGT Tools",
    "author": "Daniel Goude",
    "version": (0, 1),
    "blender": (2, 5, 7),
    "api": 35853,
    "location": "View3D > Tool Shelf > HGT Tools Panel",
    "description": "HGT Tools description",
    "warning": "",
    "wiki_url": "http://curictus.com",
    "tracker_url": "http://curictus.com",
    "category": "3D View",
}

"""HGT Tools comment"""

import bpy

class HGTTools(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    bl_label = "HGT Tools"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj != None:
            row = layout.row()
            row.label(text="Active object:", icon='OBJECT_DATA')
            row = layout.row()
            row.label(obj.name, icon='EDITMODE_HLT')
            row = layout.row()
            row.label("'Tis a " + obj.type)
            if obj.type == 'EMPTY':
                row = layout.row()
                row.label("DynamicTransform")
            row = layout.row()
            row.operator("export_scene.hgt",text="HGT Export...")
        box = layout.separator()

# Registration
def register():
    bpy.utils.register_module(__name__)

    pass

def unregister():
    bpy.utils.unregister_module(__name__)

    pass

if __name__ == "__main__":
    register()
