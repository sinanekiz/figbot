import numpy as np
import pytest
from simulation.aero_v3_front_mount_study import joint_state
from cad.prototype_arm import build_aero_v3 as arm


def test_translation_invariance_without_rewriting_design():
    original=joint_state((650,415,102),(380,415,280))
    translated=joint_state((790,415,102),(520,415,280))
    assert np.allclose(original,translated)
    assert arm.BASE==(380.,415.,280.)


def test_existing_basket_requires_excess_yaw_after_front_mount():
    q=joint_state((400,275,460),(520,415,280))
    assert q[0]==pytest.approx(-130.6012946)
    candidate=joint_state((540,275,460),(520,415,280))
    assert candidate[0]==pytest.approx(-81.8698976)


def test_lower_same_arm_exceeds_existing_wrist_limit():
    high=joint_state((650,415,102),(520,415,280))
    low=joint_state((650,415,102),(520,415,160))
    assert high[3]>-135 and low[3]<-135
