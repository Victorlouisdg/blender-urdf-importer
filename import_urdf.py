from os import path
import xml.etree.ElementTree as ET
import bpy
import mathutils
import numpy as np

filepath = '/home/victor/ur10.urdf'

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


def add_childjoints(link, empty, bone_name):
    childjoints = find_childjoints(joints, link)
    for childjoint in childjoints:
        new_empty = add_next_empty(empty, childjoint)
        
        
        
        if childjoint.attrib['type'] == 'revolute':
            print('rev', childjoint.find('axis').attrib['xyz'])
            
            axis = mathutils.Vector([float(s) for s in childjoint.find('axis').attrib['xyz'].split()])
#            print(axis)
#            print(new_empty.matrix_world)
#            print(new_empty.matrix_world.to_3x3())

            axis_world = new_empty.matrix_world.to_3x3() @ axis
#            print(new_empty.matrix_world.to_translation())
            print(new_empty.location)
#            print(axis_world)

            armature = bpy.data.objects['Armature']
            select_only(armature)
            bpy.ops.object.mode_set(mode='EDIT')
            eb = armature.data.edit_bones.new(childjoint.attrib['name'])
            eb.head = new_empty.location
            eb.tail = new_empty.location + axis_world / 10
            eb.parent = armature.data.edit_bones[bone_name]
            bone_name = eb.name
            bpy.ops.object.mode_set(mode='OBJECT')
            
            
        empty = new_empty
        childlink = childjoint.find('child').attrib['link']
        add_childjoints(childlink, empty, bone_name)

for rootlink in rootlinks:
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.empty_display_size = 0.2
    empty = bpy.context.active_object
    empty.name = rootlink
    
    bpy.ops.object.armature_add(radius=0.05, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    armature  = bpy.context.active_object

    bone_name = bpy.context.active_bone.name
    add_childjoints(rootlink, empty, bone_name)
    

# Adding and locking the IK
armature = bpy.data.objects['Armature']
eef = armature.data.bones['wrist_3_joint']
eef_position = eef.tail_local

select_only(armature)
bpy.ops.object.mode_set(mode='EDIT')
eb = armature.data.edit_bones.new('TargetBone')
eb.head = eef_position + mathutils.Vector((0.0, 0.0, 0.0))
eb.tail = eef_position + mathutils.Vector((0.0, 0.0, 0.1))

bpy.ops.object.mode_set(mode='POSE')

armature.pose.bones['wrist_3_joint'].bone.select = True
armature.pose.bones['wrist_3_joint'].constraints.new('IK')
bpy.context.object.pose.bones["wrist_3_joint"].constraints["IK"].target = armature
bpy.context.object.pose.bones["wrist_3_joint"].constraints["IK"].subtarget = "TargetBone"

for posebone in armature.pose.bones:
    posebone.lock_ik_x = True
    posebone.lock_ik_y = False
    posebone.lock_ik_z = True