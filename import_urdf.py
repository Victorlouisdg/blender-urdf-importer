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
    bpy.context.view_layer.update()
    return new_empty


def load_geometry(visual):
    geometry = visual.find('geometry')
    mesh = geometry.find('mesh')
    mesh_filename = mesh.attrib['filename']        
    mesh_filename = mesh_filename.replace('package://', '/home/victor/catkin_ws/src/')
    bpy.ops.wm.collada_import(filepath=mesh_filename)
    objs = [ob for ob in bpy.context.scene.objects if ob.type in ('CAMERA', 'LIGHT')]
    bpy.ops.object.delete({"selected_objects": objs})
        
    first_object = bpy.context.selected_objects[0]
    #first_object.name = link.attrib['name']
    
    for obj in bpy.context.selected_objects[1:]:
        obj.parent = first_object
        
    return first_object


def add_childjoints(link, empty, bone_name):
    childjoints = find_childjoints(joints, link)
    for childjoint in childjoints:
        new_empty = add_next_empty(empty, childjoint)
        
        if childjoint.attrib['type'] == 'revolute':
            axis = mathutils.Vector([float(s) for s in childjoint.find('axis').attrib['xyz'].split()])
            axis_world = new_empty.matrix_world.to_3x3() @ axis

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
        childlink_name = childjoint.find('child').attrib['link']
        
        
        # todo linkname -> link xml
        for childlink in links:
            if childlink.attrib['name'] == childlink_name:
                break
        
        print(childlink, childlink.attrib)
        
        # TODO load geometry here
        visual = childlink.find('visual')
        print('visual', visual)
        
        
        if visual:
            object = load_geometry(visual)
            select_only(object)
            #object.location = new_empty.location
            object.matrix_world = new_empty.matrix_world
            object.name = 'DEFORM_' + childjoint.attrib['name']
            bpy.context.scene.cursor.matrix = new_empty.matrix_world
            
            bpy.context.scene.transform_orientation_slots[0].type = 'CURSOR'
            
            
            translation = [float(s) for s in visual.find('origin').attrib['xyz'].split()]
            bpy.ops.transform.translate(value=translation, orient_type='CURSOR')
            
            roll, pitch, yaw = [float(s) for s in visual.find('origin').attrib['rpy'].split()]
            
            bpy.ops.transform.rotate(value=roll, orient_axis='X', orient_type='CURSOR')
            bpy.ops.transform.rotate(value=pitch, orient_axis='Y', orient_type='CURSOR')
            bpy.ops.transform.rotate(value=yaw, orient_axis='Z', orient_type='CURSOR')
            bpy.context.view_layer.update()
        
        add_childjoints(childlink_name, empty, bone_name)

for rootlink in rootlinks:
    bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.object.empty_display_size = 0.2
    empty = bpy.context.active_object
    empty.name = rootlink
    
    bpy.ops.object.armature_add(radius=0.05, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    armature  = bpy.context.active_object

    bone_name = bpy.context.active_bone.name
    bpy.data.objects['Armature'].data.bones[bone_name].name = 'base_link-base_link_inertia'
    bone_name = 'base_link-base_link_inertia'
    
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
    
    
bpy.ops.object.mode_set(mode='OBJECT')

select_only(armature)

for obj in bpy.data.objects:
    if 'DEFORM' in obj.name:
        obj.select_set(True)

bpy.ops.object.parent_set(type='ARMATURE_NAME')

def assign_vertices_to_group(object, groupname):
    select_only(object)
#    bpy.ops.object.mode_set(mode='EDIT')
#    bpy.ops.mesh.select_all(action='SELECT')
    
    group = object.vertex_groups[groupname]
    
    indices = [v.index for v in bpy.context.selected_objects[0].data.vertices]
    group.add(indices, 1.0, type='ADD')
#    bpy.ops.object.vertex_group_assign()
    
for object in bpy.data.objects:
    if 'DEFORM' in object.name:
        groupname = object.name.split('DEFORM_')[1]
        print(groupname)
        assign_vertices_to_group(object, groupname)

        # TODO assign all vertices to correct group
        # for all childern:
        # do the same