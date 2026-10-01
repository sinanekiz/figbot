package com.figbot.scanner;

import java.util.ArrayDeque;

/** Bounded/coalesced queue: stop flushes pending moves; explicit enable rearms. */
public final class MotionQueue {
    public record Command(int channel, Integer angle, int speed, boolean wide, boolean enable, int pairMin) {}
    private final ArrayDeque<Command> queue=new ArrayDeque<>();
    private boolean blocked=true, stop;
    public synchronized void clear() {queue.clear();blocked=true;stop=false;}
    public synchronized void stop() {queue.clear();blocked=true;stop=true;}
    /** Prepare every logical joint once per fresh, validated connection; no positions. */
    public synchronized void prepareSession() {
        if(stop)return;
        for(int ch:new int[]{0,1,3,4,5,6,7,9,10,11})arm(ch,true);
    }
    public synchronized void arm(int ch,boolean on) {
        if(stop)return;
        queue.removeIf(c->c.channel()==ch);
        if(on)blocked=false;
        queue.add(new Command(ch,null,0,false,on,1000));
    }
    public synchronized void move(int ch,int angle,int speed,boolean wide) {
        move(ch,angle,speed,wide,1000);
    }
    public synchronized void move(int ch,int angle,int speed,boolean wide,int pairMin) {
        if(blocked||stop)return;
        queue.removeIf(c->c.channel()==ch && c.angle()!=null);
        if(queue.size()<24)queue.add(new Command(ch,angle,speed,wide,true,pairMin));
    }
    public synchronized boolean takeStop() {boolean s=stop;stop=false;return s;}
    public synchronized Command next() {return queue.poll();}
    public synchronized int size() {return queue.size();}
}
