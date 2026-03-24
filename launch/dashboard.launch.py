#!/usr/bin/env python3
"""
Launch file for CHARS Dashboard.

Launches:
1. rosbridge_websocket (port 9090) for ROS-Web communication
2. Python HTTP server (port 8080) serving the dashboard

Usage:
    ros2 launch chars_dashboard dashboard.launch.py
    Then open http://localhost:8080/dashboard.html
"""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory('chars_dashboard')
    web_dir = os.path.join(pkg_dir, 'web')

    # 1. rosbridge_websocket
    rosbridge_launch = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rosbridge_server'),
                'launch',
                'rosbridge_websocket_launch.xml'
            )
        ),
    )

    # 2. Simple HTTP server to serve the web dashboard
    http_server = ExecuteProcess(
        cmd=['python3', '-m', 'http.server', '8080', '--directory', web_dir],
        output='screen',
        name='dashboard_http_server',
    )

    return LaunchDescription([
        rosbridge_launch,
        http_server,
    ])
