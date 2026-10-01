package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;

public class WorkSurfaceTest {
    @Test public void decimalPointAndTurkishCommaDescribeTheSameMeasuredHeight() {
        assertEquals(new WorkSurface(65),WorkSurface.fromCentimeters("6.5"));
        assertEquals(new WorkSurface(65),WorkSurface.fromCentimeters(" \t6,5\n"));
    }

    @Test public void raisedBasePlacesTableBelowTheUnchangedRobotOrigin() {
        WorkSurface surface = new WorkSurface(65);
        assertEquals(-65,surface.groundZMm(),0);
        assertEquals(-40,surface.gripZMm(25),0);
        assertEquals(-65,surface.gripZMm(0),0);
        assertEquals(65,surface.baseHeightMm(),0);
    }

    @Test public void zeroAndMaximumHeightAreAccepted() {
        assertEquals(25,new WorkSurface(0).gripZMm(25),0);
        assertEquals(new WorkSurface(0),WorkSurface.fromCentimeters("0"));
        assertEquals(new WorkSurface(1000),WorkSurface.fromCentimeters("100"));
        assertEquals(new WorkSurface(5),WorkSurface.fromCentimeters(",5"));
    }

    @Test public void invalidAndAmbiguousUiValuesAreRejected() {
        for (String value : new String[]{null,""," ","-6.5","NaN","Infinity","∞",
                "6,5.0","6.5,0","6,,5","6 5","6cm","1e2","100.1"})
            assertThrows(String.valueOf(value),IllegalArgumentException.class,
                    () -> WorkSurface.fromCentimeters(value));
    }

    @Test public void invalidMillimeterHeightsAreRejected() {
        for (double value : new double[]{-1,1000.01,Double.NaN,
                Double.NEGATIVE_INFINITY,Double.POSITIVE_INFINITY})
            assertThrows(IllegalArgumentException.class,() -> new WorkSurface(value));
    }

    @Test public void clearanceMustBeFiniteAndNonnegative() {
        WorkSurface surface = new WorkSurface(65);
        for (double value : new double[]{-1,Double.NaN,
                Double.NEGATIVE_INFINITY,Double.POSITIVE_INFINITY})
            assertThrows(IllegalArgumentException.class,() -> surface.gripZMm(value));
    }
}
