package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;
import static com.figbot.scanner.so101.HoldControl.Action.*;
import static com.figbot.scanner.so101.RobotController.State.*;

public class HoldControlTest {
    @Test public void measuredTorqueOverridesUnadoptedState() {
        assertEquals(RELEASE, HoldControl.action(DISARMED, 6, 6));
        assertEquals(RELEASE, HoldControl.action(DISARMED, 6, 2));
        assertEquals(HOLD, HoldControl.action(DISARMED, 6, 0));
    }
    @Test public void motionAndMissingFeedbackCannotOfferToggle() {
        assertEquals(WAIT, HoldControl.action(MOVING, 6, 6));
        assertEquals(WAIT, HoldControl.action(STOPPING, 6, 6));
        assertEquals(UNKNOWN, HoldControl.action(DISARMED, 5, 0));
        assertEquals(UNKNOWN, HoldControl.action(FAULT_UNKNOWN, 6, 0));
    }
    @Test public void poweredFaultOffersSupportedReleaseNotReenable() {
        assertEquals(RELEASE, HoldControl.action(FAULT_HOLD, 6, 6));
        assertEquals(RELEASE, HoldControl.action(FAULT_UNKNOWN, 6, 1));
    }
}
