package com.figbot.scanner.vision;

/** Pinhole ray to a measured horizontal plane; all distances in mm.
 * The pixel must describe the object's ground contact, not its elevated centre.
 */
public final class GroundProjection {
    private GroundProjection() {}
    public static double[] contact(RigidPose baseCamera,double u,double v,
                                   double fx,double fy,double cx,double cy,double groundZ) {
        for(double value:new double[]{u,v,fx,fy,cx,cy,groundZ})
            if(!Double.isFinite(value))throw new IllegalArgumentException("Nonfinite projection");
        if(fx<=0||fy<=0)throw new IllegalArgumentException("Invalid intrinsics");
        double[] origin=baseCamera.translation();
        double[] point=baseCamera.map(new double[]{(u-cx)/fx,(v-cy)/fy,1});
        double[] ray={point[0]-origin[0],point[1]-origin[1],point[2]-origin[2]};
        double norm=Math.sqrt(ray[0]*ray[0]+ray[1]*ray[1]+ray[2]*ray[2]);
        if(ray[2]/norm>-.15)throw new IllegalArgumentException("Ray too close to ground horizon");
        double scale=(groundZ-origin[2])/ray[2];
        if(scale<=0||scale*norm>1500)throw new IllegalArgumentException("Ground outside valid ray");
        return new double[]{origin[0]+scale*ray[0],origin[1]+scale*ray[1],groundZ};
    }
}
