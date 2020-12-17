import os
import glob
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
    new_empty.name = 'TF_' + joint.attrib['name']

    
    translation = [float(s) for s in joint.find('origin').attrib['xyz'].split()]
    bpy.ops.transform.translate(value=translation, orient_type='LOCAL')

    bpy.context.scene.cursor.matrix = new_empty.matrix_world
    
    roll, pitch, yaw = [float(s) for s in joint.find('origin').attrib['rpy'].split()]    

    bpy.ops.transform.rotate(value=roll, orient_axis='X', orient_type='CURSOR')
    bpy.ops.transform.rotate(value=pitch, orient_axis='Y', orient_type='CURSOR')
    bpy.ops.transform.rotate(value=yaw, orient_axis='Z', orient_type='CURSOR')

    bpy.context.view_layer.update()
    return new_empty


def parse_mesh_filename(mesh_filename):
    """This function will return the mesh path if it can be found, else throw an error"""
    if os.path.exists(mesh_filename):
        return mesh_filename
    
    if 'package://' in mesh_filename:
        ros_package_paths = os.environ.get('ROS_PACKAGE_PATH')
        if ros_package_paths is None:
            error_msg = (
                'Your urdf file references a mesh file from a ROS package: \n'
                f'{mesh_filename}\n'
                'However, the ROS_PACKAGE_PATH environment variable is not set ' 
                'so we cannot find it.'
            )
            print(error_msg)
            # TODO throw error
            
        ros_package_paths = ros_package_paths.split(':')
        for ros_package_path in ros_package_paths:
            filepath_package = mesh_filename.replace('package://', '')
            
            filepath_split = filepath_package.split('/')
            package_name = filepath_split[0]
            filepath_in_package = os.path.join(*filepath_split[1:])
            
            # TODO recursive search in ros_package_path for package_path
            for package_path in glob.glob(ros_package_path + '/**/' + package_name):
                filepath = os.path.join(package_path, filepath_in_package)

                print(filepath, os.path.exists(filepath))
                if os.path.exists(filepath):
                    return filepath
        
    print('Cant find the mesh file :(')
    # TODO if we get here, throw an error


def load_mesh(mesh):
    mesh_filename = mesh.attrib['filename']
    mesh_path = parse_mesh_filename(mesh_filename)
    bpy.ops.wm.collada_import(filepath=mesh_path)
    objects_to_delete = [o for o in bpy.context.scene.objects if o.type in ('CAMERA', 'LIGHT')]
    bpy.ops.object.delete({"selected_objects": objects_to_delete})
    objects = bpy.context.selected_objects
    return objects


def load_geometry(visual):
    geometry = visual.find('geometry')

    mesh = geometry.find('mesh')
    if mesh:
        return load_mesh(mesh)

    cylinder = geometry.find('cyclinder')
    if cylinder:
        length = cylinder.attrib['length']
        radius = cylinder.attrib['radius']
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=length, enter_editmode=False, align='WORLD')
        return [bpy.context.active_object]

    return []



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

    bpy.ops.object.mode_set(mode='POSE')

    posebone = armature.pose.bones[bone_name]

    posebone.rotation_mode = 'XYZ'
    posebone.lock_rotation[0] = True
    posebone.lock_rotation[1] = False
    posebone.lock_rotation[2] = True

    posebone.lock_ik_x = True
    posebone.lock_ik_y = False
    posebone.lock_ik_z = True

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


def add_childjoints(armature, joints, links, link, empty, parent_bone_name):
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
            position_link_objects(visual, objects, new_empty, bone_name)
        
        add_childjoints(armature, joints, links, childlink_name, new_empty, bone_name)


def assign_vertices_to_group(object, groupname):
    select_only(object)
    group = object.vertex_groups[groupname]
    indices = [v.index for v in bpy.context.selected_objects[0].data.vertices]
    group.add(indices, 1.0, type='ADD')


def import_urdf(filepath):
    if not os.path.exists(filepath):
        print('File does not exist')

    tree = ET.parse(filepath)
    xml_root = tree.getroot()

    links = xml_root.findall('link')
    joints = xml_root.findall('joint')

    if joints:
        rootlinks = find_rootlinks(joints)
    else:
        rootlinks = [link.attrib['name'] for link in links]

    for rootlink in rootlinks:
        bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.context.object.empty_display_size = 0.2
        empty = bpy.context.active_object
        empty.name = 'TF_' + rootlink
        
        bpy.ops.object.armature_add(radius=0.05, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))    
        armature = bpy.context.active_object

        bone_name = 'root'
        bpy.context.active_bone.name = bone_name

        select_only(armature)
        bpy.ops.object.mode_set(mode='POSE')
        armature.pose.bones[bone_name].lock_ik_x = True
        armature.pose.bones[bone_name].lock_ik_y = True
        armature.pose.bones[bone_name].lock_ik_z = True
        bpy.ops.object.mode_set(mode='OBJECT')

        visual = rootlink.find('visual')
        # TODO add this visual

        add_childjoints(armature, joints, links, rootlink, empty, bone_name)

        ## Skinning
        select_only(armature)

        for object in bpy.data.objects:
            if 'DEFORM__' in object.name:
                object.select_set(True)


        bpy.ops.object.shade_flat()            
        bpy.ops.object.parent_set(type='ARMATURE_NAME')

        for object in bpy.data.objects:
            if 'DEFORM__' in object.name:
                groupname = object.name.split('__')[1]
                assign_vertices_to_group(object, groupname)

        # Delete the empties
        # bpy.ops.object.select_all(action='DESELECT') 
        # for object in bpy.data.objects:
        #     if 'TF_' in object.name:
        #         object.select_set(True)
        # bpy.ops.object.delete() 
    
    
if __name__ == '__main__':
    filepath = '/home/idlab185/ur10.urdf'
    import_urdf(filepath)
