from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    pkg_robotik_gazebo = get_package_share_directory('robotik_gazebo')
    pkg_robotik_vision = get_package_share_directory('robotik_vision')

    # Falls Modelle
    model_path = os.path.join(pkg_robotik_gazebo, 'models')

    world_file = os.path.join(
        pkg_robotik_gazebo,
        'works',
        'pick_place_world.sdf'
    )

    # Gazebo Resource Path setzen
    set_gz_model_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=model_path + ":" + os.environ.get("GZ_SIM_RESOURCE_PATH", "")
    )

    # Gazebo starten
    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', world_file],
        output='screen'
    )

    #ROS2  Gazebo Bridge für Kamera
    camera_bridge = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'ros_gz_bridge', 'parameter_bridge',
            '/gripper_camera/image@sensor_msgs/msg/Image@gz.msgs.Image'
        ],
        output='screen'
    )

    return LaunchDescription([
        set_gz_model_path,
        gazebo,
        camera_bridge
    ])