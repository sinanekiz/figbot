package com.figbot.scanner;

import android.content.Context;
import com.figbot.scanner.so101.*;
import org.json.*;
import java.util.*;

/** Persist measurements, never a trusted 'calibrated=true' switch. AR fits stay session-local.
 * When the bundled fixed camera mount calibration is present, the manual 4+3 point
 * correspondence and 3 ground points are replaced by the constant camera-to-base transform.
 */
final class PhoneSetup {
    static final WorkspaceCalibration.Limits LIMITS=new WorkspaceCalibration.Limits(5,8,.03,80,20,.65);
    final List<WorkspaceCalibration.Sample> fit=new ArrayList<>(),held=new ArrayList<>();
    final List<double[]> groundPoints=new ArrayList<>();
    final Context context;
    ArmProfile profile=ArmProfile.unverifiedDefaults();
    ArmValidation arm=new ArmValidation(profile,8);
    WorkspaceCalibration workspace;
    FixedCameraCalibration fixedCamera;
    boolean homeSaved,basketSaved,closedSaved,openSaved;
    double minHeight=Double.NaN,maxHeight=Double.NaN,pickHeight=Double.NaN,pitch=Double.NaN;
    double jawRadius=Double.NaN,novelty=Double.NaN;
    double groundZ=0;
    PickEvidence.Basket basketVolume;
    PhoneSetup(Context c){context=c.getApplicationContext();loadFixedCamera();load();
        // Fresh install: apply the recorded layout measurements so ground/grip/basket
        // are available immediately. The user can adjust via the dimensions dialog.
        if(basketVolume==null)configure(DEFAULT_DIMENSIONS.clone());}

    /** Recorded installation layout: user-measured basket/fig values from 2026-09-26. */
    static final double[] DEFAULT_DIMENSIONS={20,40,10,0,15,30,0,-100,100,100,100,150};

    /** Supervised test profile: the encoder map physically exercised in the recorded
     * 2026-09-20/21 sessions; fresh tip measurements remain absent by design. */
    synchronized ArmProfile testProfile(){
        return profile.withRecordedSessionValidation(
                "RECORDED_SESSION_2026_09_20_21; no fresh tip measurement; supervised test move");
    }
    static String speedLabel(int speed){
        if(speed<=SPEED_SLOW+50)return "Hız: Yavaş";
        if(speed<=SPEED_MEDIUM+50)return "Hız: Orta";
        return "Hız: Hızlı";
    }
    static final int SPEED_SLOW=300,SPEED_MEDIUM=700,SPEED_FAST=1200;

    /** The bundled asset defines the rigid camera-to-base mount; loading never authorizes motion. */
    private void loadFixedCamera(){
        try(java.io.InputStream in=context.getAssets().open("camera_calibration.json")){
            fixedCamera=FixedCameraCalibration.fromAsset(in);
        }catch(Exception e){fixedCamera=null;}
    }
    /** True when the fixed camera mount asset is available for this install. */
    boolean fixedCameraAvailable(){return fixedCamera!=null;}
    synchronized ArmProfile effectiveProfile(){return profile.withPhysicalCalibrationVerified(arm.isValid());}
    synchronized String missing(){
        List<String> missing=new ArrayList<>();
        if(!homeSaved||!basketSaved)missing.add("başlangıç / sepet duruşu");
        if(!closedSaved||!openSaved)missing.add("kıskaç açık / kavrama konumu");
        if(!arm.isValid())missing.add("3 bağımsız uç-konum ölçümü");
        if(fixedCamera==null){
            if(workspace==null||!workspace.isValidated())missing.add("4 eşleme + 3 kontrol noktası");
            if(workspace==null||workspace.groundPlane()==null)missing.add("zemin ve kavrama yüksekliği");
        }else{
            if(!fixedCamera.isReady())missing.add("kamera görüntüsü (pozu otomatik alınır)");
            if(fixedCamera.ground()==null)missing.add("zemin ve kavrama yüksekliği ölçüleri");
        }
        if(basketVolume==null||!Double.isFinite(jawRadius)||!Double.isFinite(novelty)||!Double.isFinite(pitch))missing.add("kıskaç / sepet ölçüleri");
        return String.join(", ",missing);
    }
    synchronized void capture(String name,int[]raw){
        if(raw==null||raw.length!=6)throw new IllegalArgumentException("Önce altı motoru oku.");
        int[] home=profile.home(),basket=profile.basket();int closed=profile.gripperClosed(),open=profile.gripperOpen();
        switch(name){
            case "home" -> home=raw.clone();
            case "basket" -> basket=raw.clone();
            case "closed" -> closed=raw[5];
            case "open" -> open=raw[5];
            default -> throw new IllegalArgumentException("Bilinmeyen kayıt.");
        }
        if(closed>=open)throw new IllegalArgumentException("Açık kıskaç konumu kapalıdan büyük olmalı.");
        ArmProfile next=profile.withSavedPoses(home,basket,closed,open);
        if(Math.abs(home[4]-basket[4])>12)throw new IllegalArgumentException("Başlangıç ve sepette bilek dönüşü sabit kalmalı.");
        profile=next;
        switch(name){case "home" -> homeSaved=true;case "basket" -> basketSaved=true;case "closed" -> closedSaved=true;case "open" -> openSaved=true;default -> {}}
        save();
    }
    synchronized void addPoint(String type,double[]world,double[]robot){
        if(fixedCamera!=null&&(type.equals("fit")||type.equals("held")||type.equals("ground")))
            throw new IllegalStateException("Sabit kamera montajı etkin; manuel nokta ölçümüne gerek yok.");
        WorkspaceCalibration.Sample sample=new WorkspaceCalibration.Sample(UUID.randomUUID().toString(),world,robot);
        if(type.equals("fit")){
            List<WorkspaceCalibration.Sample> trial=new ArrayList<>(fit);trial.add(sample);
            WorkspaceCalibration next=trial.size()>=4?WorkspaceCalibration.fit(trial,LIMITS):null;
            fit.clear();fit.addAll(trial);held.clear();workspace=next;
        }else if(type.equals("held")){
            if(workspace==null)throw new IllegalStateException("Önce en az 4 eşleme noktası al.");
            List<WorkspaceCalibration.Sample> trial=new ArrayList<>(held);trial.add(sample);
            if(trial.size()>=3)workspace.validateHeldOut(trial);
            held.clear();held.addAll(trial);
        }else if(type.equals("ground")){
            List<double[]> trial=new ArrayList<>(groundPoints);trial.add(robot.clone());
            if(trial.size()>=3&&Double.isFinite(pickHeight))
                WorkspaceCalibration.GroundPlane.fit(trial,LIMITS,minHeight,maxHeight,pickHeight);
            groundPoints.clear();groundPoints.addAll(trial);
        }else throw new IllegalArgumentException("Bilinmeyen ölçüm türü.");
        rebuildGround();save();
    }
    synchronized void configure(double[]v){
        if(v.length!=12)throw new IllegalArgumentException("12 ölçüm gerekli.");
        for(double d:v)if(!Double.isFinite(d))throw new IllegalArgumentException("Bütün ölçüleri milimetre olarak doldur.");
        if(v[0]<0||v[1]<v[0]||v[2]<0||v[2]>v[1]||Math.abs(v[3])>90||v[4]<=0||v[5]<=0)
            throw new IllegalArgumentException("Yükseklik, açı veya kavrama ölçüsü geçersiz.");
        PickEvidence.Basket volume=new PickEvidence.Basket(v[7],v[8],v[9],v[10],v[11]);
        groundZ=v[6];
        minHeight=v[0];maxHeight=v[1];pickHeight=v[2];pitch=Math.toRadians(v[3]);jawRadius=v[4];novelty=v[5];basketVolume=volume;
        if(fixedCamera!=null)
            fixedCamera.setGround(new FixedCameraCalibration.FlatGround(groundZ,minHeight,maxHeight,pickHeight));
        else{
            WorkspaceCalibration.GroundPlane ground=groundPoints.size()>=3?
                WorkspaceCalibration.GroundPlane.fit(groundPoints,LIMITS,v[0],v[1],v[2]):null;
            if(workspace!=null&&ground!=null)workspace.setGroundPlane(ground);
        }
        save();
    }
    synchronized void clearWorkspace(){fit.clear();held.clear();groundPoints.clear();workspace=null;save();}
    private void rebuildGround(){if(workspace!=null&&groundPoints.size()>=3&&Double.isFinite(pickHeight))
        workspace.setGroundPlane(WorkspaceCalibration.GroundPlane.fit(groundPoints,LIMITS,minHeight,maxHeight,pickHeight));}
    synchronized double[] dimensions(){return new double[]{minHeight,maxHeight,pickHeight,Math.toDegrees(pitch),jawRadius,novelty,groundZ,
        basketVolume==null?Double.NaN:basketVolume.x(),basketVolume==null?Double.NaN:basketVolume.y(),
        basketVolume==null?Double.NaN:basketVolume.radius(),basketVolume==null?Double.NaN:basketVolume.bottom(),basketVolume==null?Double.NaN:basketVolume.top()};}
    synchronized void save(){
        try{
            JSONObject j=new JSONObject();j.put("schema",1);j.put("home",array(profile.home()));j.put("basket",array(profile.basket()));
            j.put("closed",profile.gripperClosed());j.put("open",profile.gripperOpen());j.put("home_saved",homeSaved);j.put("basket_saved",basketSaved);
            j.put("closed_saved",closedSaved);j.put("open_saved",openSaved);
            JSONArray measurements=new JSONArray();for(ArmValidation.Measurement m:arm.measurements())
                measurements.put(new JSONObject().put("raw",array(m.raw())).put("measured_mm",array(m.measuredMm())));
            j.put("arm_measurements",measurements);JSONArray dim=new JSONArray();for(double v:dimensions())dim.put(Double.isFinite(v)?v:JSONObject.NULL);j.put("dimensions",dim);
            // Retained for audit only: a new AR session must collect its own world transform.
            JSONArray audit=new JSONArray();for(WorkspaceCalibration.Sample m:fit)audit.put(new JSONObject().put("world_m",array(m.worldMetres())).put("robot_mm",array(m.robotMm())));
            j.put("last_session_fit_audit_only",audit);
            context.getSharedPreferences("phone-so101",Context.MODE_PRIVATE).edit().putString("measurements",j.toString()).apply();
        }catch(JSONException e){throw new IllegalStateException("Ölçümler kaydedilemedi.",e);}
    }
    private void load(){
        try{
            String raw=context.getSharedPreferences("phone-so101",Context.MODE_PRIVATE).getString("measurements","");if(raw.isEmpty())return;
            JSONObject j=new JSONObject(raw);if(j.getInt("schema")!=1)return;
            profile=profile.withSavedPoses(ints(j.getJSONArray("home")),ints(j.getJSONArray("basket")),j.getInt("closed"),j.getInt("open"));
            homeSaved=j.getBoolean("home_saved");basketSaved=j.getBoolean("basket_saved");closedSaved=j.getBoolean("closed_saved");openSaved=j.getBoolean("open_saved");
            arm=new ArmValidation(profile,8);JSONArray ms=j.getJSONArray("arm_measurements");
            for(int i=0;i<ms.length();i++){JSONObject m=ms.getJSONObject(i);arm.add(ints(m.getJSONArray("raw")),doubles(m.getJSONArray("measured_mm")));}
            JSONArray dim=j.getJSONArray("dimensions");boolean complete=true;for(int i=0;i<dim.length();i++)complete&=!dim.isNull(i);
            if(complete)configure(doubles(dim));
        }catch(Exception e){profile=ArmProfile.unverifiedDefaults();arm=new ArmValidation(profile,8);homeSaved=basketSaved=closedSaved=openSaved=false;}
    }
    private static JSONArray array(int[]v){JSONArray a=new JSONArray();for(int n:v)a.put(n);return a;}
    private static JSONArray array(double[]v)throws JSONException{JSONArray a=new JSONArray();for(double n:v)a.put(n);return a;}
    private static int[] ints(JSONArray a)throws JSONException{int[]v=new int[a.length()];for(int i=0;i<v.length;i++)v[i]=a.getInt(i);return v;}
    private static double[] doubles(JSONArray a)throws JSONException{double[]v=new double[a.length()];for(int i=0;i<v.length;i++)v[i]=a.getDouble(i);return v;}
}
