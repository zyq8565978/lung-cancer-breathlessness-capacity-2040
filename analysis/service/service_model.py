"""Expected activity accounting and equal-budget national capacity allocation."""
from common import *
import itertools

PAR=json.loads((ROOT/'data/service_parameters.json').read_text())
C1,C2=PAR['c1'],PAR['c2']
STRATEGIES=['Uniform','Demand-proportional','Minimum-coverage-focused']
YEARS=np.arange(2027,2041)

def wilson(k,n):
    z=1.959963984540054; p=k/n; den=1+z*z/n
    centre=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return centre-half,centre+half

def completion_scenarios():
    lo1,hi1=wilson(PAR['first'],PAR['assigned'])
    lo2,hi2=wilson(PAR['second'],PAR['first'])
    return {'Low':(lo1,lo1*lo2),'Trial':(C1,C2),'High':(hi1,hi1*hi2)}

def unit_hours(duration=37.5,c1=C1,c2=C2,doc=10,coord=15):
    return (c1+c2)*(duration+doc)/60+coord/60

def activity(offered,duration=37.5,c1=C1,c2=C2,doc=10,coord=15):
    first=offered*c1; second=offered*c2
    return dict(offered=offered,started=first,completed=second,first_contacts=first,
        second_contacts=second,contacts=first+second,direct_hours=(first+second)*duration/60,
        documentation_hours=(first+second)*doc/60,coordination_hours=offered*coord/60,
        specified_hours=offered*unit_hours(duration,c1,c2,doc,coord))

def weighted_add(amount,weights,caps,fallback):
    out=np.zeros(len(weights)); left=float(amount)
    for _ in range(len(weights)+2):
        room=np.maximum(0,caps-out); active=room>1e-9
        if left<1e-8 or not active.any(): break
        w=np.where(active,weights,0)
        if w.sum()==0: w=np.where(active,fallback,0)
        if w.sum()==0: w=active.astype(float)
        add=np.minimum(room,left*w/w.sum()); out+=add; left-=add.sum()
    assert left<1e-5,('Unallocated annual resource',left)
    return out

def equalise(amount,capacity,demand,target,caps):
    room=np.minimum(np.maximum(target*demand-capacity,0),caps)
    spend=min(float(amount),float(room.sum()))
    if spend<=1e-9: return np.zeros_like(capacity)
    if spend>=room.sum()-1e-9: return room
    lo=0.; hi=target
    for _ in range(42):
        mid=(lo+hi)/2
        add=np.minimum(np.maximum(mid*demand-capacity,0),room)
        if add.sum()<spend: lo=mid
        else: hi=mid
    add=np.minimum(np.maximum(hi*demand-capacity,0),room)
    return add*(spend/add.sum())

def simulate(demand,q,g,strategy,cap=None,initial=None):
    # Units here are expected offered-person equivalents; multiply by h for nursing hours.
    k=q*demand[:,0] if initial is None else initial.copy()
    start=k.sum(); summaries=[]; records=[]; cumulative=0.
    for j,year in enumerate(YEARS):
        d=demand[:,j]; inc=np.zeros(len(k))
        if j:
            budget=start*(1+g)**(j-1)*g
            caps=np.full(len(k),np.inf) if cap is None else cap*k
            if strategy=='Uniform': inc=budget*k/k.sum()
            elif strategy=='Demand-proportional':
                inc=weighted_add(budget,np.maximum(d-demand[:,j-1],0),caps,d)
            else:
                inc=equalise(budget,k,d,q,caps)
                left=budget-inc.sum()
                inc+=equalise(left,k+inc,d,1,caps-inc)
                left=budget-inc.sum()
                if left>1e-8: inc+=weighted_add(left,d,caps-inc,d)
            assert np.isclose(inc.sum(),budget,rtol=1e-10,atol=1e-6)
            if cap is not None: assert np.all(inc<=caps+1e-6)
            k+=inc
        offered=np.minimum(k,d)
        cov=np.divide(offered,d,out=np.full(len(d),np.nan),where=d>0)
        below=cov<q-1e-10; gap=np.maximum(q*d-offered,0)
        cumulative+=gap.sum()
        pooled=min(1,k.sum()/d.sum())
        summaries.append(dict(year=int(year),strategy=strategy,annual_growth=g,
            eligible=d.sum(),capacity_equivalents=k.sum(),offered=offered.sum(),
            weighted_coverage=offered.sum()/d.sum(),pooled_coverage=pooled,
            countries_below=int(below.sum()),demand_share_below=d[below].sum()/d.sum(),
            shortfall=gap.sum(),cumulative_shortfall=cumulative,
            minimum_coverage=float(np.nanmin(cov)),coverage_p05=float(np.nanquantile(cov,.05)),
            coverage_p25=float(np.nanquantile(cov,.25)),idle_equivalents=np.maximum(k-d,0).sum(),
            pooled_shortfall=max(0,q*d.sum()-k.sum()),new_capacity=inc.sum()))
        records.append(dict(year=int(year),capacity=k.copy(),offered=offered,coverage=cov,shortfall=gap,new_capacity=inc))
    return summaries,records

def source_paths():
    ca=legacy('country_paths.csv'); isos=sorted(ca.ISO3.unique()); out={}
    for s in ca.scenario.unique():
        if s=='historical_GHE_estimate': continue
        z=ca[(ca.year>=2027)&ca.scenario.eq(s)].pivot(index='ISO3',columns='year',values='symptom_people').reindex(isos)
        assert z.shape==(183,14) and z.notna().all().all()
        out[s]=z.to_numpy()
    return ca,isos,out

def planning(ca):
    rows=[]
    for s in ca.scenario.unique():
        if s=='historical_GHE_estimate': continue
        for start in [2023,2026,2027]:
            fut=ca[ca.scenario.eq(s)]
            base=ca[ca.year.eq(start)&(ca.scenario.eq(s) if start>2023 else True)].set_index('ISO3').symptom_people
            groups=list(fut.groupby('ISO3'))+[('ALL_183',fut.groupby('year',as_index=False).symptom_people.sum())]
            for iso,z in groups:
                z=z[z.year>start].sort_values('year'); n0=base.sum() if iso=='ALL_183' else base[iso]
                if n0<=0:
                    rows.append(dict(ISO3=iso,scenario=s,start=start,status='Zero baseline; proportional expansion undefined'))
                    continue
                roots=(z.symptom_people.to_numpy()/n0)**(1/(z.year.to_numpy()-start))-1
                rows.append(dict(ISO3=iso,scenario=s,start=start,baseline_people=n0,
                    endpoint_people=float(z.symptom_people.iloc[-1]),g_endpoint=float(roots[-1]),
                    g_path=float(roots.max()),binding_year=int(z.year.iloc[int(np.argmax(roots))]),status='Positive baseline'))
    df=pd.DataFrame(rows); save(df,'planning_rates.csv'); return df

def delivery(paths):
    totals=legacy('scope_totals.csv'); rows=[]; units=[]
    for r in totals[totals.scope.eq('183_countries')&totals.year.isin([2023,2027,2040])].itertuples():
        for e,q,d,(cs,(c1,c2)) in itertools.product([.25,.5,.75,1],[.25,.5,.75,1],[30,37.5,45],completion_scenarios().items()):
            rows.append(dict(year=r.year,scenario=r.scenario,symptom_people=r.symptom_people,
                eligible=r.symptom_people*e,e=e,q=q,duration=d,completion_scenario=cs,c1=c1,c2=c2,
                **activity(r.symptom_people*e*q,d,c1,c2)))
    funnel=pd.DataFrame(rows); save(funnel,'delivery_funnel.csv')
    for d,(cs,(c1,c2)),doc,coord in itertools.product([30,37.5,45],completion_scenarios().items(),[10,20],[0,15,30]):
        h=unit_hours(d,c1,c2,doc,coord)
        for denom,offered in [('1000 symptomatic',250),('1000 offered',1000),('1000 started',1000/c1),('1000 completed',1000/c2),('1000 specified hours',1000/h)]:
            units.append(dict(denominator=denom,duration=d,completion_scenario=cs,
                documentation_minutes=doc,coordination_minutes=coord,**activity(offered,d,c1,c2,doc,coord)))
    u=pd.DataFrame(units); save(u,'resources_per_1000.csv')
    bounds=[]
    for count in [max(0,PAR['first']+PAR['second']-PAR['assigned']),PAR['second']]:
        bounds.append(dict(joint_complete_count=count,assigned=PAR['assigned'],joint_completion=count/PAR['assigned'],
            contact_count_per_assigned=C1+C2,hours_per_1000_completed=1000*unit_hours()/(count/PAR['assigned']),
            interpretation='Attendance overlap bound; same observed marginal contacts and hours'))
    save(pd.DataFrame(bounds),'joint_completion_bounds.csv')
    return funnel,u

def main():
    ca,isos,paths=source_paths(); planning(ca); delivery(paths)
    annual=[]; country=[]; h=unit_hours()
    for risk,n in paths.items():
        for g,strategy,cap in itertools.product([.02,.03,.04,.05],STRATEGIES,[None,.20]):
            a,r=simulate(n*.5,.5,g,strategy,cap)
            for row in a:
                row.update(risk=risk,local_cap='Unconstrained new capacity' if cap is None else '20% annual local cap',
                    allocated_hours=row['capacity_equivalents']*h,used_hours=row['offered']*h,
                    completed=row['offered']*C2,started=row['offered']*C1,
                    completed_per_used_hour=C2/h,completed_per_allocated_hour=row['offered']*C2/(row['capacity_equivalents']*h))
                annual.append(row)
            for rec in r:
                country.append(pd.DataFrame(dict(ISO3=isos,year=rec['year'],risk=risk,annual_growth=g,strategy=strategy,
                    local_cap='Unconstrained new capacity' if cap is None else '20% annual local cap',
                    eligible=n[:,rec['year']-2027]*.5,capacity_hours=rec['capacity']*h,
                    new_hours=rec['new_capacity']*h,offered=rec['offered'],coverage=rec['coverage'],
                    completed=rec['offered']*C2,shortfall=rec['shortfall'])))
    annual=pd.DataFrame(annual); save(annual,'allocation_annual.csv')
    save(pd.concat(country,ignore_index=True),'allocation_country.csv.gz')
    save(annual[annual.year.eq(2040)],'allocation_endpoint.csv')
    log('service_and_allocation','Reference and 20% local build-rate stress completed with equal budgets')
    print(read('planning_rates.csv').query("ISO3 == 'ALL_183' and start == 2027").to_string(index=False))
    print(annual.query("year==2040 and risk=='fixed_WPP' and annual_growth==0.03 and local_cap=='Unconstrained new capacity'").to_string(index=False))

if __name__=='__main__': main()
