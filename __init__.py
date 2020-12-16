# Info displayed in the add-on overview.
bl_info = {
    'name': "URDF Importer",
    'description': "",
    'author': "Victor-Louis De Gusseme",
    'version': (0, 1),
    'blender': (2, 80, 0),
    'location': "View3D > Tool Shelf > Lightfield || "
                "Properties > Data",
    'wiki_url': '',
    'support': "COMMUNITY",
    'category': "Import"
}

# Importing in this init file is a bit weird.
if "bpy" in locals():
    print("Force reloading the plugin.")
    import importlib

    importlib.reload(import_urdf)
    importlib.reload(import_urdf_operator)

else:
    from . import import_urdf, \
        import_urdf_operator

import bpy


# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------
def make_annotations(cls):
    """Converts class fields to annotations if running with Blender 2.8"""
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls

# All classes to register.
classes = (
    URDF_OT_FilebrowserImporter,
    URDF_PT_Import,
)


# Register all classes + the collection property for storing lightfields
def register():
    # Classes
    for cls in classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)

    # Properties
    # bpy.types.Scene.lightfield = bpy.props.CollectionProperty(type=lightfield.LightfieldPropertyGroup)
    # bpy.types.Scene.lightfield_index = bpy.props.IntProperty(default=-1)

    # Menus
    #bpy.types.VIEW3D_MT_add.append(gui.add_lightfield)



# Unregister all classes + the collection property for storing lightfields
# This is done in reverse to 'pop the register stack'.
def unregister():
    # Remove items from menu
    #bpy.types.VIEW3D_MT_add.remove(gui.add_lightfield)

    # Remove properties
    # del bpy.types.Scene.lightfield_index
    # del bpy.types.Scene.lightfield

    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)