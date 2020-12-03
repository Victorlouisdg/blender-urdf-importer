from os import path
import xml.etree.ElementTree as ET
import bpy
import mathutils

def load_geometry(visual):
    geometry = visual.find('geometry')
    mesh = geometry.find('mesh')
    mesh_filename = mesh.attrib['filename']        
    mesh_filename = mesh_filename.replace('package://', '/home/victor/catkin_ws/src/')
    bpy.ops.wm.collada_import(filepath=mesh_filename)
    objs = [ob for ob in bpy.context.scene.objects if ob.type in ('CAMERA', 'LIGHT')]
    bpy.ops.object.delete({"selected_objects": objs})
        
    first_object = bpy.context.selected_objects[0]
    first_object.name = link.attrib['name']
    
    for obj in bpy.context.selected_objects[1:]:
        obj.parent = first_object
        
#    position = [float(s) for s in visual.find('origin').attrib['xyz'].split()]
#    rotation = [float(s) for s in visual.find('origin').attrib['rpy'].split()]
#    
#    bpy.ops.object.select_all(action='DESELECT')
#    first_object.select_set(True)
#    
#    eul = mathutils.Euler(rotation, 'XYZ')
#    mat_rot = eul.to_matrix().to_4x4()
#    
    #first_object.matrix_world = first_object.matrix_world @ mat_rot
    #bpy.ops.transform.translate(value=position, orient_type='LOCAL')
#    bpy.ops.transform.translate(value=position)
    
    

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
        load_geometry(visual)
    else:
        o = bpy.data.objects.new( "empty", None)
        bpy.context.scene.collection.objects.link(o)
        o.empty_display_size = 0.2
        o.name = link.attrib['name']
        




for joint in joints:
    parent_link = joint.find('parent').attrib['link']
    child_link = joint.find('child').attrib['link']
    bpy.data.objects[child_link].parent = bpy.data.objects[parent_link]
    
    
for joint in joints:
    parent_link = joint.find('parent').attrib['link']
    child_link = joint.find('child').attrib['link']

    position = [float(s) for s in joint.find('origin').attrib['xyz'].split()]
    rotation = [float(s) for s in joint.find('origin').attrib['rpy'].split()]

    eul = mathutils.Euler(rotation, 'XYZ')
    mat_rot = eul.to_matrix().to_4x4()
    
        
    print(bpy.data.objects[child_link].matrix_world)
    print(mat_rot.to_4x4())
    
    #bpy.data.objects[child_link].matrix_world = bpy.data.objects[child_link].matrix_world @ mat_rot
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[child_link].select_set(True)
    #bpy.ops.transform.rotate(orient_matrix=mat_rot)
    #bpy.ops.transform.translate(value=position)

#    
#    #bpys.objects[]
#    
    

    
    
print('ok')