"""Finite scenario robustness; recalibrated budgets are distinct from committed budgets."""
from service_model import *

def main():
    ca,isos,paths=source_paths(); rows=[]; config=0
    pgrid=sorted(set(np.round(np.arange(.5,1.001,.05),2))|{.78})
    for risk,p,m,q,g in itertools.product(['fixed_WPP','damped_risk_WPP'],pgrid,[.5,.75,1,1.25],[.25,.5,.75],[.02,.03,.04,.05]):
        config+=1; ppath=np.linspace(p,min(1,p*m),len(YEARS)); n=paths[risk]*ppath/.78
        simulations={s:simulate(n,q,g,s)[0][-1] for s in STRATEGIES}
        min_gap=min(r['cumulative_shortfall'] for r in simulations.values())
        for e,d,(cs,(c1,c2)) in itertools.product([.25,.5,.75],[30,37.5,45],completion_scenarios().items()):
            sid=f'{config:04d}_{e}_{d}_{cs}'
            h=unit_hours(d,c1,c2)
            for s,r in simulations.items():
                rows.append(dict(scenario_id=sid,risk=risk,baseline_p=p,future_p_multiplier=m,future_p=min(1,p*m),
                    eligibility=e,target=q,duration=d,completion=cs,c1=c1,c2=c2,annual_growth=g,strategy=s,
                    weighted_coverage=r['weighted_coverage'],countries_below=r['countries_below'],
                    demand_share_below=r['demand_share_below'],shortfall=r['shortfall']*e,
                    cumulative_shortfall=r['cumulative_shortfall']*e,completed=r['offered']*e*c2,
                    used_hours=r['offered']*e*h,allocated_hours=r['capacity_equivalents']*e*h,
                    regret=max(0,(r['cumulative_shortfall']-min_gap)*e),
                    tied_minimum=r['cumulative_shortfall']<=min_gap+1e-6))
        if config%100==0: print('Scenario structures',config,flush=True)
    df=pd.DataFrame(rows); save(df,'robust_scenarios.csv.gz')
    summary=df.groupby('strategy',as_index=False).agg(scenarios=('scenario_id','size'),
        maximum_regret=('regret','max'),median_regret=('regret','median'),
        tied_minimum_count=('tied_minimum','sum'),coverage_min=('weighted_coverage','min'),coverage_max=('weighted_coverage','max'))
    save(summary,'robust_summary.csv')
    # Fixed reference budget exposes the effect of misspecified p, eligibility and time.
    fixed=[]; reference=paths['fixed_WPP'][:,0]*.25*unit_hours()
    tests=[('Reference',.78,.5,37.5,C1,C2)]
    tests += [(f'p={p}',p,.5,37.5,C1,C2) for p in [.5,1.]]
    tests += [(f'e={e}',.78,e,37.5,C1,C2) for e in [.25,.75]]
    tests += [(f'd={d}',.78,.5,d,C1,C2) for d in [30,45]]
    tests += [(f'completion={cs}',.78,.5,37.5,c1,c2) for cs,(c1,c2) in completion_scenarios().items() if cs!='Trial']
    for label,p,e,d,c1,c2 in tests:
        h=unit_hours(d,c1,c2); demand=paths['fixed_WPP']*(p/.78)*e
        for g,s in itertools.product([.02,.03,.04,.05],STRATEGIES):
            r=simulate(demand,.5,g,s,initial=reference/h)[0][-1]
            fixed.append(dict(stress=label,annual_growth=g,strategy=s,p=p,e=e,duration=d,c1=c1,c2=c2,
                weighted_coverage=r['weighted_coverage'],countries_below=r['countries_below'],
                cumulative_shortfall=r['cumulative_shortfall'],shortfall=r['shortfall'],
                allocated_hours=r['capacity_equivalents']*h,used_hours=r['offered']*h,completed=r['offered']*c2))
    save(pd.DataFrame(fixed),'committed_budget_stress.csv')
    log('robustness',dict(rows=len(df),configurations=config,summary=summary.to_dict('records')))
    print(summary.to_string(index=False))

if __name__=='__main__': main()
