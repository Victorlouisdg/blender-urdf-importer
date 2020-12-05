from os import path
import xml.etree.ElementTree as ET
import bpy
import mathutils


filepath = r'C:\Users\Administrator\Blender\urdf_testing\ur10.urdf'
#filepath = '/home/victor/ur10.urdf'

print(filepath)

if not path.exists(filepath):
    print('File does not exist')

tree = ET.parse(filepath)
xml_root = tree.getroot()


links = xml_root.findall('link')
joints = xml_root.findall('joint')


def find_rootlinks(joints):
    """Return all links that don't occur as child in any joint"""
    parents = []
    childern = []
    for joint in joints:
        parents.append(joint.find('parent').attrib['link'])
        childern.append(joint.find('child').attrib['link'])

    rootlinks = list(set(parents) - set(childern))
    return rootlinks

rootlinks = find_rootlinks(joints)

def find_childjoints(joints, link):
    """Returns all joints that contain the link as parent"""
    childjoints = []
    for joint in joints:
        if joint.find('parent').attrib['link'] == link:
            childjoints.append(joint)
    return childjoints
        
    
def select_only(blender_object):
    """Selects and actives a Blender object and deselects all others"""
    print('MODE IS:', bpy.context.mode)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = blender_object
    blender_object.select_set(True)
    
    
def add_next_empty(empty, joint):
    """Duplicates the empty and applies the transform specified in the joint"""
    select_only(empty)
    
    bpy.ops.object.duplicate()
    new_empty = bpy.context.active_object
    new_empty.name = joint.attrib['name']
    
    translation = [float(s) for s in joint.find('origin').attrib['xyz'].split()]
    bpy.ops.transform.translate(value=translation, orient_type='LOCAL')
    
    roll, pitch, yaw = [float(s) for s in joint.find('origin').attrib['rpy'].split()]    
    new_empty.rotation_euler.rotate_axis("X", roll)
    new_empty.rotation_euler.rotate_axis("Y", pitch)
    new_empty.rotation_euler.rotate_axis("Z", yaw)
    return new_empty
    
        
def add_childjoints(link, empty, bone):
    childjoints = find_childjoints(joints, link)
    for childjoint in childjoints:
        new_empty = add_next_empty(empty, childjoint)
        
        print('MODE IS:', bpy.context.mode)
       
        armature_object = bpy.data.objects['Armature']
        select_only(armature_object)
        
        bpy.ops.object.mode_set(mode='EDIT')

        for b in armature_object.data.edit_bones: # deselect the other bones
            b.select = False
            b.select_tail = False
            b.select_head = False

        bone.select_tail = True
                
        bpy.ops.armature.extrude_move(TRANSFORM_OT_translate={"value":new_empty.location.xyz, "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL'})
        
        new_bone = 
        
        bpy.ops.object.mode_set(mode='OBJECT')
#        
#        new_tail= bpy.context.active_object
#        
#        child_link = child_joint.find('child').attrib['link']
        #recurse(child_link, new_empty, new_tail)
    

# TODO check spec whether multiple roots can even exist

for rootlink in rootlinks:
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.empty_display_size = 0.2
    empty = bpy.context.active_object
    empty.name = rootlink
    
    bpy.ops.object.armature_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, -1), scale=(1, 1, 1))
    armature  = bpy.context.active_object
    
    bpy.ops.object.mode_set(mode='EDIT')
    bone = armature.data.edit_bones['Bone']
    bpy.ops.object.mode_set(mode='OBJECT')
    add_childjoints(rootlink, empty, bone)  


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