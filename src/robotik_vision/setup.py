from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'robotik_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
   	(
    	os.path.join(
        	'share',
        	package_name,
        	'models',
        	'gripper_depth_camera'
    	),
    	glob('models/gripper_depth_camera/*')
	), ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maksmykha',
    maintainer_email='mykhailich@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'color_detector_node = robotik_vision.color_detector_node:main',
        'manual_target_selector_node = robotik_vision.manual_target_selector_node:main',
        'target_pose_node = robotik_vision.target_pose_node:main',
    ],
},
)
