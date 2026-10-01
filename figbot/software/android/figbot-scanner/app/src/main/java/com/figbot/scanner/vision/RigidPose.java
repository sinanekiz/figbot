package com.figbot.scanner.vision;

/** Immutable right-handed SE(3), millimetres; a.compose(b) maps b's source to a's target. */
public final class RigidPose {
    private final double[][] r;
    private final double[] t;
    public RigidPose(double[][] rotation,double[] translation){
        if(rotation==null||rotation.length!=3||translation==null||translation.length!=3)throw new IllegalArgumentException("Pose dimensions");
        r=new double[3][3];t=translation.clone();
        for(int i=0;i<3;i++){
            if(rotation[i]==null||rotation[i].length!=3||!Double.isFinite(t[i]))throw new IllegalArgumentException("Invalid pose");
            for(int j=0;j<3;j++){r[i][j]=rotation[i][j];if(!Double.isFinite(r[i][j]))throw new IllegalArgumentException("Invalid rotation");}
        }
        for(int i=0;i<3;i++)for(int j=0;j<3;j++){
            double dot=0;for(int k=0;k<3;k++)dot+=r[i][k]*r[j][k];
            if(Math.abs(dot-(i==j?1:0))>1e-4)throw new IllegalArgumentException("Nonorthogonal rotation");
        }
        double det=r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])-r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])+r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]);
        if(det<.9999)throw new IllegalArgumentException("Reflected rotation");
    }
    public static RigidPose identity(){return new RigidPose(new double[][]{{1,0,0},{0,1,0},{0,0,1}},new double[3]);}
    public static RigidPose fromMatrix(double[][] m){
        double[][] r=new double[3][3];double[]t=new double[3];
        for(int i=0;i<3;i++){System.arraycopy(m[i],0,r[i],0,3);t[i]=m[i][3];}return new RigidPose(r,t);
    }
    public double[][] rotation(){double[][]v=new double[3][];for(int i=0;i<3;i++)v[i]=r[i].clone();return v;}
    public double[] translation(){return t.clone();}
    public double[] map(double[] p){double[]o=t.clone();for(int i=0;i<3;i++)for(int j=0;j<3;j++)o[i]+=r[i][j]*p[j];return o;}
    public RigidPose compose(RigidPose b){double[][]o=new double[3][3];for(int i=0;i<3;i++)for(int j=0;j<3;j++)for(int k=0;k<3;k++)o[i][j]+=r[i][k]*b.r[k][j];return new RigidPose(o,map(b.t));}
    public RigidPose inverse(){double[][]o=new double[3][3];double[]v=new double[3];for(int i=0;i<3;i++)for(int j=0;j<3;j++){o[i][j]=r[j][i];v[i]-=r[j][i]*t[j];}return new RigidPose(o,v);}
    public double distance(RigidPose b){double d=0;for(int i=0;i<3;i++)d+=Math.pow(t[i]-b.t[i],2);return Math.sqrt(d);}
    public double angle(RigidPose b){double trace=0;for(int i=0;i<3;i++)for(int j=0;j<3;j++)trace+=r[i][j]*b.r[i][j];return Math.acos(Math.max(-1,Math.min(1,(trace-1)/2)));}
}
