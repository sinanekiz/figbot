package com.figbot.scanner.vision;

/** Local pinhole sensitivity, not a certified physical error bound. No robot/FK prior.
 * Rotation is perturbed about the marker centre in camera coordinates, so the
 * result is independent of Rodrigues parameterization and image roll. */
public record MarkerViewQuality(double incidenceDegrees, double thicknessPx,
                                double positionSensitivityMm, double rotationSensitivityDegrees) {
    public static final double MIN_THICKNESS_PX=20;
    public boolean usable() {
        return Double.isFinite(incidenceDegrees) && incidenceDegrees<80
                && thicknessPx>=MIN_THICKNESS_PX && Double.isFinite(thicknessPx)
                && positionSensitivityMm<=3 && Double.isFinite(positionSensitivityMm)
                && rotationSensitivityDegrees<=3 && Double.isFinite(rotationSensitivityDegrees);
    }
    public static MarkerViewQuality evaluate(RigidPose pose,float[] corners,double fx,double fy,double reprojectionPx) {
        double angle=incidence(pose),thickness=thickness(corners);
        if(!(fx>0)||!(fy>0)||!Double.isFinite(fx)||!Double.isFinite(fy)
                ||!Double.isFinite(reprojectionPx)||reprojectionPx<0||thickness<=0)
            return invalid(angle,thickness);
        double[][] normal=new double[6][6];double[][] r=pose.rotation();double[] t=pose.translation();
        for(double[] p:new double[][]{{-18,18,0},{18,18,0},{18,-18,0},{-18,-18,0}}) {
            double[] q=new double[3];for(int i=0;i<3;i++)for(int j=0;j<3;j++)q[i]+=r[i][j]*p[j];
            double x=q[0]+t[0],y=q[1]+t[1],z=q[2]+t[2];
            if(!(z>0))return invalid(angle,thickness);
            double[][] projection={{fx/z,0,-fx*x/(z*z)},{0,fy/z,-fy*y/(z*z)}};
            double[][] rotation={{0,q[2],-q[1]},{-q[2],0,q[0]},{q[1],-q[0],0}};
            for(double[] row:projection) {
                double[] j=new double[6];System.arraycopy(row,0,j,0,3);
                for(int a=0;a<3;a++)for(int b=0;b<3;b++)j[3+a]+=row[b]*rotation[b][a];
                for(int a=0;a<6;a++)for(int b=0;b<6;b++)normal[a][b]+=j[a]*j[b];
            }
        }
        double[][] covariance=inverse(normal);
        if(covariance==null)return invalid(angle,thickness);
        // A zero residual with only four corners is not zero measurement noise.
        // 0.35 px is an explicit engineering floor, not a learned camera model.
        double sigma=Math.max(.35,reprojectionPx);
        double position=0,rotation=0;
        for(int i=0;i<3;i++){position+=covariance[i][i];rotation+=covariance[i+3][i+3];}
        if(position<0||rotation<0)return invalid(angle,thickness);
        return new MarkerViewQuality(angle,thickness,sigma*Math.sqrt(position),Math.toDegrees(sigma*Math.sqrt(rotation)));
    }
    public static double incidence(RigidPose pose) {
        double[][] r=pose.rotation();double[] t=pose.translation();double norm=Math.sqrt(t[0]*t[0]+t[1]*t[1]+t[2]*t[2]);
        if(!(norm>0))return Double.NaN;
        return Math.toDegrees(Math.acos(Math.max(-1,Math.min(1,-(r[0][2]*t[0]+r[1][2]*t[1]+r[2][2]*t[2])/norm))));
    }
    /** Minimum polygon width normal to any edge, unlike edge length this
     * detects a thin diamond after an in-image rotation. */
    public static double thickness(float[] p) {
        if(p==null||p.length!=8)return 0;
        for(float v:p)if(!Float.isFinite(v))return 0;
        double minimum=Double.POSITIVE_INFINITY;
        for(int i=0;i<4;i++) {
            int k=(i+1)%4;double dx=p[2*k]-p[2*i],dy=p[2*k+1]-p[2*i+1],length=Math.hypot(dx,dy);
            if(length<1e-6)return 0;
            double lo=Double.POSITIVE_INFINITY,hi=Double.NEGATIVE_INFINITY;
            for(int j=0;j<4;j++){double d=(-dy*p[2*j]+dx*p[2*j+1])/length;lo=Math.min(lo,d);hi=Math.max(hi,d);}
            minimum=Math.min(minimum,hi-lo);
        }
        return minimum;
    }
    private static MarkerViewQuality invalid(double angle,double thickness) {
        return new MarkerViewQuality(angle,thickness,Double.POSITIVE_INFINITY,Double.POSITIVE_INFINITY);
    }
    private static double[][] inverse(double[][] matrix) {
        double[][] a=new double[6][12];
        for(int i=0;i<6;i++){System.arraycopy(matrix[i],0,a[i],0,6);a[i][6+i]=1;}
        for(int c=0;c<6;c++) {
            int pivot=c;for(int i=c+1;i<6;i++)if(Math.abs(a[i][c])>Math.abs(a[pivot][c]))pivot=i;
            if(!Double.isFinite(a[pivot][c])||Math.abs(a[pivot][c])<1e-10)return null;
            double[] swap=a[c];a[c]=a[pivot];a[pivot]=swap;double scale=a[c][c];
            for(int j=0;j<12;j++)a[c][j]/=scale;
            for(int i=0;i<6;i++)if(i!=c){double factor=a[i][c];for(int j=0;j<12;j++)a[i][j]-=factor*a[c][j];}
        }
        double[][] result=new double[6][6];for(int i=0;i<6;i++)System.arraycopy(a[i],6,result[i],0,6);
        return result;
    }
}
