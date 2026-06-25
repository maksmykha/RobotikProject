from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os
import xacro

def generate_launch_description():
    pkg_gazebo = get_package_share_directory('robotik_gazebo')
    pkg_desc   = get_package_share_directory('robotik_description')

    world_file = os.path.join(pkg_gazebo, 'works', 'pick_place_world.sdf')
    xacro_file = os.path.join(pkg_desc, 'urdf', 'ur5e.urdf.xacro')
    robot_desc = xacro.process_file(xacro_file).toxml()

    try:
        pkg_vision = get_package_share_directory('robotik_vision')
        model_path = os.path.join(pkg_vision, 'models')
    except Exception:
        model_path = os.path.join(pkg_gazebo, 'models')

    gz_env = {
        # Mesh-Fix: ur_description Meshes fuer Gazebo sichtbar machen
        'GZ_SIM_RESOURCE_PATH': model_path + ':/opt/ros/jazzy/share',
        'GZ_SIM_SYSTEM_PLUGIN_PATH': '/opt/ros/jazzy/lib',
        'LD_LIBRARY_PATH': '/opt/ros/jazzy/lib:' + os.environ.get('LD_LIBRARY_PATH', ''),
    }

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_desc, 'use_sim_time': True}]
        ),
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', world_file],
            output='screen',
            additional_env=gz_env,
        ),
        TimerAction(period=2.0, actions=[
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name='clock_bridge',
                output='screen',
                arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            ),
        ]),
        TimerAction(period=3.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'run', 'ros_gz_sim', 'create',
                     '-topic', 'robot_description',
                     '-name', 'ur5e',
                     '-x', '0.0', '-y', '0.0', '-z', '0.77'],
                output='screen'
            ),
        ]),
        TimerAction(period=8.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'control', 'load_controller',
                     '--set-state', 'active', 'joint_state_broadcaster'],
                output='screen'
            ),
        ]),
        TimerAction(period=10.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'control', 'load_controller',
                     '--set-state', 'active', 'arm_controller'],
                output='screen'
            ),
        ]),
        TimerAction(period=5.0, actions=[
            ExecuteProcess(
                cmd=['ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
                     '/gripper_camera/image@sensor_msgs/msg/Image@gz.msgs.Image'],
                output='screen'
            ),
        ]),
    ])
