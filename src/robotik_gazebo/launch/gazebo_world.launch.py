from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_robotik_gazebo = get_package_share_directory('robotik_gazebo')
    pkg_robotik_vision = get_package_share_directory('robotik_vision')
    pkg_ur_description = get_package_share_directory('ur_description')

    world_file = os.path.join(
        pkg_robotik_gazebo,
        'works',
        'pick_place_world.sdf'
    )

    resource_path = os.pathsep.join([
        os.path.join(pkg_robotik_vision, 'models'),
        os.path.dirname(pkg_ur_description)
    ])

    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=resource_path
    )

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', world_file],
        output='screen'
    )

    return LaunchDescription([
        set_gz_resource_path,
        gazebo
    ])