import lzma,struct,sys,time,requests,pandas as pd
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
S=requests.Session()
def get(h):
    u=f"https://datafeed.dukascopy.com/datafeed/{SYM}/{h.year}/{h.month-1:02d}/{h.day:02d}/{h.hour:02d}h_ticks.bi5"
    for a in range(8):
        try:
            r=S.get(u,timeout=30)
            if r.status_code==200: return r.content
            if r.status_code==404: return b""
        except Exception: pass
        time.sleep(2*(a+1))
    return None
def hour(h):
    pl=get(h)
    if pl is None: return ("ERR",h)
    if not pl: return None
    raw=lzma.decompress(pl); n=len(raw)//20
    if n==0: return None
    a=[struct.unpack(">IIIff",raw[i*20:i*20+20]) for i in range(n)]
    df=pd.DataFrame(a,columns=["ms","ask","bid","av","bv"])
    DIV=1000.0 if (SYM.endswith("JPY") or SYM=="XAUUSD") else 100000.0
    df["m"]=(df.ask+df.bid)/2/DIV; df["sp"]=(df.ask-df.bid)/DIV
    df["t"]=pd.Timestamp(h)+pd.to_timedelta(df.ms,unit="ms")
    g=df.groupby(df.t.dt.floor("min"))
    o=pd.DataFrame({"o":g.m.first(),"h":g.m.max(),"l":g.m.min(),"c":g.m.last(),"n":g.m.count(),"sp":g.sp.mean()})
    return o
SYM=sys.argv[1]; y=int(sys.argv[2]); half=int(sys.argv[3])
hs=[datetime(y,1,1,tzinfo=timezone.utc)+timedelta(hours=i) for i in range(24*366)]
hs=[h for h in hs if h.year==y and (h.weekday()<5 or (h.weekday()==6 and h.hour>=21))]
hs=[h for h in hs if (h.month<=6)==(half==1)]
with ThreadPoolExecutor(12) as ex: res=list(ex.map(hour,hs))
err=[r[1] for r in res if isinstance(r,tuple)]
d=pd.concat([r for r in res if isinstance(r,pd.DataFrame)]).sort_index()
d.index=pd.DatetimeIndex(d.index)
if d.index.tz is None: d.index=d.index.tz_localize("UTC")
else: d.index=d.index.tz_convert("UTC")
d.to_parquet(f"m1_{SYM}_{y}_{half}.parquet")
print(y,len(d),"minutes;",len(err),"heures en erreur")
