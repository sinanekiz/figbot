from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    description = FindPackageShare("figbot_description")
    model = PathJoinSubstitution([description, "urdf", "figbot_v0.urdf.xacro"])
    robot_description = {"robot_description": Command([FindExecutable(name="xacro"), " ", model])}
    return LaunchDescription(
        [
            Node(package="robot_state_publisher", executable="robot_state_publisher", parameters=[robot_description]),
            Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui"),
            Node(package="rviz2", executable="rviz2", output="screen"),
        ]
    )

