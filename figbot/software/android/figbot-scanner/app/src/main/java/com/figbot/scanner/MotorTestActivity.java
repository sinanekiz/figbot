package com.figbot.scanner;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.bluetooth.*;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.view.WindowManager;
import android.widget.*;
import java.util.ArrayList;
import java.util.List;

public final class MotorTestActivity extends Activity {
    private BluetoothServoLink link;
    private TextView status;
    private final List<Row> rows=new ArrayList<>();
    private LinearLayout armOne,armTwo;
    private boolean visible;
    private int generation;
    private BluetoothServoLink.State state;
    private static final int[] SPEEDS={10,30,60,90,120,150,180,240,300,360};
    private static final class Row {
        int ch, speed=ServoProtocol.DEFAULT_COMMAND_SPEED, pairMin=ServoProtocol.DEFAULT_PAIR_MIN_US; TextView target,ack; SeekBar slider;
        boolean reverse,wide,rearm; Button centre;
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout root=ControlUi.column(this);setContentView(root);ControlUi.insets(this,root);
        ControlUi.text(this,root,"Motor testleri",25);
        status=ControlUi.text(this,root,"HC-05 bağlı değil",14);
        LinearLayout buttons=new LinearLayout(this);root.addView(buttons);
        Button bt=new Button(this);bt.setText("HC-05 bağlan");buttons.addView(bt,new LinearLayout.LayoutParams(0,-2,1));bt.setOnClickListener(v->chooseDevice());
        Button disconnect=new Button(this);disconnect.setText("Bağlantıyı kes");buttons.addView(disconnect,new LinearLayout.LayoutParams(0,-2,1));disconnect.setOnClickListener(v->{if(link!=null)link.disconnect();});
        Button stop=ControlUi.button(this,root,"DURDUR · Tüm motorlar",v->{if(link!=null)link.stop();});stop.setTextColor(0xffb52327);
        ControlUi.text(this,root,"Kaydırıcıyı sürüklerken hedef güncellenir. Hız ve motor ayarları ⚙ içinde.",12);
        Spinner arm=new Spinner(this);arm.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Kol 1 · CH0–5","Kol 2 · CH6–11"}));root.addView(arm);
        ScrollView scroller=new ScrollView(this);root.addView(scroller,new LinearLayout.LayoutParams(-1,0,1));LinearLayout body=ControlUi.column(this);scroller.addView(body);
        armOne=ControlUi.column(this);armTwo=ControlUi.column(this);body.addView(armOne);body.addView(armTwo);armTwo.setVisibility(View.GONE);
        for(int base:new int[]{0,6}) {
            LinearLayout parent=base==0?armOne:armTwo;
            String[] names={"Taban dönüşü · MG996R","Omuz çifti · 2 × MG996R","Dirsek · MG996R","Bilek · MG90S","Tutucu / kıskaç · MG90S"};
            int[] offsets={0,1,3,4,5};for(int i=0;i<5;i++)makeRow(parent,base+offsets[i],names[i]);
        }
        arm.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            public void onNothingSelected(android.widget.AdapterView<?> p){}
            public void onItemSelected(android.widget.AdapterView<?> p,View v,int pos,long id){
                armOne.setVisibility(pos==0?View.VISIBLE:View.GONE);armTwo.setVisibility(pos==1?View.VISIBLE:View.GONE);
            }
        });
        ControlUi.button(this,root,"Menüye dön",v->finish());
        update(null);
    }
    private void makeRow(LinearLayout parent,int ch,String name) {
        Row r=new Row();r.ch=ch;r.wide=!ServoProtocol.paired(ch)&&ServoProtocol.DEFAULT_WIDE_RANGE;rows.add(r);
        LinearLayout heading=new LinearLayout(this);parent.addView(heading);
        TextView title=new TextView(this);title.setText(name);title.setTextSize(18);heading.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        Button settings=new Button(this);settings.setText("⚙");settings.setTextSize(24);settings.setContentDescription(name+" ayarları");settings.setMinWidth(0);settings.setMinimumWidth(0);heading.addView(settings,new LinearLayout.LayoutParams(ControlUi.dp(this,56),ControlUi.dp(this,56)));settings.setOnClickListener(v->settings(r,name));
        r.target=ControlUi.text(this,parent,"Hedef:90°",15);
        r.slider=new SeekBar(this);r.slider.setMax(180);r.slider.setProgress(90);r.slider.setContentDescription(name+" hedef açısı0–180");parent.addView(r.slider,new LinearLayout.LayoutParams(-1,ControlUi.dp(this,48)));
        r.slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(SeekBar b){}
            public void onStopTrackingTouch(SeekBar b){}
            public void onProgressChanged(SeekBar b,int value,boolean user){
                r.target.setText("Hedef:"+value+"°");
                if(user&&b.isEnabled())move(r,value);
            }
        });
        r.centre=ControlUi.button(this,parent,"90° merkeze git",v->{r.slider.setProgress(90);move(r,90);});
        r.ack=ControlUi.text(this,parent,"UNO hedef onayı: —",12);
    }
    private void settings(Row r,String name) {
        ScrollView scroll=new ScrollView(this);LinearLayout panel=ControlUi.column(this);scroll.addView(panel);
        CheckBox enabled=new CheckBox(this);enabled.setText("Motor etkin");enabled.setChecked(state!=null&&state.ready()&&(state.enabled()&ServoProtocol.mask(r.ch))==ServoProtocol.mask(r.ch));panel.addView(enabled);
        ControlUi.text(this,panel,"Komut hızı · derece/saniye",14);
        String[] labels=new String[SPEEDS.length];int selected=0;
        for(int i=0;i<SPEEDS.length;i++){labels[i]=SPEEDS[i]+"°/sn";if(SPEEDS[i]==r.speed)selected=i;}
        Spinner speed=new Spinner(this);speed.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,labels));speed.setSelection(selected);panel.addView(speed);
        CheckBox reverse=new CheckBox(this);reverse.setText("Yönü ters çevir");reverse.setChecked(r.reverse);panel.addView(reverse);
        CheckBox wide=new CheckBox(this);wide.setText("Geniş darbe: 500–2500 µs");wide.setChecked(r.wide);wide.setVisibility(ServoProtocol.paired(r.ch)?View.GONE:View.VISIBLE);panel.addView(wide);
        Spinner range=new Spinner(this);
        range.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"1000–2000 µs","900–2100 µs","800–2200 µs","700–2300 µs","600–2400 µs","500–2500 µs · varsayılan"}));
        range.setSelection((1000-r.pairMin)/100);range.setVisibility(ServoProtocol.paired(r.ch)?View.VISIBLE:View.GONE);panel.addView(range);
        ControlUi.text(this,panel,"Açı ve hız komut ölçeğidir; gerçek mil hareketi ölçülmez. Darbe aralığını yalnız yükten ayrık motorlarda kademeli dene; zorlanmada dur. Aralık değişince omuz yeniden merkezlenmelidir. PWM kapatıldığında kol düşebilir.",13);
        new AlertDialog.Builder(this).setTitle(name+" · Ayarlar").setView(scroll).setNegativeButton("Vazgeç",null).setPositiveButton("Uygula",(dialog,which)->{
            int nextMin=1000-100*range.getSelectedItemPosition();boolean rangeChanged=ServoProtocol.paired(r.ch)&&nextMin!=r.pairMin;
            r.speed=SPEEDS[speed.getSelectedItemPosition()];r.reverse=reverse.isChecked();r.wide=!ServoProtocol.paired(r.ch)&&wide.isChecked();r.pairMin=nextMin;
            boolean wasEnabled=state!=null&&state.ready()&&(state.enabled()&ServoProtocol.mask(r.ch))==ServoProtocol.mask(r.ch);
            if(link!=null&&state!=null&&state.ready()&&(rangeChanged||wasEnabled!=enabled.isChecked())){r.rearm=rangeChanged;link.arm(r.ch,enabled.isChecked());}
            update(state);
        }).show();
    }
    private void move(Row r,int angle) {
        if(link==null||state==null||!state.ready())return;
        int mask=ServoProtocol.mask(r.ch);
        if((state.enabled()&mask)!=mask||r.rearm)return;
        if(ServoProtocol.paired(r.ch)&&(state.active()&mask)!=mask&&angle!=90)return;
        link.move(r.ch,r.reverse?180-angle:angle,r.speed,r.wide,r.pairMin);
    }
    private void update(BluetoothServoLink.State next) {
        state=next;if(status!=null)status.setText(next==null?"HC-05 bağlı değil":next.message());
        for(Row r:rows) {
            boolean ready=next!=null&&next.ready(),enabled=ready&&(next.enabled()&ServoProtocol.mask(r.ch))==ServoProtocol.mask(r.ch);
            boolean active=enabled&&(next.active()&ServoProtocol.mask(r.ch))==ServoProtocol.mask(r.ch);
            if(!active)r.rearm=false;
            r.centre.setEnabled(enabled);
            r.centre.setVisibility(ServoProtocol.paired(r.ch)&&enabled&&(!active||r.rearm)?View.VISIBLE:View.GONE);
            r.slider.setEnabled(enabled&&(!ServoProtocol.paired(r.ch)||(active&&!r.rearm)));
            r.ack.setText(!enabled?"Pasif · Ayarlar'dan etkinleştir":ServoProtocol.paired(r.ch)&&!active?"İlk hareket: 90° merkeze git":next!=null&&next.acknowledged()[r.ch]?"Hedef onayı: "+next.angles()[r.ch]+"°":"Komuta hazır");
        }
    }
    @Override protected void onResume(){super.onResume();visible=true;int current=++generation;link=new BluetoothServoLink(s->runOnUiThread(()->{if(visible&&generation==current)update(s);}));update(null);}
    @Override protected void onPause(){visible=false;++generation;if(link!=null){link.shutdown();link=null;}super.onPause();}
    private void chooseDevice() {
        if(Build.VERSION.SDK_INT>=31 && checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT},52);return;}
        try {
            BluetoothManager manager=getSystemService(BluetoothManager.class);BluetoothAdapter adapter=manager==null?null:manager.getAdapter();
            if(adapter==null){notice("Bu cihazda Bluetooth yok.");return;}
            if(!adapter.isEnabled()){startActivity(new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE));return;}
            List<BluetoothDevice> devices=new ArrayList<>(adapter.getBondedDevices());
            String[] names=new String[devices.size()];for(int i=0;i<names.length;i++)names[i]=devices.get(i).getName()+"\n"+devices.get(i).getAddress();
            new AlertDialog.Builder(this).setTitle("Eşleştirilmiş HC-05'i seç")
                .setItems(names,(d,index)->{if(link!=null)link.connect(devices.get(index));})
                .setNeutralButton("Telefon Bluetooth ayarları",(d,w)->startActivity(new Intent(Settings.ACTION_BLUETOOTH_SETTINGS)))
                .setNegativeButton("Vazgeç",null).setMessage(devices.isEmpty()?"Önce telefon ayarlarında HC-05 ile eşleştir.":null).show();
        } catch(SecurityException e){notice("Yakındaki cihazlar izni gerekli.");}
    }
    @Override public void onRequestPermissionsResult(int code,String[] perms,int[] results){super.onRequestPermissionsResult(code,perms,results);if(code==52&&results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)chooseDevice();else if(code==52)notice("Bluetooth izni verilmedi; motor komutları kapalı.");}
    private void notice(String text){Toast.makeText(this,text,Toast.LENGTH_LONG).show();}
}
