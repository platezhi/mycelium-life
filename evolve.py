import json, math, random, datetime, pathlib
P=pathlib.Path(__file__).with_name('state.json')
NOW=datetime.datetime.now(datetime.timezone.utc)
SEED=271828
LIMIT=500

def init():
    r=random.Random(SEED)
    return {'version':1,'day':0.0,'updated':NOW.isoformat(),'born':0,'dead':0,'next_id':101,'cells':[{'id':i+1,'x':r.uniform(30,730),'y':r.uniform(30,470),'age':r.uniform(0,0.5),'energy':1.0,'progress':0.0,'generation':1,'dna':[r.uniform(-0.5,0.5) for _ in range(6)],'signal':0} for i in range(100)]}

def tick(s,dt,r):
    cells=s['cells']; new=[]; alive=[]
    # Local neighbors are sampled from a 40px neighborhood; no central commands.
    grid={}
    for c in cells:grid.setdefault((int(c['x']//40),int(c['y']//40)),[]).append(c)
    for c in cells:
        gx,gy=int(c['x']//40),int(c['y']//40)
        near=[b for ix in (gx-1,gx,gx+1) for iy in (gy-1,gy,gy+1) for b in grid.get((ix,iy),[]) if b['id']!=c['id'] and (b['x']-c['x'])**2+(b['y']-c['y'])**2<1600]
        signal=sum(b['signal'] for b in near)/len(near) if near else 0
        local=max(0.15,min(1.15,0.6+0.4*math.sin(c['x']*0.018+c['y']*0.011+s['day']*0.2)))
        # 200% energy supplied by default, configurable in config.json.
        supply=s['supply_percent']/100
        gain=supply*local*0.10*dt
        cost=(0.10+0.006*len(near))*dt
        delta=gain-cost
        c['energy']=max(0,min(5,c['energy']+delta));c['age']+=dt
        d=c['dna'];z=d[0]*(c['energy']-1)+d[1]*signal+d[2]*len(near)/10+d[3]
        c['signal']=1 if z>0.12 else -1 if z< -0.12 else 0
        # Simple digital hereditary learning (not biological DNA).
        if delta>0:d[0]=min(0.95,d[0]+0.001*dt)
        if delta<0:d[1]=max(-0.95,d[1]-0.001*dt)
        c['progress']+=dt*supply*local*(0.8+0.2*d[4])
        if c['progress']>=14 and c['energy']>0.35 and len(cells)+len(new)<LIMIT:
            c['progress']-=14;c['energy']/=2
            child={**c,'id':s['next_id'],'x':max(8,min(752,c['x']+r.uniform(-10,10))),'y':max(8,min(512,c['y']+r.uniform(-10,10))),'age':0,'progress':0,'generation':c['generation']+1,'dna':[max(-0.95,min(0.95,v+r.uniform(-0.07,0.07))) for v in d]}
            s['next_id']+=1;new.append(child);s['born']+=1
        if c['age']>=7 or c['energy']<=0:
            s['dead']+=1;continue
        c['x']=max(8,min(752,c['x']+r.uniform(-1,1)*dt*6));c['y']=max(8,min(512,c['y']+r.uniform(-1,1)*dt*6))
        alive.append(c)
    s['cells']=alive+new;s['day']+=dt

def main():
    s=json.loads(P.read_text()) if P.exists() else init()
    config=json.loads(pathlib.Path(__file__).with_name('config.json').read_text())
    s['supply_percent']=config['supply_percent']
    try: prev=datetime.datetime.fromisoformat(s['updated'])
    except ValueError:prev=NOW
    elapsed=max(0,(NOW-prev).total_seconds()/600) # 10 real minutes = 1 simulated day; 7 days = 70 minutes
    r=random.Random()
    # Time advances from wall-clock elapsed time, even if Actions runs late.
    remaining=elapsed
    while remaining>0.000001 and s['cells']:
        dt=min(0.1,remaining);tick(s,dt,r);remaining-=dt
    if not s['cells']:s['day']+=remaining
    s['updated']=NOW.isoformat()
    P.write_text(json.dumps(s,ensure_ascii=False,separators=(',',':'))+'\n')
    print(f"day={s['day']:.3f} cells={len(s['cells'])} born={s['born']} dead={s['dead']}")
if __name__=='__main__':main()
