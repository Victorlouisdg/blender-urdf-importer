from os import path
import xml.etree.ElementTree as ET
import bpy
import mathutils
import numpy as np


def find_rootlinks(joints):
    """Return all links that don't occur as child in any joint"""
    parents = []
    children = []
    for joint in joints:
        parents.append(joint.find('parent').attrib['link'])
        children.append(joint.find('child').attrib['link'])

    rootlinks = list(set(parents) - set(children))
    return rootlinks


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
    bpy.context.view_layer.update()
    return new_empty


def load_geometry(visual):
    geometry = visual.find('geometry')
    mesh = geometry.find('mesh')
    mesh_filename = mesh.attrib['filename']
    # TODO fix this, maybe by using rospack or ENV variable
    mesh_filename = mesh_filename.replace('package://', '/home/victor/catkin_ws/src/')
    bpy.ops.wm.collada_import(filepath=mesh_filename)
    objects_to_delete = [o for o in bpy.context.scene.objects if o.type in ('CAMERA', 'LIGHT')]
    bpy.ops.object.delete({"selected_objects": objects_to_delete})
    objects = bpy.context.selected_objects
    return objects


def add_revolute_joint_bone(armature, joint, empty, parent_bone_name):
    axis = mathutils.Vector([float(s) for s in joint.find('axis').attrib['xyz'].split()])
    axis_world = empty.matrix_world.to_3x3() @ axis

    select_only(armature)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = armature.data.edit_bones.new(joint.attrib['name'])
    eb.head = empty.location
    eb.tail = empty.location + axis_world / 10
    eb.parent = armature.data.edit_bones[parent_bone_name]
    bone_name = eb.name
    bpy.ops.object.mode_set(mode='OBJECT')
    return bone_name


def position_link_objects(visual, objects, empty, joint_name):
    for i, object in enumerate(objects):
        select_only(object)
        object.matrix_world = empty.matrix_world
        object.name = 'DEFORM__' + joint_name + '__' + str(i)
        bpy.context.scene.cursor.matrix = empty.matrix_world

        translation = [float(s) for s in visual.find('origin').attrib['xyz'].split()]
        bpy.ops.transform.translate(value=translation, orient_type='CURSOR')

        roll, pitch, yaw = [float(s) for s in visual.find('origin').attrib['rpy'].split()]

        bpy.ops.transform.rotate(value=roll, orient_axis='X', orient_type='CURSOR')
        bpy.ops.transform.rotate(value=pitch, orient_axis='Y', orient_type='CURSOR')
        bpy.ops.transform.rotate(value=yaw, orient_axis='Z', orient_type='CURSOR')
        bpy.context.view_layer.update()


def add_childjoints(armature, link, empty, parent_bone_name):
    childjoints = find_childjoints(joints, link)
    for childjoint in childjoints:
        new_empty = add_next_empty(empty, childjoint)
        
        bone_name = parent_bone_name
        
        if childjoint.attrib['type'] == 'revolute':
            bone_name = add_revolute_joint_bone(armature, childjoint, new_empty, parent_bone_name)
            
        # Find the childlink xml object
        childlink_name = childjoint.find('child').attrib['link']
        for childlink in links:
            if childlink.attrib['name'] == childlink_name:
                break
        
        visual = childlink.find('visual')
        
        if visual:
            objects = load_geometry(visual)
            position_link_objects(visual, objects, new_empty, childjoint.attrib['name'])
        
        add_childjoints(armature, childlink_name, new_empty, bone_name)



filepath = '/home/victor/ur10.urdf'

if not path.exists(filepath):
    print('File does not exist')

tree = ET.parse(filepath)
xml_root = tree.getroot()

links = xml_root.findall('link')
joints = xml_root.findall('joint')
rootlinks = find_rootlinks(joints)

for rootlink in rootlinks:
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.empty_display_size = 0.2
    empty = bpy.context.active_object
    empty.name = rootlink
    
    bpy.ops.object.armature_add(radius=0.05, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))    
    armature = bpy.context.active_object

    bone_name = 'root' #'base_link-base_link_inertia'
    # find joint with rootlink as parent
    
    bpy.context.active_bone.name = bone_name

    add_childjoints(armature, rootlink, empty, bone_name)
    

# Adding and locking the IK
armature = bpy.data.objects['Armature']
eef = armature.data.bones['wrist_3_joint']
eef_position = eef.tail_local

select_only(armature)
bpy.ops.object.mode_set(mode='EDIT')
eb = armature.data.edit_bones.new('target_bone')
eef_forward = mathutils.Vector(eef.matrix_local[1][0:3])
print(eef.matrix_local)
print(eef_forward)

eb.head = eef_position
eb.tail = eef_position + 0.1 * eef_forward

bpy.ops.object.mode_set(mode='POSE')

armature.pose.bones['wrist_3_joint'].bone.select = True
armature.pose.bones['wrist_3_joint'].constraints.new('IK')
bpy.context.object.pose.bones["wrist_3_joint"].constraints["IK"].target = armature
bpy.context.object.pose.bones["wrist_3_joint"].constraints["IK"].subtarget = "target_bone"
bpy.context.object.pose.bones["wrist_3_joint"].constraints["IK"].use_rotation = True


for posebone in armature.pose.bones:
    posebone.lock_ik_x = True
    posebone.lock_ik_y = False
    posebone.lock_ik_z = True
    
    
bpy.ops.object.mode_set(mode='OBJECT')

select_only(armature)

for object in bpy.data.objects:
    if 'DEFORM' in object.name:
        object.select_set(True)

        
bpy.ops.object.shade_flat()            
bpy.ops.object.parent_set(type='ARMATURE_NAME')

def assign_vertices_to_group(object, groupname):
    select_only(object)
    group = object.vertex_groups[groupname]
    indices = [v.index for v in bpy.context.selected_objects[0].data.vertices]
    group.add(indices, 1.0, type='ADD')

    
for object in bpy.data.objects:
    if 'DEFORM' in object.name:
        groupname = object.name.split('__')[1]
        assign_vertices_to_group(object, groupname)