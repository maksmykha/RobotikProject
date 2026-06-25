from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    return LaunchDescription([
        ExecuteProcess(
            cmd=[
                'ros2', 'launch',
                'ur_moveit_config',
                'ur_moveit.launch.py',
                'ur_type:=ur5e',
                'launch_rviz:=true',
                'use_sim_time:=true',
            ],
            output='screen'
        )
    ])
