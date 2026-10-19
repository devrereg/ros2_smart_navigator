"""detector_node와 avoider를 함께 실행하는 통합 launch 파일."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, LogInfo, OpaqueFunction,
                            SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _find_world(name):
    """world 인자(경로 또는 이름)를 실제 파일 경로로 바꾼다.

    탐색 순서: 존재하는 경로 -> obstacle_avoider/worlds -> turtlebot3_gazebo/worlds
    """
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
    available = sorted(
        f[:-len('.world')] for d in search_dirs if os.path.isdir(d)
        for f in os.listdir(d) if f.endswith('.world'))
    raise RuntimeError(
        f"world '{name}'을(를) 찾을 수 없습니다. 사용 가능: {', '.join(available)}")


def _launch_simulation(context):
    """Gazebo 서버/GUI를 world 인자로 받은 맵으로 띄우고 로봇을 스폰한다."""
    world = _find_world(LaunchConfiguration('world').perform(context))
    ros_gz_sim = get_package_share_directory('ros_gz_sim')
    gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    launch_dir = os.path.join(gazebo_dir, 'launch')
    gz_sim = os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')

    actions = [
        LogInfo(msg=f'[avoid.launch] world: {world}'),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.path.join(gazebo_dir, 'models')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_sim),
            launch_arguments={'gz_args': ['-r -s -v2 ', world],
                              'on_exit_shutdown': 'true'}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_sim),
            launch_arguments={'gz_args': '-g -v2 ',
                              'on_exit_shutdown': 'true'}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'robot_state_publisher.launch.py')),
            launch_arguments={'use_sim_time': 'true'}.items()),
    ]
    if LaunchConfiguration('spawn_robot').perform(context).lower() == 'true':
        # 로봇 스폰 + ros_gz_bridge(parameter_bridge, turtlebot3_burger_bridge.yaml)
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'spawn_turtlebot3.launch.py')),
            launch_arguments={'x_pose': LaunchConfiguration('x_pose'),
                              'y_pose': LaunchConfiguration('y_pose')}.items()))
    return actions


def generate_launch_description():
    return LaunchDescription([
        # sim:=false 이면 이미 떠 있는 시뮬레이션에 감지/회피 노드만 붙인다.
        DeclareLaunchArgument('sim', default_value='true',
                              description='true이면 Gazebo 시뮬레이션도 함께 실행'),
        DeclareLaunchArgument('world', default_value='turtlebot3_world',
                              description='맵 이름 또는 .world 파일 경로 '
                                          '(worlds/ 및 turtlebot3_gazebo/worlds 에서 탐색)'),
        DeclareLaunchArgument('spawn_robot', default_value='true',
                              description='false이면 로봇을 스폰하지 않음 '
                                          '(world 파일에 로봇이 이미 포함된 경우)'),
        DeclareLaunchArgument('x_pose', default_value='-2.0',
                              description='로봇 스폰 x 좌표'),
        DeclareLaunchArgument('y_pose', default_value='-0.5',
                              description='로봇 스폰 y 좌표'),
        # front_deg: 정면 기준 전체 폭(도). 30이면 좌우 15도
        DeclareLaunchArgument('front_deg', default_value='30.0',
                              description='전방 감지 구간 전체 폭(도)'),
        SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
        OpaqueFunction(function=_launch_simulation,
                       condition=IfCondition(LaunchConfiguration('sim'))),
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
