from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    pkg_robotik_gazebo = get_package_share_directory('robotik_gazebo')
    pkg_robotik_vision = get_package_share_directory('robotik_vision')
    model_path = os.path.join(pkg_robotik_vision, 'models')

    world_file = os.path.join(
        pkg_robotik_gazebo,
        'works',
        'pick_place_world.sdf'
    )

    set_gz_model_path = SetEnvironmentVariable(
    name='GZ_SIM_RESOURCE_PATH',
    value=model_path + ":" + os.environ.get("GZ_SIM_RESOURCE_PATH", "")
)

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', world_file],
        output='screen'
    )

    return LaunchDescription([
        set_gz_model_path,
        gazebo
    ])