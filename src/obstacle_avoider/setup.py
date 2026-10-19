from glob import glob

from setuptools import find_packages, setup

package_name = 'obstacle_avoider'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        # 저장소 루트의 worlds/ (colcon은 패키지 디렉토리에서 setup.py를 실행한다)
        ('share/' + package_name + '/worlds', glob('../../worlds/*.world')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jjk27',
    maintainer_email='jjk27@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'manual_drive = obstacle_avoider.manual_drive:main',
            'avoider = obstacle_avoider.avoider:main',
        ],
    },
)
