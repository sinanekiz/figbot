package com.figbot.scanner;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.LinearLayout;

/** Separate direct USB, legacy Bluetooth, and PC bridge workflows. */
public final class HomeActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout p=ControlUi.column(this);ControlUi.scroll(this,p);ControlUi.insets(this,p);
        ControlUi.text(this,p,"FIGBOT",32);
        ControlUi.text(this,p,"Telefon: kamera, hedef seçimi ve kol kontrolü\nSO-101: USB üzerinden altı motor",17);
        ControlUi.text(this,p,"01  ·  Kamerayla toplama testi",23);
        ControlUi.text(this,p,"Kamera inciri görür, kol kayıtlı başlangıçtan hedefe gider. Önizle, hız seç (Yavaş/Orta/Hızlı), Hedefe git, sapmayı ölç.",16);
        ControlUi.button(this,p,"Kamerayla toplama ekranını aç",v->startActivity(new Intent(this,MainActivity.class)));
        ControlUi.text(this,p,"02  ·  Eski Arduino motor testleri",23);
        ControlUi.text(this,p,"HC-05 ile bağlan. İki kolun eklemlerini açı ve hız barlarıyla dene. Karşılıklı omuz motorları tek eklem olarak birlikte sürülür.",16);
        ControlUi.button(this,p,"Bluetooth ve motor testleri",v->startActivity(new Intent(this,MotorTestActivity.class)));
        ControlUi.text(this,p,"03  ·  PC üzerinden toplama",23);
        ControlUi.text(this,p,"Telefonu ve motor kartını ayrı USB kablolarıyla PC'ye bağla. PC'de PC_Uzerinden_Toplama.cmd dosyasını aç; sonra burada PC'ye bağlan. Hedef testi aynı şekilde çalışır.",16);
        ControlUi.button(this,p,"PC üzerinden toplama ekranını aç",v->startActivity(new Intent(this,MainActivity.class).putExtra("pc_bridge",true)));
        ControlUi.text(this,p,"İlk bağlantı hareket başlatmaz. Ekrandan ayrılınca bağlantı kapanır; kolun düşmemesi için mekanik destek gerekir.",14);
        ControlUi.text(this,p,"v0.16 · Hedef testi · Yavaş/Orta/Hızlı",13);
    }
}
