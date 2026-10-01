package com.figbot.scanner.so101;

import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;

/** Persisted raw jaw endpoints tied to an explicit encoder profile.
 * These are motor commands, not measured aperture, grip force, or proof of contact.
 * Creating, decoding or applying settings never moves a motor or grants calibration.
 */
public final class GripperSettings {
    public static final int LEGACY_COMMAND_CLOSED = 870;
    public static final int RECORDED_2026_09_20_CLOSED = 780;
    public static final int RECORDED_2026_09_20_OPEN = 1153;
    private static final String SCHEMA = "1";
    private static final Set<String> KEYS = new HashSet<>(Arrays.asList(
            "schema", "profile", "closed", "open", "provenance"));
    private final int closed, open;
    private final String provenance, profileIdentity;

    private GripperSettings(int closed, int open, String provenance, String profileIdentity) {
        this.closed = closed;
        this.open = open;
        this.provenance = provenance;
        this.profileIdentity = profileIdentity;
    }

    /** Preserve the legacy app's effective 870 command only for its exact old
     * endpoint/offset combination. Other profiles keep their explicit endpoints. */
    public static GripperSettings compatibility(ArmProfile profile) {
        requireProfile(profile);
        boolean legacy = profile.gripperClosed() == 894 && profile.gripperOpen() == 1153
                && profile.offsets()[5] == 85;
        return from(profile, legacy ? LEGACY_COMMAND_CLOSED : profile.gripperClosed(),
                profile.gripperOpen(), legacy ? "LEGACY_APP_EFFECTIVE_COMMAND_870"
                        : "EXISTING_PROFILE_ENDPOINTS");
    }

    /** Explicitly selected recorded preset; never selected automatically on load. */
    public static GripperSettings historical(ArmProfile profile) {
        requireProfile(profile);
        if (profile.offsets()[5] != 85)
            throw new IllegalArgumentException("20 Eylül kıskaç kaydı bu motor ofsetiyle uyumlu değil.");
        return from(profile, RECORDED_2026_09_20_CLOSED, RECORDED_2026_09_20_OPEN,
                "RECORDED_2026_09_20_RAW_PRESET; APERTURE_AND_FORCE_UNVERIFIED");
    }

    public static GripperSettings from(ArmProfile profile, int closed, int open, String provenance) {
        requireProfile(profile);
        requireEndpoints(profile, closed, open);
        requireProvenance(provenance);
        return new GripperSettings(closed, open, provenance, identity(profile));
    }

    public int closed() { return closed; }
    public int open() { return open; }
    public String provenance() { return provenance; }

    /** Retains home/basket, passive mode and the existing calibration status. */
    public ArmProfile apply(ArmProfile profile) {
        requireProfile(profile);
        if (!profileIdentity.equals(identity(profile)))
            throw new IllegalArgumentException("Kayıtlı kıskaç ayarı mevcut enkoder profiliyle eşleşmiyor.");
        requireEndpoints(profile, closed, open);
        return profile.withSavedPoses(profile.home(), profile.basket(), closed, open);
    }

    public String encode() {
        Properties properties = new Properties();
        properties.setProperty("schema", SCHEMA);
        properties.setProperty("profile", profileIdentity);
        properties.setProperty("closed", Integer.toString(closed));
        properties.setProperty("open", Integer.toString(open));
        properties.setProperty("provenance", provenance);
        StringWriter writer = new StringWriter();
        try {
            properties.store(writer, "FIGBOT raw gripper endpoints; no force/aperture calibration");
        } catch (IOException impossible) {
            throw new IllegalStateException("Kıskaç ayarı kodlanamadı.", impossible);
        }
        return writer.toString();
    }

    /** Invalid or foreign records fail closed. The caller must not silently
     * replace a rejected record with a default or a historical tighter setting. */
    public static GripperSettings decode(ArmProfile profile, String text) {
        requireProfile(profile);
        if (text == null || text.isEmpty() || text.length() > 8192)
            throw new IllegalArgumentException("Kıskaç ayarı kaydı boş veya geçersiz uzunlukta.");
        Properties properties = new Properties() {
            @Override public synchronized Object put(Object key, Object value) {
                if (containsKey(key))
                    throw new IllegalArgumentException("Kıskaç ayarı kaydında yinelenen alan var.");
                return super.put(key, value);
            }
        };
        try {
            properties.load(new StringReader(text));
        } catch (IOException | IllegalArgumentException invalid) {
            throw new IllegalArgumentException("Kıskaç ayarı kaydı okunamadı.", invalid);
        }
        if (!properties.stringPropertyNames().equals(KEYS)
                || !SCHEMA.equals(properties.getProperty("schema")))
            throw new IllegalArgumentException("Kıskaç ayarı kayıt biçimi desteklenmiyor veya eksik.");
        if (!identity(profile).equals(properties.getProperty("profile")))
            throw new IllegalArgumentException("Kayıtlı kıskaç ayarı mevcut enkoder profiliyle eşleşmiyor.");
        return from(profile, parseRaw(properties.getProperty("closed")),
                parseRaw(properties.getProperty("open")), properties.getProperty("provenance"));
    }

    private static int parseRaw(String value) {
        if (value == null || !value.matches("0|[1-9][0-9]{0,3}"))
            throw new IllegalArgumentException("Kıskaç uç konumu geçerli bir ham enkoder değeri değil.");
        int raw = Integer.parseInt(value);
        if (raw > 4095)
            throw new IllegalArgumentException("Kıskaç uç konumu 0–4095 dışında.");
        return raw;
    }

    private static void requireEndpoints(ArmProfile profile, int closed, int open) {
        int[] bounds = profile.envelopes()[5];
        if (closed < bounds[0] || open > bounds[1] || closed >= open)
            throw new IllegalArgumentException("Kıskaç kapanma/açılma konumları mevcut hareket sınırları içinde ve artan sırada olmalı.");
    }

    private static void requireProvenance(String provenance) {
        if (provenance == null || provenance.trim().isEmpty() || provenance.length() > 256)
            throw new IllegalArgumentException("Kıskaç ayarının kaynağı gerekli (1–256 karakter).");
        for (int i=0;i<provenance.length();i++) if (Character.isISOControl(provenance.charAt(i)))
            throw new IllegalArgumentException("Kıskaç ayarının kaynağı kontrol karakteri içeremez.");
    }

    private static void requireProfile(ArmProfile profile) {
        if (profile == null) throw new IllegalArgumentException("Kol profili gerekli.");
    }

    /** Task poses, old jaw endpoints and validation status are not encoder identity.
     * Exact radians are included as hex doubles to avoid locale/rounding changes. */
    private static String identity(ArmProfile profile) {
        StringBuilder canonical = new StringBuilder("figbot-gripper-profile-v1|")
                .append(ArmProfile.VENDOR_URDF_SHA256).append('|').append(ArmProfile.FRAME)
                .append('|').append(Arrays.toString(profile.offsets()))
                .append('|').append(Arrays.toString(profile.referenceRaw()));
        for (double radians : profile.referenceRadians()) canonical.append('|').append(Double.toHexString(radians));
        canonical.append('|').append(Arrays.toString(profile.directionSigns()))
                .append('|').append(Arrays.deepToString(profile.envelopes()))
                .append('|').append(profile.passiveWristRoll());
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(canonical.toString().getBytes(StandardCharsets.UTF_8));
            char[] digits = "0123456789abcdef".toCharArray();
            StringBuilder hex = new StringBuilder(64);
            for (byte value : digest) hex.append(digits[(value & 255) >>> 4]).append(digits[value & 15]);
            return hex.toString();
        } catch (NoSuchAlgorithmException unavailable) {
            throw new IllegalStateException("SHA-256 gerekli.", unavailable);
        }
    }
}
