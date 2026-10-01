package com.figbot.scanner.vision;

/** Pinhole prediction in unrotated CPU-image coordinates. Not an occlusion detector. */
public record MarkerVisibility(double fx,double fy,double cx,double cy,int width,int height) {
    public boolean contains(RigidPose cameraMarker) {
        return contains(cameraMarker,32);
    }
    /** Only after a fresh unambiguous detection; never below detector's 28 px gate. */
    public static double supportedEdge(float[] corners){
        double edge=Double.POSITIVE_INFINITY;
        if(corners==null||corners.length!=8)return 32;
        for(int i=0;i<4;i++){int j=(i+1)%4;edge=Math.min(edge,Math.hypot(corners[2*i]-corners[2*j],corners[2*i+1]-corners[2*j+1]));}
        return Double.isFinite(edge)?Math.max(28,Math.min(32,edge*.8)):32;
    }
    public boolean contains(RigidPose cameraMarker,double minimumEdge) {
        if(!Double.isFinite(minimumEdge)||minimumEdge<28)return false;
        double[][] corners=new double[4][2];float[] pixels=new float[8];int i=0;
        for(double[] corner:new double[][]{{-18,18,0},{18,18,0},{18,-18,0},{-18,-18,0}}){
            double[] p=cameraMarker.map(corner);
            if(p[2]<=0)return false;
            double x=fx*p[0]/p[2]+cx,y=fy*p[1]/p[2]+cy;
            // Reserve room for model residual and the printed white border.
            if(!Double.isFinite(x)||!Double.isFinite(y)||x<24||y<24||x>width-24||y>height-24)return false;
            pixels[2*i]=(float)x;pixels[2*i+1]=(float)y;corners[i++]=new double[]{x,y};
        }
        for(i=0;i<4;i++)if(Math.hypot(corners[i][0]-corners[(i+1)%4][0],corners[i][1]-corners[(i+1)%4][1])<minimumEdge)return false;
        return MarkerViewQuality.incidence(cameraMarker)<80
                &&MarkerViewQuality.thickness(pixels)>=MarkerViewQuality.MIN_THICKNESS_PX;
    }
    /** Scan admission also needs measurement precision, not just an image footprint. */
    public boolean measurable(RigidPose pose,double minimumEdge){
        if(!contains(pose,minimumEdge))return false;
        float[] pixels=new float[8];int i=0;
        for(double[] corner:new double[][]{{-18,18,0},{18,18,0},{18,-18,0},{-18,-18,0}}){
            double[] p=pose.map(corner);pixels[i++]=(float)(fx*p[0]/p[2]+cx);pixels[i++]=(float)(fy*p[1]/p[2]+cy);
        }
        return MarkerViewQuality.evaluate(pose,pixels,fx,fy,0).usable();
    }
}
