package com.figbot.scanner.vision;

/** Short visual continuity only. Reading never renews the capture timestamp. */
public final class DisplayMemory<T> {
    private T value;
    private long captured;
    private int generation=-1;
    public synchronized void offer(T observation,long timestamp,int session) {
        if(session!=generation){clear();generation=session;}
        if(observation!=null && timestamp>captured){value=observation;captured=timestamp;}
    }
    public synchronized T get(long now,int session) {
        if(session!=generation || now<captured || now-captured>800_000_000L){clear();return null;}
        return value;
    }
    public synchronized void clear(){value=null;captured=0;}
}
