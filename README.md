<img src="https://download.blender.org/branding/blender_logo_socket.png" width="280"> <img src="https://www.ros.org/wp-content/uploads/2013/10/rosorg-logo1.png" width="250"/> 

# Blender URDF Importer
A minimalistic URDF file importer for Blender.
It allows you to bring your robot model into Blender and creates an armature so you can easily pose it.
This is an alpha version developed and tested for Blender 2.9.1 but should work for all versions since 2.8.
If you encounter issues with your URDF file or version of Blender, feel free to open an issue.

The armature created for the robot contains a bone for each revolute joint that can only rotate along the correct axis.
Joint limits, prismatic joints and planar joints are not supported yet.

## Installation
Currently the easiest way to install is to clone or download this repository and copy the `urdf_importer` directory into the addons directory for Blender (e.g. `/home/blender-2.91.0/2.91/scripts/addons`):

Then open Blender and in `Edit > Preferences > Add-ons` search for 'URDF Importer' and check the box.

## Usage
If the installation was succesful, you should see `URDF` as an option in the `File > Import` menu.

**Important note**: many URDF files reference mesh files inside ROS packages.
To find these mesh files, this addon relies on the environment variable `ROS_PACKAGE_PATH` to be set correctly.
This means that if the package that is referenced in the URDF file is in your catkin workspace, 
you have to source the `devel/setup.bash` file in your workspace first and then open Blender via the same terminal.


## How do I get an URDF file for my robot?
The ROS packages for URDF files are generally called `something_description`. 
For example, there's a ROS package [ur_description](https://github.com/ros-industrial/universal_robot) for the robots from Universal Robots.
However, you will often find that these packages don't contain the URDF files themselves.
Instead you will find `.xacro` files that you will have to use with the xacro command to generate the URDFs.

## How can I add inverse kinematics?
I recommend adding a bone to the armature in edit mode in front of the end effector (that is not its child). 
Then add an IK constraint to the end-effector and set the target bone to the newly created bone.

## Contributing
This is my first Blender addon so there's probably many ways to improve it.
If you have any ideas on how to do this, feel free to open a discussion or issue :)

You can also contact me at `victorlouisdg@gmail.com`
