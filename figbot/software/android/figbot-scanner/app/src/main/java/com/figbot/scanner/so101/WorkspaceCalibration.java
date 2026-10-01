package com.figbot.scanner.so101;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Measured rigid AR-world (metres) to robot (millimetres) calibration. No Android dependency. */
public final class WorkspaceCalibration {
    public static final class Sample {
        public final String id;
        private final double[] worldMetres, robotMm;
        public Sample(String id, double[] worldMetres, double[] robotMm) {
            if (id == null || id.trim().isEmpty()) throw new IllegalArgumentException("Measurement ID required");
            this.id = id;
            this.worldMetres = point(worldMetres);
            this.robotMm = point(robotMm);
        }
        public double[] worldMetres() { return worldMetres.clone(); }
        public double[] robotMm() { return robotMm.clone(); }
    }

    /** Acceptance criteria are an explicit application policy, not proof of physical accuracy. */
    public static final class Limits {
        public final double maxRmsMm, maxErrorMm, maxRelativeScaleError;
        public final double minSpanMm, minSpreadMm, heldOutSpanFraction;
        public Limits(double maxRmsMm, double maxErrorMm, double maxRelativeScaleError,
                      double minSpanMm, double minSpreadMm, double heldOutSpanFraction) {
            positive(maxRmsMm); positive(maxErrorMm); positive(maxRelativeScaleError);
            positive(minSpanMm); positive(minSpreadMm); positive(heldOutSpanFraction);
            if (maxErrorMm < maxRmsMm || maxRelativeScaleError >= 1 || heldOutSpanFraction > 1)
                throw new IllegalArgumentException("Invalid calibration limits");
            this.maxRmsMm = maxRmsMm; this.maxErrorMm = maxErrorMm;
            this.maxRelativeScaleError = maxRelativeScaleError;
            this.minSpanMm = minSpanMm; this.minSpreadMm = minSpreadMm;
            this.heldOutSpanFraction = heldOutSpanFraction;
        }
    }

    public static final class Residuals {
        public final int count;
        public final double rmsMm, maxMm;
        private Residuals(int count, double rmsMm, double maxMm) {
            this.count = count; this.rmsMm = rmsMm; this.maxMm = maxMm;
        }
    }

    /** Height field z = ax + by + c, fitted only from measured robot-frame ground points. */
    public static final class GroundPlane {
        public final double a, b, c, minObjectHeightMm, maxObjectHeightMm, pickOffsetMm;
        public final Residuals residuals;
        private final List<double[]> measuredPoints;
        private GroundPlane(double a, double b, double c, List<double[]> points, Residuals residuals,
                            double minHeight, double maxHeight, double offset) {
            this.a = a; this.b = b; this.c = c; this.measuredPoints = points;
            this.residuals = residuals; minObjectHeightMm = minHeight;
            maxObjectHeightMm = maxHeight; pickOffsetMm = offset;
        }
        public static GroundPlane fit(List<double[]> measurements, Limits limits,
                                      double minObjectHeightMm, double maxObjectHeightMm,
                                      double pickOffsetMm) {
            if (limits == null || measurements == null || measurements.size() < 3)
                throw new IllegalArgumentException("At least three measured ground points required");
            finite(minObjectHeightMm); finite(maxObjectHeightMm); finite(pickOffsetMm);
            if (minObjectHeightMm > maxObjectHeightMm || pickOffsetMm < 0)
                throw new IllegalArgumentException("Invalid measured height range / pick offset");
            List<double[]> points = new ArrayList<>();
            for (double[] p : measurements) points.add(point(p));
            double[][] data = points.toArray(new double[0][]);
            checkSpread(data, limits.minSpanMm, limits.minSpreadMm);
            double[] center = mean(data);
            double xx = 0, xy = 0, yy = 0, xz = 0, yz = 0;
            for (double[] p : data) {
                double x = p[0] - center[0], y = p[1] - center[1], z = p[2] - center[2];
                xx += x*x; xy += x*y; yy += y*y; xz += x*z; yz += y*z;
            }
            double det = xx*yy - xy*xy;
            if (det <= 1e-12 * Math.max(1, xx*yy))
                throw new IllegalArgumentException("Ground points must span robot X and Y");
            double a = (xz*yy - yz*xy)/det, b = (yz*xx - xz*xy)/det;
            double c = center[2] - a*center[0] - b*center[1];
            double sum = 0, max = 0;
            for (double[] p : data) {
                double error = Math.abs(p[2] - (a*p[0] + b*p[1] + c));
                sum += error*error; max = Math.max(max, error);
            }
            Residuals residuals = new Residuals(data.length, Math.sqrt(sum/data.length), max);
            accept(residuals, limits);
            return new GroundPlane(a, b, c, points, residuals,
                    minObjectHeightMm, maxObjectHeightMm, pickOffsetMm);
        }
        public double heightAt(double xMm, double yMm) {
            finite(xMm); finite(yMm);
            return a*xMm + b*yMm + c;
        }
        public List<double[]> measuredPoints() {
            List<double[]> result = new ArrayList<>();
            for (double[] p : measuredPoints) result.add(p.clone());
            return Collections.unmodifiableList(result);
        }
    }

    private final Limits limits;
    private final List<Sample> fitSamples;
    private final double[][] rotation;
    private final double[] translation;
    private final double fitSpan;
    private final Residuals fitResiduals;
    private List<Sample> heldOutSamples = Collections.emptyList();
    private Residuals validationResiduals;
    private GroundPlane groundPlane;

    private WorkspaceCalibration(Limits limits, List<Sample> fitSamples,
                                 double[][] rotation, double[] translation, double span) {
        this.limits = limits; this.fitSamples = fitSamples;
        this.rotation = rotation; this.translation = translation; this.fitSpan = span;
        fitResiduals = residuals(fitSamples);
        accept(fitResiduals, limits);
    }

    public static WorkspaceCalibration fit(List<Sample> measurements, Limits limits) {
        if (limits == null) throw new IllegalArgumentException("Explicit calibration limits required");
        List<Sample> samples = samples(measurements, 4);
        double[][] source = coordinates(samples, true), target = coordinates(samples, false);
        double span = checkSpread(target, limits.minSpanMm, limits.minSpreadMm);
        checkSpread(source, limits.minSpanMm, limits.minSpreadMm);
        double[] sourceCenter = mean(source), targetCenter = mean(target);
        double[][] covariance = new double[3][3];
        double sourceVariance = 0, targetVariance = 0;
        for (int k = 0; k < source.length; k++) {
            for (int i = 0; i < 3; i++) {
                double x = source[k][i] - sourceCenter[i];
                sourceVariance += x*x;
                double y = target[k][i] - targetCenter[i];
                targetVariance += y*y;
                for (int j = 0; j < 3; j++) covariance[i][j] += x*(target[k][j] - targetCenter[j]);
            }
        }
        double observedScale = Math.sqrt(targetVariance/sourceVariance);
        if (Math.abs(observedScale - 1) > limits.maxRelativeScaleError)
            throw new IllegalArgumentException("Metres/mm scale or measured distances disagree: " + observedScale);
        // A non-planar reflected data set cannot be represented by a proper rigid rotation.
        double covNorm = 0;
        for (double[] row : covariance) for (double value : row) covNorm += value*value;
        if (determinant(covariance) < -1e-10*Math.pow(covNorm, 1.5))
            throw new IllegalArgumentException("Reflected / left-handed correspondences");
        double[][] r = horn(covariance);
        double[] t = targetCenter.clone();
        double[] rotated = multiply(r, sourceCenter);
        for (int i = 0; i < 3; i++) t[i] -= rotated[i];
        return new WorkspaceCalibration(limits, samples, r, t, span);
    }

    /** Reconstructs from measured data; serialized validation flags and matrices are never trusted. */
    public static WorkspaceCalibration fromData(List<Sample> fitSamples, List<Sample> heldOut,
                                                Limits limits) {
        WorkspaceCalibration result = fit(fitSamples, limits);
        if (heldOut != null && !heldOut.isEmpty()) result.validateHeldOut(heldOut);
        return result;
    }

    public synchronized Residuals validateHeldOut(List<Sample> measurements) {
        validationResiduals = null;
        heldOutSamples = Collections.emptyList();
        List<Sample> checks = samples(measurements, 3);
        for (Sample check : checks) for (Sample trained : fitSamples) {
            if (check.id.equals(trained.id)
                    || distance(check.worldMetres, trained.worldMetres)*1000 < 1e-5
                    || distance(check.robotMm, trained.robotMm) < 1e-5)
                throw new IllegalArgumentException("Validation must use independent held-out locations");
        }
        double requiredSpan = Math.max(limits.minSpanMm, fitSpan*limits.heldOutSpanFraction);
        checkSpread(coordinates(checks, false), requiredSpan, limits.minSpreadMm);
        checkSpread(coordinates(checks, true), requiredSpan, limits.minSpreadMm);
        Residuals result = residuals(checks);
        accept(result, limits);
        heldOutSamples = checks;
        validationResiduals = result;
        return result;
    }

    /** Available before validation for displaying errors, never sufficient to authorize movement. */
    public double[] toRobotMm(double[] worldMetres) {
        double[] p = point(worldMetres);
        for (int i = 0; i < 3; i++) p[i] *= 1000;
        double[] result = multiply(rotation, p);
        for (int i = 0; i < 3; i++) result[i] += translation[i];
        return result;
    }

    public synchronized double[] toPickTargetMm(double[] worldMetres) {
        if (!isValidated() || groundPlane == null)
            throw new IllegalStateException("Independent calibration validation and measured ground required");
        double[] target = toRobotMm(worldMetres);
        if (!containsWorkspace(target)) throw new IllegalArgumentException("Detection outside measured workspace");
        double groundZ = groundPlane.heightAt(target[0], target[1]);
        double height = target[2] - groundZ;
        if (height < groundPlane.minObjectHeightMm || height > groundPlane.maxObjectHeightMm)
            throw new IllegalArgumentException("Detection outside configured ground object height range");
        target[2] = groundZ + groundPlane.pickOffsetMm;
        return target;
    }
    public synchronized void setGroundPlane(GroundPlane plane) {
        if (plane == null) throw new IllegalArgumentException("Measured ground plane required");
        groundPlane = plane;
    }
    public synchronized GroundPlane groundPlane() { return groundPlane; }
    /** No XY extrapolation beyond the convex hull of measured fit and held-out locations. */
    public synchronized boolean containsWorkspace(double[] robotMm) {
        double[] target = point(robotMm);
        List<double[]> points = new ArrayList<>();
        for (Sample sample : fitSamples) points.add(sample.robotMm());
        for (Sample sample : heldOutSamples) points.add(sample.robotMm());
        points.sort((a,b) -> { int x=Double.compare(a[0],b[0]); return x!=0?x:Double.compare(a[1],b[1]); });
        List<double[]> hull = new ArrayList<>();
        for (double[] p : points) {
            while (hull.size()>=2 && cross2(hull.get(hull.size()-2),hull.get(hull.size()-1),p)<=0)
                hull.remove(hull.size()-1);
            hull.add(p);
        }
        int lower = hull.size();
        for (int i=points.size()-2;i>=0;i--) {
            double[] p=points.get(i);
            while(hull.size()>lower && cross2(hull.get(hull.size()-2),hull.get(hull.size()-1),p)<=0)
                hull.remove(hull.size()-1);
            hull.add(p);
        }
        if(hull.size()>1)hull.remove(hull.size()-1);
        if(hull.size()<3)return false;
        for(int i=0;i<hull.size();i++)
            if(cross2(hull.get(i),hull.get((i+1)%hull.size()),target)<-1e-8)return false;
        return true;
    }
    public synchronized boolean isValidated() { return validationResiduals != null; }
    public Residuals fitResiduals() { return fitResiduals; }
    public synchronized Residuals validationResiduals() { return validationResiduals; }
    public List<Sample> fitSamples() { return fitSamples; }
    public synchronized List<Sample> heldOutSamples() { return heldOutSamples; }
    public Limits limits() { return limits; }
    public double[] translationMm() { return translation.clone(); }
    public double[][] rotation() {
        double[][] result = new double[3][];
        for (int i = 0; i < 3; i++) result[i] = rotation[i].clone();
        return result;
    }

    private Residuals residuals(List<Sample> points) {
        double sum = 0, max = 0;
        for (Sample sample : points) {
            double d = distance(toRobotMm(sample.worldMetres), sample.robotMm);
            sum += d*d; max = Math.max(max, d);
        }
        return new Residuals(points.size(), Math.sqrt(sum/points.size()), max);
    }
    private static void accept(Residuals r, Limits limits) {
        if (!Double.isFinite(r.rmsMm) || r.rmsMm > limits.maxRmsMm || r.maxMm > limits.maxErrorMm)
            throw new IllegalArgumentException("Calibration error exceeds policy: RMS=" + r.rmsMm + ", max=" + r.maxMm + " mm");
    }
    private static List<Sample> samples(List<Sample> values, int minimum) {
        if (values == null || values.size() < minimum)
            throw new IllegalArgumentException("At least " + minimum + " measured correspondences required");
        List<Sample> result = new ArrayList<>(); Set<String> ids = new HashSet<>();
        for (Sample sample : values) {
            if (sample == null || !ids.add(sample.id)) throw new IllegalArgumentException("Duplicate / missing measurement ID");
            for (Sample existing : result) {
                if (distance(existing.worldMetres, sample.worldMetres) < 1e-8
                        || distance(existing.robotMm, sample.robotMm) < 1e-5)
                    throw new IllegalArgumentException("Duplicate measured location");
            }
            result.add(sample);
        }
        return Collections.unmodifiableList(result);
    }
    private static double[][] coordinates(List<Sample> samples, boolean world) {
        double[][] result = new double[samples.size()][3];
        for (int i = 0; i < samples.size(); i++) for (int j = 0; j < 3; j++)
            result[i][j] = world ? samples.get(i).worldMetres[j]*1000 : samples.get(i).robotMm[j];
        return result;
    }
    private static double checkSpread(double[][] points, double minSpan, double minSpread) {
        double[] center = mean(points); double[][] covariance = new double[3][3]; double span = 0;
        for (int k = 0; k < points.length; k++) {
            for (int l = 0; l < k; l++) span = Math.max(span, distance(points[k], points[l]));
            for (int i = 0; i < 3; i++) for (int j = 0; j < 3; j++)
                covariance[i][j] += (points[k][i]-center[i])*(points[k][j]-center[j])/points.length;
        }
        double[] eigenvalues = eigen(covariance).values;
        java.util.Arrays.sort(eigenvalues);
        if (span < minSpan || eigenvalues[1] < minSpread*minSpread)
            throw new IllegalArgumentException("Measurements do not span a non-collinear workspace");
        return span;
    }
    private static double[][] horn(double[][] s) {
        double xx=s[0][0], xy=s[0][1], xz=s[0][2], yx=s[1][0], yy=s[1][1], yz=s[1][2];
        double zx=s[2][0], zy=s[2][1], zz=s[2][2];
        double[][] n = {{xx+yy+zz, yz-zy, zx-xz, xy-yx},
                {yz-zy, xx-yy-zz, xy+yx, zx+xz},
                {zx-xz, xy+yx, -xx+yy-zz, yz+zy},
                {xy-yx, zx+xz, yz+zy, -xx-yy+zz}};
        Eigen e = eigen(n); int largest = 0;
        for (int i = 1; i < 4; i++) if (e.values[i] > e.values[largest]) largest = i;
        double w=e.vectors[0][largest], x=e.vectors[1][largest], y=e.vectors[2][largest], z=e.vectors[3][largest];
        return new double[][] {{1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)},
                {2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)},
                {2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)}};
    }
    private static final class Eigen {
        final double[] values; final double[][] vectors;
        Eigen(double[] values, double[][] vectors) { this.values=values; this.vectors=vectors; }
    }
    private static Eigen eigen(double[][] matrix) {
        int n=matrix.length; double[][] a=new double[n][n], v=new double[n][n];
        for (int i=0;i<n;i++) { a[i]=matrix[i].clone(); v[i][i]=1; }
        for (int iteration=0;iteration<100;iteration++) {
            int p=0,q=1; double largest=0, norm=0;
            for (int i=0;i<n;i++) {
                norm=Math.max(norm,Math.abs(a[i][i]));
                for (int j=i+1;j<n;j++) if (Math.abs(a[i][j])>largest) { largest=Math.abs(a[i][j]);p=i;q=j; }
            }
            if (largest <= 1e-14*Math.max(1,norm)) break;
            double angle=.5*Math.atan2(2*a[p][q],a[q][q]-a[p][p]);
            double c=Math.cos(angle), s=Math.sin(angle), app=a[p][p], aqq=a[q][q], apq=a[p][q];
            a[p][p]=c*c*app-2*s*c*apq+s*s*aqq;
            a[q][q]=s*s*app+2*s*c*apq+c*c*aqq; a[p][q]=a[q][p]=0;
            for (int k=0;k<n;k++) {
                if (k!=p && k!=q) {
                    double kp=a[k][p],kq=a[k][q];
                    a[k][p]=a[p][k]=c*kp-s*kq; a[k][q]=a[q][k]=s*kp+c*kq;
                }
                double vp=v[k][p],vq=v[k][q];v[k][p]=c*vp-s*vq;v[k][q]=s*vp+c*vq;
            }
        }
        double[] values=new double[n];for(int i=0;i<n;i++)values[i]=a[i][i];
        return new Eigen(values,v);
    }
    private static double determinant(double[][] m) {
        return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
                -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
                +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);
    }
    private static double[] mean(double[][] points) {
        double[] mean=new double[3];
        for(double[] p:points)for(int i=0;i<3;i++)mean[i]+=p[i]/points.length;
        return mean;
    }
    private static double[] multiply(double[][] m,double[] p) {
        double[] result=new double[3];for(int i=0;i<3;i++)for(int j=0;j<3;j++)result[i]+=m[i][j]*p[j];
        return result;
    }
    private static double[] point(double[] point) {
        if(point==null || point.length!=3)throw new IllegalArgumentException("A finite XYZ point required");
        for(double v:point)finite(v);return point.clone();
    }
    private static double distance(double[] a,double[] b) {
        return Math.hypot(Math.hypot(a[0]-b[0],a[1]-b[1]),a[2]-b[2]);
    }
    private static double cross2(double[] a,double[] b,double[] c) {
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
    }
    private static void finite(double value) {
        if(!Double.isFinite(value))throw new IllegalArgumentException("Nonfinite calibration data");
    }
    private static void positive(double value) {finite(value);if(value<=0)throw new IllegalArgumentException("Positive limit required");}
}
