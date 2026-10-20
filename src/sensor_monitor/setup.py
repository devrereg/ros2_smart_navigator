from setuptools import find_packages, setup

package_name = 'sensor_monitor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='taeho-kim',
    maintainer_email='your_email@example.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'LaserScan_sub = sensor_monitor.LaserScan_sub:main',
            'benchmark_pub = sensor_monitor.benchmark_pub:main',
            'benchmark_sub = sensor_monitor.benchmark_sub:main',
        ],
    },
)
