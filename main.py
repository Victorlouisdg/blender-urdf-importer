from os import path
import xml.etree.ElementTree as ET
import bpy
import mathutils



filepath = '/home/victor/ur10.urdf'

print(filepath)

if not path.exists(filepath):
    print('File does not exist')

tree = ET.parse(filepath)
xml_root = tree.getroot()


links = []
joints = []

# TODO check if we can get all elements in tree with tag
for child in xml_root:
    print(child.tag, child.attrib)
    if child.tag == 'link':
        links.append(child)
    elif child.tag == 'joint':
        joints.append(child)

# findall()

parents = []
childern = []

for joint in joints:
    parents.append(joint.find('parent').attrib['link'])
    childern.append(joint.find('child').attrib['link'])


root_links = list(set(parents) - set(childern))

print('p', parents)
print('c', childern)

print('root_links', root_links)


def find_child_joints(joints, link):
    # vindt alle joints met link als parent
    
    child_joints = []
    
    for joint in joints:
        if joint.find('parent').attrib['link'] == link:
            child_joints.append(joint)
    return child_joints
        
        
def recurse(link, empty):
    child_joints = find_child_joints(joints, link)
    print(child_joints)
    for child_joint in child_joints:
        bpy.context.view_layer.objects.active = empty
        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
        new_empty = bpy.context.active_object
        new_empty.name = child_joint.attrib['name']
        
        translation = [float(s) for s in child_joint.find('origin').attrib['xyz'].split()]
        
        bpy.ops.transform.translate(value=translation, orient_type='LOCAL')
        
        roll, pitch, yaw = [float(s) for s in child_joint.find('origin').attrib['rpy'].split()]
        
        print('rpy', roll, pitch, yaw)
        
        new_empty.rotation_euler.rotate_axis("X", roll)
        new_empty.rotation_euler.rotate_axis("Y", pitch)
        new_empty.rotation_euler.rotate_axis("Z", yaw)
        
        
        
        # TODO add bones here
        
        child_link = child_joint.find('child').attrib['link']
        recurse(child_link, new_empty)
    

# TODO check spec whether multiple roots can even exist
for root_link in root_links:
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.empty_display_size = 0.2
    empty = bpy.context.active_object
    empty.name = root_link
    recurse(root_link, empty)
        
        
    
   
            


# TODO 


#for joint in joints:
#    parent_link = joint.find('parent').attrib['link']
#    child_link = joint.find('child').attrib['link']
#    
##for joint in joints:
##    parent_link = joint.find('parent').attrib['link']
##    child_link = joint.find('child').attrib['link']
##    bpy.data.objects[child_link].parent = bpy.data.objects[parent_link]
#    
#    
#for joint in joints:
#    parent_link = joint.find('parent').attrib['link']
#    child_link = joint.find('child').attrib['link']

#    position = [float(s) for s in joint.find('origin').attrib['xyz'].split()]
#    rotation = [float(s) for s in joint.find('origin').attrib['rpy'].split()]

#    eul = mathutils.Euler(rotation, 'XYZ')
#    mat_rot = eul.to_matrix().to_4x4()
#    
#        
#    print(bpy.data.objects[child_link].matrix_world)
#    print(mat_rot.to_4x4())
#    
#    #bpy.data.objects[child_link].matrix_world = bpy.data.objects[child_link].matrix_world @ mat_rot
#    
#    bpy.ops.object.select_all(action='DESELECT')
#    bpy.data.objects[child_link].select_set(True)
#    #bpy.ops.transform.rotate(orient_matrix=mat_rot)
#    #bpy.ops.transform.translate(value=position)

##    
##    #bpys.objects[]
##    
#    

#    
#    
#print('ok')