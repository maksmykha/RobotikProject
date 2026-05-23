import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/maksmykha/Documents/RobotikProject/install/robotik_gazebo'
