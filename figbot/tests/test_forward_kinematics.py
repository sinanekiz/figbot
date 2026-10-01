from math import isclose, pi, radians
from pathlib import Path
from xml.etree import ElementTree

from software.kinematics import ArmKinematics, JointState, load_arm_geometry


def test_zero_pose_reaches_nominal_horizontal_length():
    arm = ArmKinematics()
    pose = arm.forward(JointState(0.0, 0.0, 0.0, 0.0))
    assert isclose(pose.x, arm.geometry.maximum_reach, abs_tol=1e-12)
    assert isclose(pose.y, 0.0, abs_tol=1e-12)
    assert isclose(pose.z, arm.geometry.base_height, abs_tol=1e-12)
    assert isclose(pose.tool_pitch, 0.0, abs_tol=1e-12)


def test_base_yaw_rotates_radial_chain_into_y_axis():
    arm = ArmKinematics()
    pose = arm.forward(JointState(pi / 2, 0.0, 0.0, 0.0))
    assert isclose(pose.x, 0.0, abs_tol=1e-12)
    assert isclose(pose.y, arm.geometry.maximum_reach, abs_tol=1e-12)


def test_link_points_end_at_forward_pose():
    arm = ArmKinematics()
    joints = JointState(0.35, 0.42, -0.8, 0.2)
    pose = arm.forward(joints)
    tip = arm.link_points(joints)[-1]
    assert all(isclose(value, expected, abs_tol=1e-12) for value, expected in zip(tip, (pose.x, pose.y, pose.z)))


def test_geometry_is_bound_to_central_cad_parameters_when_available():
    from cad.config import parameters

    geometry = load_arm_geometry()
    assert geometry.source == "cad.config.parameters"
    assert isclose(geometry.upper_arm, parameters.ARM_UPPER_LENGTH / 1000.0)
    assert isclose(geometry.forearm, parameters.ARM_FORE_LENGTH / 1000.0)
    assert isclose(geometry.tool, parameters.ARM_TOOL_LENGTH / 1000.0)
    assert isclose(geometry.base_height, parameters.ARM_BASE_HEIGHT / 1000.0)


def test_joint_limits_speed_and_acceleration_are_bound_to_cad_parameters():
    from cad.config import parameters

    geometry = load_arm_geometry()
    for name, limit in zip(("J1", "J2", "J3", "J4"), geometry.joint_limits):
        expected_lower, expected_upper = parameters.JOINT_LIMITS_DEG[name]
        assert isclose(limit.lower, radians(expected_lower))
        assert isclose(limit.upper, radians(expected_upper))
        assert isclose(limit.max_velocity, radians(parameters.JOINT_MAX_SPEED_DEG_S[name]))
        assert isclose(limit.max_acceleration, radians(parameters.JOINT_MAX_ACCEL_DEG_S2[name]))


def test_xacro_geometry_and_joint_limits_match_kinematics_contract():
    path = Path(__file__).resolve().parents[1] / "simulation" / "ros2" / "figbot_description" / "urdf" / "figbot_v0.urdf.xacro"
    root = ElementTree.parse(path).getroot()
    xacro_namespace = "{http://www.ros.org/wiki/xacro}"
    properties = {node.attrib["name"]: float(node.attrib["value"]) for node in root.findall(f"{xacro_namespace}property")}
    geometry = load_arm_geometry()
    assert isclose(properties["upper"], geometry.upper_arm)
    assert isclose(properties["fore"], geometry.forearm)
    assert isclose(properties["tool"], geometry.tool)
    assert isclose(properties["base_height"], geometry.base_height)
    joints = {node.attrib["name"]: node for node in root.findall("joint") if node.attrib.get("name") in {"J1", "J2", "J3", "J4"}}
    for name, expected in zip(("J1", "J2", "J3", "J4"), geometry.joint_limits):
        limit = joints[name].find("limit")
        assert limit is not None
        assert isclose(float(limit.attrib["lower"]), expected.lower, abs_tol=1e-6)
        assert isclose(float(limit.attrib["upper"]), expected.upper, abs_tol=1e-6)
        assert isclose(float(limit.attrib["velocity"]), expected.max_velocity, abs_tol=1e-6)
