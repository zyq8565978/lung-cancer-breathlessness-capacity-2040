"""Service target and shortfall definitions."""
from common import *

def main():
    par=json.loads((ROOT/'data/service_parameters.json').read_text())
    c1=par['first']/par['assigned']; c2=par['second']/par['assigned']
    lower=max(0,par['first']+par['second']-par['assigned'])/par['assigned']
    h=(c1+c2)*(par['duration_mid']+par['documentation_minutes'])/60+par['coordination_minutes']/60
    par.update(q_offer=par['target'],c12_proxy=c2,c12_lower=lower,c12_upper=c2,
               h_hours_per_offered=h,second_conditional_sequential=c2/c1)
    (ROOT/'results/final_parameters.json').write_text(json.dumps(par,indent=2),encoding='utf-8')
    ledger=[
        ['N','Any-breathlessness annual death-cohort population','People','D multiplied by external symptom reference p','WHO GHE680; C33-C34; age 30+','Health estimate plus external parameter'],
        ['E','Population applicable to the service','People','N multiplied by e','e=0.50 reference; 0.25/0.50/0.75 scenarios','Planning assumption'],
        ['q_offer','Target fraction eligible to be offered a service opportunity','Eligible people','0.50 reference','Opportunity, not course completion','Planning assumption'],
        ['O','Capacity-constrained offered population','People','min(E,K/h)','K is national annual specified-hour capacity','Model-derived'],
        ['c1','First-contact completion proportion','126 assigned intervention participants',c1,'106/126; Greer intervention delivery','Trial aggregate'],
        ['c2','Second-contact completion proportion','126 assigned intervention participants',c2,'93/126; do not multiply by c1 again','Trial aggregate'],
        ['c12','Both-contact completion fraction','126 assigned intervention participants',c2,'Second contact is sequential-course proxy; joint attendance not directly verified','Operational proxy'],
        ['c12 lower','Minimum joint attendance from margins alone','126 assigned intervention participants',lower,'(106+93-126)/126; does not change contacts','Logical bound'],
        ['c12 upper','Maximum joint attendance from margins alone','126 assigned intervention participants',c2,'min(106,93)/126; does not change contacts','Logical bound'],
        ['Second conditional','Second contact conditional on first in sequential interpretation','106 first-contact participants',c2/c1,'93/106 only under sequential attendance interpretation','Conditional interpretation'],
        ['d','Minutes per delivered contact','Each first or second contact',par['duration_mid'],'30/37.5/45 minutes; midpoint is a scenario','Reported range with assumed midpoint'],
        ['Documentation','Minutes of documentation','Each delivered contact',par['documentation_minutes'],'10 reference; 20 sensitivity; trial did not time this activity','Planning assumption'],
        ['Coordination','Minutes of coordination','Every offered person, including nonstarters',par['coordination_minutes'],'0/15/30 scenarios; no observed mean available','Planning assumption'],
        ['h','Specified hours per offered person','One offered person',h,'(c1+c2)*(d+documentation)/60+coordination/60','Derived resource coefficient'],
        ['K','Annual installed national service capacity','Specified activity hours','Persistent national capacity; annual new increments','No relocation of already installed national capacity','Planning assumption'],
        ['L_country','Nationally constrained opportunity target shortfall','Planned service opportunities','Sum positive parts of q_offer*E-O','Annual death cohorts; cumulative sum is not a waiting list','Model-derived'],
        ['L_pooled','Aggregate capacity shortfall lower bound','Planned service opportunities','max(0,q_offer*sum(E)-sum(K)/h)','Theoretical pooled bound, not an implementable international transfer','Model-derived theoretical benchmark'],
        ['L_distribution','Additional distribution-related shortfall','Planned service opportunities','L_country-L_pooled','Conditional decomposition of existing allocation results','Descriptive derivative'],
    ]
    parameters=pd.DataFrame(ledger,columns=['Symbol','Definition','Denominator_or_unit','Value_or_formula','Interpretation','Evidence_type'])
    save(parameters,'parameter_estimand_ledger.csv')

    funnel=service('delivery_funnel.csv')
    f=funnel[funnel.scenario.eq('fixed_WPP')&funnel.e.eq(.5)&funnel.q.eq(.5)&funnel.duration.eq(37.5)&funnel.completion_scenario.eq('Trial')].copy()
    f=f.sort_values('year').rename(columns={'q':'q_offer','completed':'course_proxy_completed'})
    f['c12_proxy']=c2
    save(f,'reference_service_funnel.csv')
    targets=[]
    for row in f.itertuples():
        for label,c12 in [('Sequential proxy',c2),('Joint lower bound',lower)]:
            for q in [.25,.5,.75,1.]:
                targets.append(dict(year=row.year,interpretation=label,target_type='Opportunity coverage',target_fraction=q,
                    required_q_offer=q,eligible=row.eligible,required_offered_people=row.eligible*q,
                    specified_hours=row.eligible*q*h,started_coverage=q*c1,second_contact_coverage=q*c2,
                    joint_completion_coverage=q*c12,feasible=True,maximum_joint_coverage=c12))
            for target in [.25,.5,.75]:
                needed=target/c12
                targets.append(dict(year=row.year,interpretation=label,target_type='Joint completion coverage',target_fraction=target,
                    required_q_offer=needed,eligible=row.eligible,required_offered_people=row.eligible*needed,
                    specified_hours=row.eligible*needed*h,started_coverage=needed*c1,second_contact_coverage=needed*c2,
                    joint_completion_coverage=target,feasible=needed<=1,maximum_joint_coverage=c12))
    target=pd.DataFrame(targets)
    target['requirement_status']=np.where(target.feasible,'Feasible conditional requirement','Infeasible: opportunity requirement exceeds 100%; counts and hours are algebraic requirements, not delivered outputs')
    save(target,'coverage_target_conversion.csv')
    bounds=service('joint_completion_bounds.csv').copy()
    bounds['first_contacts_per_1000_offered']=c1*1000
    bounds['second_contacts_per_1000_offered']=c2*1000
    bounds['specified_hours_per_1000_offered']=h*1000
    save(bounds,'joint_completion_bound.csv')

    ann=service('allocation_annual.csv').rename(columns={'shortfall':'L_country','pooled_shortfall':'L_pooled','completed':'course_proxy_completed'})
    ann['q_offer']=par['q_offer']; ann['target_people']=ann.q_offer*ann.eligible
    residual=ann.L_country-ann.L_pooled
    assert residual.min()>-1e-6
    ann['L_distribution']=residual.clip(lower=0)
    keys=['risk','local_cap','strategy','annual_growth']
    ann=ann.sort_values(keys+['year'])
    group=ann.groupby(keys,sort=False)
    ann['cum_L_pooled']=group.L_pooled.cumsum()
    ann['cum_L_distribution']=group.L_distribution.cumsum()
    ann['cum_target_people']=group.target_people.cumsum()
    ann['L_country_pct_target']=100*ann.L_country/ann.target_people
    ann['L_pooled_pct_target']=100*ann.L_pooled/ann.target_people
    ann['L_distribution_pct_target']=100*ann.L_distribution/ann.target_people
    ann['cum_L_country_pct_target']=100*ann.cumulative_shortfall/ann.cum_target_people
    ann['cum_L_pooled_pct_target']=100*ann.cum_L_pooled/ann.cum_target_people
    ann['cum_L_distribution_pct_target']=100*ann.cum_L_distribution/ann.cum_target_people
    save(ann,'shortfall_decomposition_all_annual.csv')
    end=ann[ann.year.eq(2040)].copy()
    save(end,'shortfall_decomposition_all_endpoint.csv')
    main=ann[ann.risk.eq('fixed_WPP')&ann.local_cap.eq('Unconstrained new capacity')&ann.annual_growth.isin([.02,.03])].copy()
    save(main,'main_allocation_annual.csv'); save(main[main.year.eq(2040)],'main_allocation_endpoint.csv')
    full_country=OUTPUT/'service/results/allocation_country.csv.gz'
    country=service('allocation_country.csv.gz') if full_country.exists() else result('main_country_allocation.csv.gz')
    selected=country[country.risk.eq('fixed_WPP')&country.local_cap.eq('Unconstrained new capacity')&country.annual_growth.isin([.02,.03])]
    save(selected,'main_country_allocation.csv.gz')
    ecdf=[]
    for (g,s),z in selected[selected.year.eq(2040)].groupby(['annual_growth','strategy']):
        z=z.sort_values(['coverage','ISO3']).copy(); z['ecdf_pct']=np.arange(1,len(z)+1)/len(z)*100
        ecdf.append(z[['ISO3','annual_growth','strategy','coverage','ecdf_pct']])
    save(pd.concat(ecdf,ignore_index=True),'figure2_country_coverage_ecdf.csv')
    endpoint=main[main.year.eq(2040)].set_index(['annual_growth','strategy'])
    contrasts=[]
    for g in [.02,.03]:
        u=endpoint.loc[(g,'Uniform')]
        for s in STRATEGIES[1:]:
            a=endpoint.loc[(g,s)]
            contrasts.append(dict(annual_growth=g,strategy=s,reference='Uniform',
                endpoint_shortfall_reduction=u.L_country-a.L_country,
                endpoint_distribution_reduction=u.L_distribution-a.L_distribution,
                cumulative_shortfall_reduction=u.cumulative_shortfall-a.cumulative_shortfall,
                country_count_difference=int(a.countries_below-u.countries_below),
                mean_coverage_difference=a.weighted_coverage-u.weighted_coverage,
                course_completion_difference=a.course_proxy_completed-u.course_proxy_completed))
    save(pd.DataFrame(contrasts),'allocation_strategy_contrasts.csv')

    capacities=[]
    for row in f[f.year.isin([2027,2040])].itertuples():
        capacities.append(dict(year=row.year,basis='Exactly meeting 50% opportunity target',eligible=row.eligible,
            offered_people=row.offered,specified_hours=row.specified_hours,course_proxy_completed=row.course_proxy_completed))
    for row in main[(main.year.eq(2040))&main.annual_growth.eq(.03)].itertuples():
        capacities.append(dict(year=row.year,basis='Installed capacity after 3% expansion: '+row.strategy,eligible=row.eligible,
            offered_people=row.offered,specified_hours=row.allocated_hours,course_proxy_completed=row.course_proxy_completed))
    capdf=pd.DataFrame(capacities); save(capdf,'target_hours_versus_installed_capacity.csv')


if __name__=='__main__': main()
