package com.figbot.scanner;

import android.app.Activity;
import android.graphics.Color;
import android.view.View;
import android.widget.*;

/** Shared native layout primitives; no additional network or UI dependencies. */
final class ControlUi {
    static final int INK=Color.rgb(23,48,45), BG=Color.rgb(241,246,241);
    static int dp(Activity a,int v){return (int)(v*a.getResources().getDisplayMetrics().density+.5f);}
    static LinearLayout column(Activity a) {
        LinearLayout l=new LinearLayout(a);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(a,18),dp(a,12),dp(a,18),dp(a,12));l.setBackgroundColor(BG);return l;
    }
    static TextView text(Activity a,LinearLayout p,String s,int sp) {
        TextView t=new TextView(a);t.setText(s);t.setTextSize(sp);t.setTextColor(INK);t.setPadding(0,dp(a,6),0,dp(a,6));p.addView(t);return t;
    }
    static Button button(Activity a,LinearLayout p,String s,View.OnClickListener action) {
        Button b=new Button(a);b.setText(s);b.setAllCaps(false);b.setMinHeight(dp(a,48));b.setOnClickListener(action);p.addView(b,new LinearLayout.LayoutParams(-1,-2));return b;
    }
    static void scroll(Activity a,LinearLayout content) {ScrollView s=new ScrollView(a);s.setFillViewport(true);s.addView(content);a.setContentView(s);}
    static void insets(Activity a,View root) {
        root.setOnApplyWindowInsetsListener((v,i)->{v.setPadding(v.getPaddingLeft(),i.getSystemWindowInsetTop()+dp(a,12),v.getPaddingRight(),i.getSystemWindowInsetBottom()+dp(a,12));return i;});
        root.requestApplyInsets();
    }
}
