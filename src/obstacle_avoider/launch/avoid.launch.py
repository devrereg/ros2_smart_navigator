"""detector_node와 avoider를 함께 실행하는 통합 launch 파일."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    gazebo_dir = get_package_share_directory('turtlebot3_gazebo')

    return LaunchDescription([
        # sim:=false 이면 이미 떠 있는 시뮬레이션에 감지/회피 노드만 붙인다.
        DeclareLaunchArgument('sim', default_value='true',
                              description='true이면 TurtleBot3 월드 시뮬레이션도 함께 실행'),
        # front_deg: 정면 기준 전체 폭(도). 30이면 좌우 15도
        DeclareLaunchArgument('front_deg', default_value='30.0',
                              description='전방 감지 구간 전체 폭(도)'),
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_dir, 'launch', 'turtlebot3_world.launch.py')),
            condition=IfCondition(LaunchConfiguration('sim')),
        ),
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
        ),
    ])
