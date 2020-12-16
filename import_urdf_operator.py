from . import import_urdf
import bpy
from bpy_extras.io_utils import ImportHelper 
from bpy.types import Operator


class URDF_OT_FilebrowserImporter(Operator, ImportHelper): 

    bl_idname = "import.urdf_filebrowser" 
    bl_label = "Import URDF" 

    def execute(self, context): 
        """Do something with the selected file(s).""" 
        print(self.filepath)
        return {'FINISHED'}
    
    
class URDF_PT_Import(bpy.types.Panel):
    bl_label = 'URDF'
    bl_idname = 'URDF_PT_Import'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator('import.urdf_filebrowser', icon='IMPORT')



    
classes = (
    URDF_OT_FilebrowserImporter,
    URDF_PT_Import,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == '__main__':
    import os
    print(__package__)
    print(os.getcwd())
    register()