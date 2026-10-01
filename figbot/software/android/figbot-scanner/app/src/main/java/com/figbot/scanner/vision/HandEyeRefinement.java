package com.figbot.scanner.vision;

import java.util.List;

/** Joint SE(3) least-squares refinement of camera/base and marker/tool transforms.
 * Only training samples enter this solver. 100 mm/radian is a numerical residual
 * scale, not a measured arm dimension. Independent acceptance limits are unchanged.
 */
public final class HandEyeRefinement {
    private static final double ANGLE_SCALE_MM = 100;
    public record Fit(RigidPose baseCamera, RigidPose toolMarker) {}
    private HandEyeRefinement() {}
    public static Fit refine(List<MarkerCalibration.Sample> train, RigidPose camera, RigidPose marker) {
        return refine(train,camera,marker,false);
    }
    public static Fit refineCamera(List<MarkerCalibration.Sample> train,RigidPose camera,RigidPose marker){
        return refine(train,camera,marker,true);
    }
    private static Fit refine(List<MarkerCalibration.Sample> train,RigidPose camera,RigidPose marker,boolean fixedMarker) {
        int parameters=fixedMarker?6:12;
        Fit best=new Fit(camera,marker);
        double[] r=residual(train,best);double cost=cost(r),lambda=.001;
        for(int iteration=0;iteration<50;iteration++) {
            double[][] j=new double[r.length][parameters];
            for(int col=0;col<parameters;col++) {
                double eps=col%6<3?1e-5:.01;
                double[] step=new double[12];step[col]=eps;
                double[] shifted=residual(train,update(best,step));
                for(int row=0;row<r.length;row++)j[row][col]=(shifted[row]-r[row])/eps;
            }
            double[][] a=new double[parameters][parameters];double[] b=new double[parameters];
            for(int row=0;row<r.length;row++)for(int i=0;i<parameters;i++) {
                b[i]-=j[row][i]*r[row];
                for(int k=0;k<parameters;k++)a[i][k]+=j[row][i]*j[row][k];
            }
            for(int i=0;i<parameters;i++)a[i][i]+=lambda*Math.max(1,a[i][i]);
            double[] solved=solve(a,b);if(solved==null)break;
            double[] step=java.util.Arrays.copyOf(solved,12);
            Fit next=update(best,step);double[] nextR=residual(train,next);double nextCost=cost(nextR);
            if(Double.isFinite(nextCost)&&nextCost<cost) {
                double improvement=cost-nextCost;best=next;r=nextR;cost=nextCost;lambda=Math.max(1e-9,lambda/3);
                if(improvement<1e-8)break;
            } else {lambda*=10;if(lambda>1e9)break;}
        }
        return best;
    }
    private static Fit update(Fit f,double[] s){return new Fit(update(f.baseCamera,s,0),update(f.toolMarker,s,6));}
    private static RigidPose update(RigidPose p,double[] s,int offset) {
        double x=s[offset],y=s[offset+1],z=s[offset+2],theta=Math.sqrt(x*x+y*y+z*z);
        double a=theta<1e-8?1:Math.sin(theta)/theta;
        double b=theta<1e-8?.5:(1-Math.cos(theta))/(theta*theta);
        double[][] k={{0,-z,y},{z,0,-x},{-y,x,0}},rotation=new double[3][3];
        for(int i=0;i<3;i++)for(int j=0;j<3;j++) {
            rotation[i][j]=(i==j?1:0)+a*k[i][j];
            for(int n=0;n<3;n++)rotation[i][j]+=b*k[i][n]*k[n][j];
        }
        double[] t=p.translation();for(int i=0;i<3;i++)t[i]+=s[offset+3+i];
        return new RigidPose(new RigidPose(rotation,new double[3]).compose(new RigidPose(p.rotation(),new double[3])).rotation(),t);
    }
    private static double[] residual(List<MarkerCalibration.Sample> samples,Fit f) {
        double[] r=new double[samples.size()*6];int n=0;
        for(var sample:samples) {
            RigidPose predicted=f.baseCamera.compose(sample.worldMarker()).compose(f.toolMarker.inverse());
            double[] p=predicted.translation(),q=sample.baseTool().translation();
            for(int i=0;i<3;i++)r[n++]=p[i]-q[i];
            RigidPose delta=sample.baseTool().inverse().compose(predicted);double[][] m=delta.rotation();
            double angle=delta.angle(RigidPose.identity());
            double scale=angle<1e-8?.5:angle/(2*Math.sin(angle));
            r[n++]=ANGLE_SCALE_MM*scale*(m[2][1]-m[1][2]);
            r[n++]=ANGLE_SCALE_MM*scale*(m[0][2]-m[2][0]);
            r[n++]=ANGLE_SCALE_MM*scale*(m[1][0]-m[0][1]);
        }
        return r;
    }
    private static double cost(double[] r){double c=0;for(double v:r)c+=v*v;return c;}
    private static double[] solve(double[][] a,double[] b) {
        for(int i=0;i<b.length;i++) {
            int pivot=i;for(int k=i+1;k<b.length;k++)if(Math.abs(a[k][i])>Math.abs(a[pivot][i]))pivot=k;
            if(Math.abs(a[pivot][i])<1e-12)return null;
            double[] row=a[i];a[i]=a[pivot];a[pivot]=row;double v=b[i];b[i]=b[pivot];b[pivot]=v;
            for(int k=i+1;k<b.length;k++) {
                double scale=a[k][i]/a[i][i];
                for(int j=i;j<b.length;j++)a[k][j]-=scale*a[i][j];b[k]-=scale*b[i];
            }
        }
        double[] x=new double[b.length];
        for(int i=b.length-1;i>=0;i--){double v=b[i];for(int j=i+1;j<b.length;j++)v-=a[i][j]*x[j];x[i]=v/a[i][i];}
        return x;
    }
}
