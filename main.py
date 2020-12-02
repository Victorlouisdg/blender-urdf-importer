from os import path
import xml.etree.ElementTree as ET
import bpy

filepath = '/home/victor/ur10.urdf'

print(filepath)

if not path.exists(filepath):
    print('File does not exist')

tree = ET.parse(filepath)
root = tree.getroot()

print(root.attrib)

links = []
joints = []

for child in root:
    print(child.tag, child.attrib)
    if child.tag == 'link':
        links.append(child)
    elif child.tag == 'joint':
        joints.append(child)
i = 0
for link in links:
    print(link.attrib)
    visual = link.find('visual')
    
    if(visual): #and link.attrib['name'] == 'shoulder_link'):
        print(link.attrib, 'has visual')
        geometry = visual.find('geometry')
        mesh = geometry.find('mesh')
        mesh_filename = mesh.attrib['filename']
        print(mesh_filename)
        
#        if 'package://' in mesh_filename:
#            print('Your URDF file uses package:// to refer to mesh files, please specify this path explicitly.')
            
        mesh_filename = mesh_filename.replace('package://', '/home/victor/catkin_ws/src/')
        
        imported_object = bpy.ops.wm.collada_import(filepath=mesh_filename)
        
        print('OBJECT', imported_object)
        
        
        
        objs = [ob for ob in bpy.context.scene.objects if ob.type in ('CAMERA', 'LIGHT')]
        bpy.ops.object.delete({"selected_objects": objs})
        
        print(bpy.context.selected_objects)
        
        first_object = bpy.context.selected_objects[0]
        first_object.name = link.attrib['name']
        
        for obj in bpy.context.selected_objects[1:]:
            obj.parent = first_object
        
        
        print(mesh_filename)
    
        

print('ok')