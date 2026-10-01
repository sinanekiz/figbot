package com.figbot.scanner;

import android.app.Activity;
import android.view.View;
import android.view.accessibility.AccessibilityManager;
import android.widget.Button;
import android.widget.FrameLayout;
import androidx.core.view.*;

/** Camera-only UI chrome. Never sends a robot or calibration command. */
final class CameraControls {
    private final Activity activity;
    private final View root,panel;
    private final Button menu;
    private final Runnable hide=()->show(false);
    private android.window.OnBackInvokedCallback back;
    CameraControls(Activity a){
        activity=a;root=a.findViewById(R.id.kolRoot);panel=a.findViewById(R.id.controlsPanel);menu=a.findViewById(R.id.menuButton);
        WindowCompat.setDecorFitsSystemWindows(a.getWindow(),false);
        var bars=new WindowInsetsControllerCompat(a.getWindow(),root);
        bars.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
        bars.hide(WindowInsetsCompat.Type.systemBars());
        ViewCompat.setOnApplyWindowInsetsListener(root,(v,insets)->{
            var safe=insets.getInsets(WindowInsetsCompat.Type.systemBars()|WindowInsetsCompat.Type.displayCutout());
            v.setPadding(safe.left,safe.top,safe.right,safe.bottom);return insets;
        });
        root.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->{
            int width=Math.min(ControlUi.dp(a,320),Math.max(ControlUi.dp(a,200),r-l-root.getPaddingLeft()-root.getPaddingRight()-ControlUi.dp(a,24)));
            var params=(FrameLayout.LayoutParams)panel.getLayoutParams();
            if(params.width!=width){params.width=width;panel.setLayoutParams(params);}
        });
        menu.setOnClickListener(v->show(panel.getVisibility()!=View.VISIBLE));
        ViewCompat.requestApplyInsets(root);
    }
    void show(boolean visible){
        if(android.os.Build.VERSION.SDK_INT>=33){
            if(back!=null){activity.getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(back);back=null;}
            if(visible){back=()->show(false);activity.getOnBackInvokedDispatcher().registerOnBackInvokedCallback(android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT,back);}
        }
        panel.removeCallbacks(hide);panel.setVisibility(visible?View.VISIBLE:View.GONE);
        menu.setText(visible?"GİZLE":"MENÜ");menu.setContentDescription(visible?"Kontrol menüsünü gizle":"Kontrol menüsünü aç");
        ViewCompat.setStateDescription(menu,visible?"Açık":"Kapalı");
        if(visible)interacted();
    }
    boolean visible(){return panel.getVisibility()==View.VISIBLE;}
    void interacted(){
        panel.removeCallbacks(hide);
        var accessibility=(AccessibilityManager)activity.getSystemService(Activity.ACCESSIBILITY_SERVICE);
        if(visible()&&(accessibility==null||!accessibility.isTouchExplorationEnabled()))panel.postDelayed(hide,6000);
    }
    void dispose(){panel.removeCallbacks(hide);if(android.os.Build.VERSION.SDK_INT>=33&&back!=null)activity.getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(back);}
}
