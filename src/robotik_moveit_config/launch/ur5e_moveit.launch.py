from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():

    moveit = ExecuteProcess(
        cmd=[
            'ros2', 'launch',
            'ur_moveit_config',
            'ur_moveit.launch.py',
            'ur_type:=ur5e',
            'launch_rviz:=true'
        ],
        output='screen'
    )

    return LaunchDescription([
        moveit
    ])