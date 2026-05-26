from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_robotik_gazebo = get_package_share_directory('robotik_gazebo')

    world_file = os.path.join(
        pkg_robotik_gazebo,
        'works',
        'pick_place_world.sdf'
    )

    return LaunchDescription([
        ExecuteProcess(
            cmd=['gz', 'sim', world_file],
            output='screen'
        )
    ])
