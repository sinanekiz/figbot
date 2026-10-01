from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XACRO_NS = "http://www.ros.org/wiki/xacro"


def test_p0_rev_g_urdf_instantiates_two_flanking_arms_and_sloped_front_basket():
    tree = ET.parse(ROOT / "simulation" / "ros2" / "figbot_description" / "urdf" / "figbot_p0_rover.urdf.xacro")
    root = tree.getroot()
    arms = root.findall(f"{{{XACRO_NS}}}arm_proxy")
    assert {item.attrib["side"] for item in arms} == {"left", "right"}
    assert {item.attrib["y"] for item in arms} == {"0.250", "-0.250"}
    basket_joint = root.find("joint[@name='basket_joint']")
    assert basket_joint is not None
    assert basket_joint.find("origin").attrib["xyz"].startswith("0.100 ")
    floor_joint = root.find("joint[@name='basket_sloped_floor_joint']")
    assert floor_joint is not None
    assert "${basket_slope}" in floor_joint.find("origin").attrib["rpy"]
    slope = root.find(f"{{{XACRO_NS}}}property[@name='basket_slope']")
    assert slope is not None
    assert float(slope.attrib["value"]) < 0
