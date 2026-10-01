from cad.prototype_arm import build_snap01c as c

def test_opposed_covers_clear_protruding_hub_and_each_other():
    body,half=c.build()
    for travel in [0,2,5,10,20,38]:
        caps=c.pose_halves(half,travel)
        assert caps[0].intersect(caps[1]).val().Volume()<1e-6
        for cap in caps:
            assert cap.intersect(c.hub(13.5)).val().Volume()<1e-6
    for cap in c.pose_halves(half):
        assert cap.intersect(body).val().Volume()<1e-6

def test_caps_are_retained_axially_but_remain_separate_printable_solids():
    body,half=c.build()
    for s in [body,half]:
        assert s.val().isValid() and len(s.solids().vals())==1
    for cap in c.pose_halves(half):
        assert cap.translate((0,0,0.6)).intersect(body).val().Volume()>1
