"""6일차 C 추가 정밀 확인용 headless 통합 launch (저장소 코드 아님).

avoid.launch.py와 같은 Gazebo 서버, robot_state_publisher, 로봇 스폰,
detector/avoider 노드를 실행하되 GUI만 제외한다. GUI의 OpenGL 컨텍스트
생성 실패가 반복될 때 테스트를 계속하기 위한 임시 파일이다.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, LogInfo, OpaqueFunction,
                            SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _find_world(name):
    if os.path.isfile(name):
        return os.path.abspath(name)
    search_dirs = [
        os.path.join(get_package_share_directory('obstacle_avoider'), 'worlds'),
        os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'worlds'),
    ]
    for directory in search_dirs:
        for candidate in (name, name + '.world'):
            path = os.path.join(directory, candidate)
            if os.path.isfile(path):
                return path
    raise RuntimeError(f"world '{name}' not found")


def _launch_simulation(context):
    world = _find_world(LaunchConfiguration('world').perform(context))
    ros_gz_sim = get_package_share_directory('ros_gz_sim')
    gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    launch_dir = os.path.join(gazebo_dir, 'launch')
    gz_sim = os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')

    return [
        LogInfo(msg=f'[headless] world: {world}'),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH',
                                  os.path.join(gazebo_dir, 'models')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_sim),
            launch_arguments={
                'gz_args': ['-r -s -v2 ', world],
                'on_exit_shutdown': 'true',
            }.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'robot_state_publisher.launch.py')),
            launch_arguments={'use_sim_time': 'true'}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'spawn_turtlebot3.launch.py')),
            launch_arguments={
                'x_pose': LaunchConfiguration('x_pose'),
                'y_pose': LaunchConfiguration('y_pose'),
            }.items()),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='warehouse'),
        DeclareLaunchArgument('x_pose', default_value='-2.0'),
        DeclareLaunchArgument('y_pose', default_value='-0.5'),
        DeclareLaunchArgument('front_deg', default_value='30.0'),
        DeclareLaunchArgument('odom_topic', default_value='/odom'),
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
        OpaqueFunction(function=_launch_simulation),
        Node(
            package='obstacle_detector',
            executable='detector_node',
            name='detector_node',
            output='screen',
            parameters=[{'front_deg': LaunchConfiguration('front_deg')}],
        ),
        Node(
            package='obstacle_avoider',
            executable='avoider',
            name='avoider',
            output='screen',
            parameters=[{'odom_topic': LaunchConfiguration('odom_topic')}],
        ),
    ])
