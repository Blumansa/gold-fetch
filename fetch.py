import lzma,struct,json,time,zoneinfo,sys,requests
from datetime import datetime,timedelta,date,timezone
from concurrent.futures import ThreadPoolExecutor
paris=zoneinfo.ZoneInfo("Europe/Paris")
S=requests.Session()
def hour_ticks(h):
    u=f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{h.year}/{h.month-1:02d}/{h.day:02d}/{h.hour:02d}h_ticks.bi5"
    for a in range(8):
        try:
            r=S.get(u,timeout=30)
            if r.status_code==200: return r.content
            if r.status_code==404: return b""
        except Exception: pass
        time.sleep(2*(a+1))
    return None
def last_mid(t):
    hs=t.replace(minute=0,second=0,microsecond=0)
    for back in (0,1,2):
        h=hs-timedelta(hours=back); pl=hour_ticks(h)
        if pl is None: return "ERR"
        if not pl: continue
        raw=lzma.decompress(pl); best=None
        for i in range(0,len(raw),20):
            ms,ask,bid,_,_=struct.unpack(">IIIff",raw[i:i+20])
            if h+timedelta(milliseconds=ms)<=t: best=(ask+bid)/2000
        if best: return best
    return None
def day(d):
    r={}
    for k,(hh,mm) in {"a":(9,0),"b":(15,30),"c":(22,0)}.items():
        r[k]=last_mid(datetime(d.year,d.month,d.day,hh,mm,tzinfo=paris).astimezone(timezone.utc))
    return d.isoformat(),r
y0,y1=int(sys.argv[1]),int(sys.argv[2])
ds=[date(y0,1,1)+timedelta(days=i) for i in range((date(y1,12,31)-date(y0,1,1)).days+1)]
ds=[d for d in ds if d.weekday()<5]
with ThreadPoolExecutor(6) as ex: res=dict(ex.map(day,ds))
json.dump(res,open(f"gold_{y0}_{y1}.json","w"))
print(len(res),"jours;",sum(1 for v in res.values() if None in v.values() or "ERR" in v.values()),"incomplets")
