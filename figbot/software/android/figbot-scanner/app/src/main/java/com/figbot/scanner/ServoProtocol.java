package com.figbot.scanner;

/** Pure command protocol, never physical position feedback. Used by the HC-05 link. */
public final class ServoProtocol {
    public static final int MAX_COMMAND_SPEED = 360;
    public static final int DEFAULT_COMMAND_SPEED = MAX_COMMAND_SPEED;
    public static final int DEFAULT_PAIR_MIN_US = 500;
    public static final boolean DEFAULT_WIDE_RANGE = true;
    public boolean ready;
    public int enabled, active;
    public final int[] angle = new int[12];
    public final boolean[] acknowledged = new boolean[12];
    public static boolean paired(int ch) { return ch == 1 || ch == 7; }
    public static int mask(int ch) { return paired(ch) ? 3 << ch : 1 << ch; }
    public void reset() {
        ready=false; enabled=active=0;
        java.util.Arrays.fill(acknowledged,false);
    }
    private void channel(int ch) {
        if(ch<0 || ch>=12 || ch==2 || ch==8) throw new IllegalArgumentException("Omuz çifti ortak sürülür.");
        if(!ready) throw new IllegalStateException("UNO V5 yanıtı bekleniyor.");
    }
    public String arm(int ch, boolean on) { channel(ch); return (on?"E":"D")+ch+"\n"; }
    public String position(int ch,int degrees,int speed,boolean wide) {
        return position(ch,degrees,speed,wide,1000);
    }
    public String position(int ch,int degrees,int speed,boolean wide,int pairMin) {
        channel(ch);
        if ((enabled & mask(ch))!=mask(ch)) throw new IllegalStateException("Önce eklemi etkinleştir.");
        if(degrees<0 || degrees>180 || speed<10 || speed>MAX_COMMAND_SPEED) throw new IllegalArgumentException("Açı0–180; hız10–360.");
        if(paired(ch)) {
            if(pairMin<500 || pairMin>1000 || pairMin%100!=0) throw new IllegalArgumentException("Geçersiz omuz aralığı.");
            if(wide) throw new IllegalArgumentException("Omuz geniş aralık kullanamaz.");
            if((active & mask(ch))!=mask(ch) && degrees!=90) throw new IllegalStateException("Önce90° merkezle.");
            return "S"+ch+","+degrees+","+speed+","+pairMin+","+(3000-pairMin)+"\n";
        }
        return "P"+ch+","+degrees+","+speed+","+(wide?"500,2500":"1000,2000")+"\n";
    }
    private static int[] numbers(String s,int count) {
        String[] fields=s.split(",",-1);
        if(fields.length!=count) throw new IllegalArgumentException("Geçersiz UNO yanıtı.");
        int[] values=new int[count];
        for(int i=0;i<count;i++) {
            if(!fields[i].matches("[0-9]{1,5}")) throw new IllegalArgumentException("Geçersiz UNO sayısı.");
            values[i]=Integer.parseInt(fields[i]);
        }
        return values;
    }
    /** Returns true only for recognized, validated traffic. */
    public boolean receive(String line) {
        if(line.equals("FIGBOT_PCA9685_V5")) {reset();return true;}
        if(line.startsWith("STATUS5 ")) {
            int[] v=numbers(line.substring(8),2);
            if(v[0]>=4096 || v[1]>=4096 || (v[1]&~v[0])!=0) throw new IllegalArgumentException("Geçersiz kanal maskesi.");
            for(int c:new int[]{1,7}) for(int m:v)
                if(((m>>c)&3)!=0 && ((m>>c)&3)!=3) throw new IllegalArgumentException("Omuz eşlemesi hatalı.");
            enabled=v[0];active=v[1];ready=true;return true;
        }
        if(line.startsWith("PAIR ")) {
            int[] v=numbers(line.substring(5),5);
            if(!paired(v[0]) || v[1]>180 || v[2]<10 || v[2]>MAX_COMMAND_SPEED || v[3]<500 || v[3]>1000 || v[3]%100!=0 || v[4]!=3000-v[3]) throw new IllegalArgumentException("Geçersiz omuz onayı.");
            angle[v[0]]=v[1];angle[v[0]+1]=180-v[1];acknowledged[v[0]]=acknowledged[v[0]+1]=true;return true;
        }
        if(line.startsWith("ACK ")) {
            int[] v=numbers(line.substring(4),5);
            if(v[0]>=12 || paired(v[0]) || v[0]==2 || v[0]==8 || v[1]>180 || v[2]<10 || v[2]>MAX_COMMAND_SPEED
                || !((v[3]==1000&&v[4]==2000)||(v[3]==500&&v[4]==2500))) throw new IllegalArgumentException("Geçersiz hedef onayı.");
            angle[v[0]]=v[1];acknowledged[v[0]]=true;return true;
        }
        if(line.startsWith("OFF ")) {enabled=active=0;return true;}
        if(line.startsWith("ERR ")) throw new IllegalStateException(line);
        if(line.startsWith("FIGBOT_PCA9685_") || line.startsWith("STATUS")) throw new IllegalStateException("UNO Bluetooth V5 firmware gerekli.");
        return false;
    }
}
