package com.figbot.scanner.so101;

import org.junit.Test;
import static org.junit.Assert.*;

public class GripperSettingsTest {
    private final ArmProfile profile=ArmProfile.unverifiedDefaults().withPassiveWristRoll();

    @Test public void legacyMigrationPreservesEffective870WithoutRepeatedSubtraction() {
        var settings=GripperSettings.compatibility(profile);
        assertEquals(870,settings.closed());assertEquals(1153,settings.open());
        ArmProfile applied=settings.apply(profile);
        assertEquals(870,applied.gripperClosed());
        assertEquals(870,GripperSettings.compatibility(applied).closed());
        assertEquals(894,profile.gripperClosed());
    }

    @Test public void otherProfilesKeepTheirExplicitEndpoints() {
        ArmProfile other=profile.withSavedPoses(profile.home(),profile.basket(),900,1180);
        assertEquals(900,GripperSettings.compatibility(other).closed());
        assertEquals(1180,GripperSettings.compatibility(other).open());
        int[] offsets=profile.offsets();offsets[5]=86;
        ArmProfile newOffset=copy(offsets,profile.referenceRaw(),profile.referenceRadians(),
                profile.directionSigns(),profile.envelopes());
        assertEquals(894,GripperSettings.compatibility(newOffset).closed());
    }

    @Test public void historicalPresetIsExplicitAndChecksOffsetAndBounds() {
        var recorded=GripperSettings.historical(profile);
        assertEquals(780,recorded.closed());assertEquals(1153,recorded.open());
        assertTrue(recorded.provenance().contains("APERTURE_AND_FORCE_UNVERIFIED"));
        assertEquals(894,profile.gripperClosed());
        int[] offsets=profile.offsets();offsets[5]=86;
        ArmProfile shifted=copy(offsets,profile.referenceRaw(),profile.referenceRadians(),
                profile.directionSigns(),profile.envelopes());
        assertThrows(IllegalArgumentException.class,()->GripperSettings.historical(shifted));
        int[][] bounds=profile.envelopes();bounds[5][0]=790;
        ArmProfile narrowed=copy(profile.offsets(),profile.referenceRaw(),profile.referenceRadians(),
                profile.directionSigns(),bounds);
        assertThrows(IllegalArgumentException.class,()->GripperSettings.historical(narrowed));
    }

    @Test public void roundTripPreservesUnicodeProvenanceAndExactEndpoints() {
        var source=GripperSettings.from(profile,805,1175,"Elle ölçüldü: eşitlik=değer; aç/kapa");
        var restored=GripperSettings.decode(profile,source.encode());
        assertEquals(805,restored.closed());assertEquals(1175,restored.open());
        assertEquals(source.provenance(),restored.provenance());
        assertEquals(805,restored.apply(profile).gripperClosed());
    }

    @Test public void applyPreservesTaskPosesAndExistingCalibrationEvidence() {
        var setting=GripperSettings.from(profile,800,1175,"Explicit bench setting");
        int[] home=profile.home();home[0]+=5;
        int[] basket=profile.basket();basket[0]-=5;
        var changed=profile.withSavedPoses(home,basket,850,1153)
                .withRecordedSessionValidation("existing physical evidence");
        ArmProfile applied=setting.apply(changed);
        assertArrayEquals(home,applied.home());assertArrayEquals(basket,applied.basket());
        assertEquals(changed.calibrationStatus(),applied.calibrationStatus());
        assertTrue(applied.physicalCalibrationVerified());assertTrue(applied.passiveWristRoll());
        assertFalse(setting.apply(profile).physicalCalibrationVerified());
    }

    @Test public void eachEncoderIdentityComponentIsBound() {
        var setting=GripperSettings.from(profile,800,1153,"test");
        int[] offsets=profile.offsets();offsets[0]-=1;
        rejectForeign(setting,copy(offsets,profile.referenceRaw(),profile.referenceRadians(),profile.directionSigns(),profile.envelopes()).withPassiveWristRoll());
        int[] reference=profile.referenceRaw();reference[0]+=1;
        rejectForeign(setting,copy(profile.offsets(),reference,profile.referenceRadians(),profile.directionSigns(),profile.envelopes()).withPassiveWristRoll());
        double[] radians=profile.referenceRadians();radians[0]+=.001;
        rejectForeign(setting,copy(profile.offsets(),profile.referenceRaw(),radians,profile.directionSigns(),profile.envelopes()).withPassiveWristRoll());
        int[] signs=profile.directionSigns();signs[0]=-1;
        rejectForeign(setting,copy(profile.offsets(),profile.referenceRaw(),profile.referenceRadians(),signs,profile.envelopes()).withPassiveWristRoll());
        int[][] bounds=profile.envelopes();bounds[0][0]+=1;
        rejectForeign(setting,copy(profile.offsets(),profile.referenceRaw(),profile.referenceRadians(),profile.directionSigns(),bounds).withPassiveWristRoll());
        // Identical arrays and bounds, but passive mode changed.
        rejectForeign(setting,copy(profile.offsets(),profile.referenceRaw(),profile.referenceRadians(),profile.directionSigns(),profile.envelopes()));
    }

    @Test public void malformedSchemaAndDuplicatePropertiesAreRejectedWithoutFallback() {
        String valid=GripperSettings.compatibility(profile).encode();
        for(String invalid:new String[]{"",valid.replace("schema=1","schema=2"),
                valid.replace("closed=870", ""),valid+"\nclosed=780\n",valid+"\nunknown=1\n",
                valid.replace("closed=870","closed=870.0"),valid.replace("closed=870","closed=+870"),
                valid.replace("closed=870","closed=0870"),valid.replace("closed=870","closed=9999"),
                valid.replace("closed=870","closed=768"),valid.replace("closed=870","closed=1200"),
                valid+"\ninvalid=\\uBADZ\n"})
            assertThrows(IllegalArgumentException.class,()->GripperSettings.decode(profile,invalid));
        assertThrows(IllegalArgumentException.class,()->GripperSettings.decode(profile,null));
        assertThrows(IllegalArgumentException.class,()->GripperSettings.decode(profile,"x".repeat(8193)));
    }

    @Test public void invalidEndpointsOrProvenanceCannotBeCreated() {
        for(int[] invalid:new int[][]{{768,1153},{800,1202},{900,900},{1000,900},
                {Integer.MIN_VALUE,1153},{800,Integer.MAX_VALUE}})
            assertThrows(IllegalArgumentException.class,()->GripperSettings.from(profile,invalid[0],invalid[1],"test"));
        for(String invalid:new String[]{null,"", "   ","line\nbreak","x".repeat(257)})
            assertThrows(IllegalArgumentException.class,()->GripperSettings.from(profile,800,1153,invalid));
        assertThrows(IllegalArgumentException.class,()->GripperSettings.compatibility(null));
        assertThrows(IllegalArgumentException.class,()->GripperSettings.historical(null));
        assertThrows(IllegalArgumentException.class,()->GripperSettings.decode(null,"anything"));
    }

    private void rejectForeign(GripperSettings setting,ArmProfile foreign) {
        assertThrows(IllegalArgumentException.class,()->setting.apply(foreign));
        assertThrows(IllegalArgumentException.class,()->GripperSettings.decode(foreign,setting.encode()));
    }

    private ArmProfile copy(int[] offsets,int[] refs,double[] radians,int[] signs,int[][] bounds) {
        return new ArmProfile(offsets,refs,radians,signs,bounds,profile.home(),profile.basket(),
                profile.gripperClosed(),profile.gripperOpen(),profile.physicalCalibrationVerified(),profile.calibrationStatus());
    }
}
