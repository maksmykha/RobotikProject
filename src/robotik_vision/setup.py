from setuptools import find_packages, setup
from glob import glob

package_name = 'robotik_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models/gripper_depth_camera',
            glob('models/gripper_depth_camera/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='maksmykha',
    maintainer_email='mykhailich@gmail.com',
    description='Color detection vision package',
    license='TODO: License declaration',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'color_detector = robotik_vision.color_detector_node:main',
            'manual_target_selector = robotik_vision.manual_target_selector_node:main',
            'target_pose = robotik_vision.target_pose_node:main',
        ],
    },
)
