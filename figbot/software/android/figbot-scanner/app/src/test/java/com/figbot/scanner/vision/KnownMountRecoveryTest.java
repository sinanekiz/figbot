package com.figbot.scanner.vision;
import java.util.*;import java.io.*;import org.junit.Test;import static org.junit.Assert.*;
/** Rounded transcription of seven live observations at 22:27:53--22:28:10.
 * First three train, last four held out; independent Python check RMS5.7197/max8.0206mm. */
public class KnownMountRecoveryTest {
 private static final String RECORD="4642433100fb6f70656e63762d63616d6572612d6d6d2d76313b7461673d444943545f3458345f35303a303a33363b336136356432643335653638613864326630633263633137366431396238383435303635343363393362613732393830313435623830616265323736303232635b313939362c20313832342c20333130372c20313837382c20343230385d5b302e302c202d302e32343337383638393331383030393635352c20302e3238323331343839303032323233352c202d302e30333835323739393638343231333834342c20302e305d5b312c20312c20312c20312c20315d5b343038302c20323836312c2038352c2038352c2038352c2038355d4042000000000000bfad122e141b5ff5bfb61d6c66da284a3fefd41c47b326c2bfeff24c853bbedf3f9024fb7f0631f8bfac7a464841b8dfbf86468e06b63127bfefe05a9516a32abfb64e9f2941c027c06413d6fc437f4ec05c89a44c534f904056f8ef7815fecbbf808cff7a8ee680bf9861bdf22161243feffd68f0d5ad60bf9e571c327f2b7a3feffa20d40d53f63f98207397e1cdc2bfeffc22c09f4206bf9e22bd65bb576ebf81fbd61a0afe00403d825385cd1b8540161d4aa1c412fbc050b10cae252f253ffaed105f3f091640043896f3bfae21400545886c445dc5";
 private MarkerCalibration.Result prior()throws Exception {
  byte[] bytes=new byte[RECORD.length()/2];for(int i=0;i<bytes.length;i++)bytes[i]=(byte)Integer.parseInt(RECORD.substring(2*i,2*i+2),16);
  var in=new DataInputStream(new ByteArrayInputStream(bytes));in.readInt();return CalibrationRecord.decode(RECORD,in.readUTF());
 }
 private List<MarkerCalibration.Sample> samples(){List<MarkerCalibration.Sample>s=new ArrayList<>();
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.14188662,-0.638795686,0.756180044},{-0.989689445,0.106647572,-0.095609084},{-0.019570095,-0.761949058,-0.647341212}},new double[]{184.0009606,-26.5008519,99.3243109}),new RigidPose(new double[][]{{-0.208927282,-0.210816013,0.954937694},{-0.592896537,0.803861923,0.04774626},{-0.777703727,-0.556203755,-0.292940771}},new double[]{-50.7633678,-44.9553446,300.9240794})));
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.614330698,-0.526770394,0.58746127},{-0.788823113,0.427811473,-0.441288385},{-0.018865015,-0.73450003,-0.678346384}},new double[]{164.7746939,-104.7115924,74.4422109}),new RigidPose(new double[][]{{-0.522990799,-0.520625494,0.674855332},{-0.668253293,0.741934801,0.054500344},{-0.529072925,-0.422471119,-0.735934775}},new double[]{-7.30280365,-21.2062275,272.4351732})));
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.399946117,-0.778278811,0.484071478},{-0.916440121,0.347321941,-0.198758583},{-0.013439052,-0.523115247,-0.85215599}},new double[]{156.1680675,-56.9139608,45.9707376}),new RigidPose(new double[][]{{-0.278115641,-0.481153539,0.831350084},{-0.836487682,0.546761421,0.03661019},{-0.472165276,-0.685232238,-0.554541912}},new double[]{-33.088456,-5.14771148,281.1698033})));
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.144422438,-0.678264389,0.720485654},{-0.989340345,0.112700537,-0.092218607},{-0.018650523,-0.726123961,-0.687310811}},new double[]{199.2164478,-28.6763338,71.4272051}),new RigidPose(new double[][]{{-0.21696209,-0.238770064,0.946528557},{-0.669068223,0.7424265,0.033920564},{-0.710827098,-0.625932703,-0.320831868}},new double[]{-44.746729,-21.3361806,323.2924706})));
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.384894269,-0.413546512,0.825127678},{-0.92267796,0.194530735,-0.332901149},{-0.022842586,-0.889458867,-0.456444017}},new double[]{208.0874418,-77.0006559,92.147026}),new RigidPose(new double[][]{{-0.452612251,-0.293647707,0.841969818},{-0.46818815,0.881860182,0.055879114},{-0.758908431,-0.368908721,-0.536623099}},new double[]{-15.0509613,-22.3880027,315.4758983})));
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.618013013,-0.670144807,0.411054563},{-0.786056991,0.535513059,-0.308772036},{-0.01320311,-0.513937449,-0.85772605}},new double[]{141.391097,-87.1459089,60.3087999}),new RigidPose(new double[][]{{-0.372826085,-0.638820629,0.672985078},{-0.846351448,0.531434653,0.035587004},{-0.380381304,-0.556314132,-0.738799466}},new double[]{-20.0292887,-20.1180841,258.1909039})));
s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.15015758,-0.842310052,0.517654786},{-0.988571186,0.135017527,-0.067061752},{-0.013405681,-0.521808436,-0.852957352}},new double[]{164.0898919,-24.3767297,28.7861554}),new RigidPose(new double[][]{{-0.151726484,-0.284987447,0.946446634},{-0.835732655,0.548254654,0.031108903},{-0.527759419,-0.786256312,-0.321358067}},new double[]{-49.8631645,12.1887008,300.924433})));
return s;}
 @Test public void recoversInterruptedLiveScanWithUnchangedMount()throws Exception {
  var old=prior();var result=MarkerCalibration.fitKnownMount(samples(),old.toolMarker());
  assertEquals(5.7197,result.heldRmsMm(),.02);assertEquals(8.0206,result.heldMaxMm(),.02);
  assertArrayEquals(old.toolMarker().translation(),result.toolMarker().translation(),0);
  assertEquals(0,old.toolMarker().angle(result.toolMarker()),1e-7);
 }
 @Test public void doesNotFitAwayBadHeldOutPoint()throws Exception {
  var s=samples();var last=s.get(6);double[]t=last.worldMarker().translation();t[0]+=50;
  s.set(6,new MarkerCalibration.Sample(last.baseTool(),new RigidPose(last.worldMarker().rotation(),t)));
  var mount=prior().toolMarker();assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,mount));
 }
 @Test public void onePoseRepeatedSevenTimesCannotValidate()throws Exception {
  var mount=prior().toolMarker();var s=Collections.nCopies(7,samples().get(0));
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,mount));
 }
 @Test public void knownMountNeedsFourIndependentPosesButNotRotationalExcitation(){
  var camera=poseZ(23,new double[]{-120,70,240});
  var mount=poseZ(-17,new double[]{25,5,-65});
  var s=translationSamples(camera,mount,4);
  var result=MarkerCalibration.fitKnownMount(s,mount);
  assertEquals(2,MarkerCalibration.KNOWN_MOUNT_FIT_COUNT);
  assertEquals(4,MarkerCalibration.KNOWN_MOUNT_TOTAL_COUNT);
  assertEquals(0,result.baseWorld().distance(camera),1e-5);
  assertEquals(0,result.baseWorld().angle(camera),1e-7);
  assertEquals(0,result.heldRmsMm(),1e-5);
  assertSame(mount,result.toolMarker());
 }
 @Test public void unknownMountStillRejectsTranslationOnlyMeasurements(){
  var s=translationSamples(RigidPose.identity(),RigidPose.identity(),12);
  var error=assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fit(s));
  assertTrue(error.getMessage().contains("Duruş çeşitliliği az"));
 }
 @Test public void twoTrainingOrTwoHeldDuplicatePosesAreNotIndependentChecks(){
  var camera=poseZ(10,new double[]{50,-40,300});var mount=poseZ(-5,new double[]{20,0,-60});
  for(int[] duplicate:new int[][]{{1,0},{3,2},{3,0}}){
   var s=translationSamples(camera,mount,4);s.set(duplicate[0],s.get(duplicate[1]));
   assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,mount));
  }
 }
 @Test public void movedCameraInHeldSamplesCannotBeFittedAway(){
  var camera=poseZ(10,new double[]{50,-40,300});var mount=poseZ(-5,new double[]{20,0,-60});
  var s=translationSamples(camera,mount,4);
  var moved=poseZ(10,new double[]{75,-40,300});
  for(int i=2;i<4;i++)s.set(i,new MarkerCalibration.Sample(s.get(i).baseTool(),
          moved.inverse().compose(s.get(i).baseTool()).compose(mount)));
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,mount));
 }
 @Test public void wrongMountOrientationIsRejectedByUnseenTranslations(){
  var camera=poseZ(10,new double[]{50,-40,300});var mount=poseZ(-5,new double[]{20,0,-60});
  var s=translationSamples(camera,mount,4);
  var wrong=poseZ(20,new double[]{20,0,-60});
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,wrong));
 }
 @Test public void angularValidationCapRemainsEvenWithDistinctPositions(){
  var camera=poseZ(10,new double[]{50,-40,300});var mount=poseZ(-5,new double[]{20,0,-60});
  var s=translationSamples(camera,mount,4);var last=s.get(3);
  // Move orientation while holding the inferred TCP position, isolating the
  // existing eight-degree orientation guard from positional residual limits.
  var wrongTool=poseZ(9,last.baseTool().translation());
  s.set(3,new MarkerCalibration.Sample(last.baseTool(),camera.inverse().compose(wrongTool).compose(mount)));
  var error=assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,mount));
  assertTrue(error.getMessage().contains("Etiket yönü"));
 }
 @Test public void incompleteOrMissingMountCannotTriggerShortFit(){
  var s=translationSamples(RigidPose.identity(),RigidPose.identity(),4);
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(null,RigidPose.identity()));
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,null));
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s.subList(0,3),RigidPose.identity()));
  s.set(2,null);
  assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,RigidPose.identity()));
 }
 private List<MarkerCalibration.Sample> translationSamples(RigidPose camera,RigidPose mount,int count){
  List<MarkerCalibration.Sample>s=new ArrayList<>();
  for(int i=0;i<count;i++){
   RigidPose base=poseZ(0,new double[]{100+20*i,-30,80});
   s.add(new MarkerCalibration.Sample(base,camera.inverse().compose(base).compose(mount)));
  }
  return s;
 }
 private RigidPose poseZ(double degrees,double[] t){
  double a=Math.toRadians(degrees),c=Math.cos(a),s=Math.sin(a);
  return new RigidPose(new double[][]{{c,-s,0},{s,c,0},{0,0,1}},t);
 }

 // Exact logged 2026-09-29 02:35:19--02:35:36 observations. No pose selection.
 private List<MarkerCalibration.Sample> liveSeptember29(){
  List<MarkerCalibration.Sample> s=new ArrayList<>();
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.7241948946856592,-0.43122425826511546,0.5381332489216103},{-0.6893459914907366,0.4736807440185588,-0.548113726120481},{-0.018543422739079527,-0.767901160195585,-0.6402998903977682}},new double[]{148.13495976227517,-122.86310729770518,58.975472080472336}),new RigidPose(new double[][]{{-0.5615631182598863,0.7961072387506869,0.22552190274780415},{0.6953863896799855,0.6017877779476303,-0.39279668959996294},{-0.4484246126809597,-0.06375527210835955,-0.8915439596679012}},new double[]{43.62092424647476,41.119170712001136,268.85873926630217})));
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.8740749983647557,-0.2493095413464232,0.4169384245032934},{-0.48536858457573295,0.4839721170575523,-0.7281403209669},{-0.020254242533404226,-0.8388180628148557,-0.544034946630206}},new double[]{116.12318382174976,-151.23988395460475,97.74379910599588}),new RigidPose(new double[][]{{-0.4923906078685847,0.8245261986839443,0.278761613151112},{0.8209144473014833,0.5463746886839308,-0.1660547192260353},{-0.2892247560194418,0.14707565144966037,-0.9458952337633129}},new double[]{17.546758862953208,44.28169874645016,229.65322479440272})));
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.7281240099993747,-0.5050440919068235,0.4634284101049944},{-0.685258171125809,0.5521459051958435,-0.4749275084481568},{-0.016020766765123196,-0.6633742266665736,-0.7481162813538969}},new double[]{131.89448504434046,-106.94086306357309,65.61561607951555}),new RigidPose(new double[][]{{-0.666949527389378,0.7064017633482726,0.2370123976789743},{0.6073206208089417,0.6996688927787861,-0.3763311095537403},{-0.43167116125046745,-0.10705133916097684,-0.8956561948250649}},new double[]{32.20466664779757,59.091956171795346,262.1211626875781})));
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.5214172322420211,-0.4609885808137301,0.7180623916348868},{-0.8530638239302689,0.30148780500898964,-0.42589578036454967},{-0.020153962948697732,-0.8346224486498102,-0.5504536183796577}},new double[]{179.97537928624112,-93.10954315949782,96.90771748291574}),new RigidPose(new double[][]{{-0.44452941992095313,0.8792735137581692,0.171089692349082},{0.6729466358270161,0.45386812497204354,-0.5840775209366158},{-0.5912160520096205,-0.1445054086798283,-0.7934618873697927}},new double[]{7.639868117716846,51.37480078151417,299.6759448655235})));
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.7153172880415387,-0.1974143674121719,0.6703348006542327},{-0.6984216006003321,0.23352757237334879,-0.6765147010644194},{-0.022987936918488695,-0.9520989656966666,-0.30492476822253894}},new double[]{165.1953742299253,-139.0074652846346,119.98692107275497}),new RigidPose(new double[][]{{-0.27324485439592683,0.9331649477400304,0.23353892578218088},{0.85949002640631,0.3458642620114295,-0.376370571075064},{-0.4319885925047435,0.09788305559511021,-0.8965515954885894}},new double[]{9.878246425386939,30.533935516803197,272.50115896662453})));
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.8765350964493093,-0.35119407296626554,0.3291640135342341},{-0.4810722025735174,0.6619060255034684,-0.5748477618580996},{-0.01599251711472686,-0.6622258953828117,-0.7491335681177074}},new double[]{103.38219522575254,-128.9885783767357,83.02984589774717}),new RigidPose(new double[][]{{-0.6980299891583017,0.6691297331070035,0.25498928312345104},{0.6525229691653426,0.7410428278153708,-0.15833288368195791},{-0.294903219628587,0.05586526304913665,-0.9538926372695955}},new double[]{18.691682698870565,61.701012853762506,227.2555365058396})));
  s.add(new MarkerCalibration.Sample(new RigidPose(new double[][]{{-0.5295974437322525,-0.6360225184599928,0.5612503038788238},{-0.8481019723012576,0.40934986669437246,-0.33638628274056587},{-0.015798486350922597,-0.6541468051203091,-0.7562025953274106}},new double[]{155.24989570432058,-79.19598630351905,47.909828841842774}),new RigidPose(new double[][]{{-0.6986235418487341,0.6926907198533016,0.17917788201629475},{0.483329484434134,0.6415477712036167,-0.5956585152084264},{-0.5275582965430119,-0.3295391082903332,-0.7829982246824366}},new double[]{48.80062858770801,62.5898019105817,294.4038835002753})));
  return s;
 }
 @Test public void liveSeptember29ResidualFailureMustNotBeHiddenByDiversityOrShorterScan()throws Exception {
  var mount=prior().toolMarker();var s=liveSeptember29();
  var seven=assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s,mount));
  assertTrue(seven.getMessage(),seven.getMessage().contains("Kısa eşleme kontrolü"));
  assertTrue(seven.getMessage(),seven.getMessage().contains("kontrol 9.8"));
  var four=assertThrows(IllegalArgumentException.class,()->MarkerCalibration.fitKnownMount(s.subList(0,4),mount));
  assertTrue(four.getMessage(),four.getMessage().contains("kontrol 8.1"));
 }
}
