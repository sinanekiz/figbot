package com.figbot.scanner.vision;

import java.io.*;

/** Versioned camera-frame calibration. Never an authorization to move. */
public final class CalibrationRecord {
    private static final int MAGIC=0x46424331;
    private CalibrationRecord() {}
    public static String encode(MarkerCalibration.Result result,String profile) throws IOException {
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        try(DataOutputStream out=new DataOutputStream(bytes)){
            out.writeInt(MAGIC);out.writeUTF(profile);out.writeDouble(36);
            writePose(out,result.baseWorld());writePose(out,result.toolMarker());
            out.writeDouble(result.fitRmsMm());out.writeDouble(result.heldRmsMm());out.writeDouble(result.heldMaxMm());
        }
        StringBuilder hex=new StringBuilder();for(byte value:bytes.toByteArray())hex.append(String.format(java.util.Locale.ROOT,"%02x",value&255));
        return hex.toString();
    }
    public static MarkerCalibration.Result decode(String encoded,String profile) throws IOException {
        if(encoded.length()%2!=0||encoded.length()>8192)throw new IOException("Invalid record length");
        byte[] bytes=new byte[encoded.length()/2];
        for(int i=0;i<bytes.length;i++){
            int high=Character.digit(encoded.charAt(2*i),16),low=Character.digit(encoded.charAt(2*i+1),16);
            if(high<0||low<0)throw new IOException("Invalid record encoding");
            bytes[i]=(byte)((high<<4)|low);
        }
        try(DataInputStream in=new DataInputStream(new ByteArrayInputStream(bytes))){
            if(in.readInt()!=MAGIC||!in.readUTF().equals(profile)||in.readDouble()!=36)throw new IOException("Calibration setup changed");
            RigidPose baseCamera=readPose(in),toolMarker=readPose(in);
            double fit=in.readDouble(),held=in.readDouble(),max=in.readDouble();
            if(!Double.isFinite(fit)||!Double.isFinite(held)||!Double.isFinite(max)||fit<0||held<0||max<0||fit>6||held>8||max>12||in.available()!=0)
                throw new IOException("Invalid saved calibration");
            return new MarkerCalibration.Result(baseCamera,toolMarker,fit,held,max);
        }catch(IllegalArgumentException malformed){throw new IOException("Malformed calibration",malformed);}
    }
    private static void writePose(DataOutputStream out,RigidPose pose)throws IOException {
        for(double[] row:pose.rotation())for(double value:row)out.writeDouble(value);
        for(double value:pose.translation())out.writeDouble(value);
    }
    private static RigidPose readPose(DataInputStream in)throws IOException {
        double[][] rotation=new double[3][3];double[] translation=new double[3];
        for(int i=0;i<3;i++)for(int j=0;j<3;j++)rotation[i][j]=in.readDouble();
        for(int i=0;i<3;i++)translation[i]=in.readDouble();
        return new RigidPose(rotation,translation);
    }
}
