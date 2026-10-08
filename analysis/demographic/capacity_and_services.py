"""Whole-path capacity, non-transferable national capacity and planned activities."""
from common import ROOT, P, log
import itertools
import numpy as np
import pandas as pd


def capacity_rates(baseline, years, values):
    years = np.asarray(years, dtype=int)
    values = np.asarray(values, dtype=float)
    if baseline == 0:
        return dict(g_endpoint=np.nan, g_path=np.nan, binding_year=np.nan,
                    min_coverage_at_endpoint_rate=np.nan, g_nonnegative_path=np.nan,
                    status='No finite proportional expansion from zero' if np.any(values>0) else 'Zero demand; not applicable')
    roots = (values/baseline)**(1/(years-2023))-1
    end = float(roots[years==2040][0])
    path = float(roots.max())
    binding = int(years[np.flatnonzero(np.isclose(roots,path,rtol=0,atol=1e-12))[0]])
    capacity = .5*baseline*(1+end)**(years-2023)
    q = np.divide(capacity, values, out=np.full(len(values),np.nan), where=values>0)
    return dict(g_endpoint=end, g_path=path, binding_year=binding,
                min_coverage_at_endpoint_rate=float(np.nanmin(np.minimum(1,q))),
                g_nonnegative_path=max(0,path), status='Positive baseline')


def coverage_values(baseline, future, g, years):
    future = np.asarray(future, dtype=float)
    k = .5*np.asarray(baseline)*(1+g)**(np.asarray(years)-2023)
    used = np.minimum(k, future)
    q = np.divide(used, future, out=np.full(future.shape,np.nan), where=future>0)
    return k, used, q


def activities(n, e, q, visits, phone=np.nan, doc=np.nan, coord=np.nan):
    served = n*e*q
    return dict(symptom_people=n, e=e, q=q, effective_receipt=e*q, sessions=visits,
                service_recipients=served, face_contacts=served*visits, phone_contacts=served,
                face_hours=served*visits, phone_minutes=phone, phone_hours=served*phone/60,
                documentation_minutes_per_contact=doc, documentation_hours=served*(visits+1)*doc/60,
                coordination_minutes_per_course=coord, coordination_hours=served*coord/60,
                enumerated_hours=served*(visits+phone/60+(visits+1)*doc/60+coord/60),
                total_all_nursing_hours=np.nan, actual_FTE=np.nan,
                eligibility_role='Maximum applicability only' if e==1 else 'Planning scenario')


def main():
    ca = pd.read_csv(ROOT/'results/country_paths.csv')
    baseline = ca[ca.year.eq(2023)].set_index('ISO3').symptom_people
    fut = ca[ca.year.gt(2023)].copy()
    rate_rows = []
    for (iso, scenario), z in fut.groupby(['ISO3','scenario']):
        z = z.sort_values('year')
        r = capacity_rates(baseline[iso],z.year,z.symptom_people)
        rate_rows.append(dict(ISO3=iso,country=z.country.iloc[0],scenario=scenario,
                              baseline_people=baseline[iso],endpoint_people=z.symptom_people.iloc[-1],**r))
    rates = pd.DataFrame(rate_rows)
    rates['path_minus_endpoint_pp'] = 100*(rates.g_path-rates.g_endpoint)
    rates.to_csv(ROOT/'results/country_capacity_requirements.csv', index=False)
    tot = pd.read_csv(ROOT/'results/scope_totals.csv')
    ag = []
    for (scope, scenario), z in tot[tot.year.gt(2023)].groupby(['scope','scenario']):
        n0 = tot[tot.scope.eq(scope)&tot.year.eq(2023)].symptom_people.iloc[0]
        z = z.sort_values('year')
        ag.append(dict(scope=scope,scenario=scenario,baseline_people=n0,
                       endpoint_people=z.symptom_people.iloc[-1],growth_pct=100*(z.symptom_people.iloc[-1]/n0-1),
                       **capacity_rates(n0,z.year,z.symptom_people)))
    ag = pd.DataFrame(ag)
    ag.to_csv(ROOT/'results/aggregate_capacity_requirements.csv', index=False)
    coverage = []
    for (scenario, year), z in fut.groupby(['scenario','year']):
        n0 = z.ISO3.map(baseline).to_numpy()
        n = z.symptom_people.to_numpy()
        for g in [0,.01,.02,.03,.04,.05]:
            k, used, q = coverage_values(n0,n,g,year)
            coverage.append(pd.DataFrame(dict(ISO3=z.ISO3.to_numpy(),year=year,scenario=scenario,
                annual_expansion=g,baseline_people=n0,symptom_people=n,capacity_equivalents=k,
                used_equivalents=used,unused_equivalents=k-used,coverage=q,
                target_maintained=np.where(n>0,q>=.5-1e-12,False),zero_demand=n==0)))
    cv = pd.concat(coverage,ignore_index=True)
    cv.to_csv(ROOT/'results/country_coverage_paths.csv.gz', index=False, compression='gzip')
    rows = []
    for (scenario, year, g), z in cv.groupby(['scenario','year','annual_expansion']):
        n = z.symptom_people.sum()
        below = z.coverage.lt(.5-1e-12)&~z.zero_demand
        pooled = min(1,z.capacity_equivalents.sum()/n)
        separate = z.used_equivalents.sum()/n
        rows.append(dict(scenario=scenario,year=year,annual_expansion=g,
                         pooled_capacity_coverage=pooled,no_transfer_weighted_coverage=separate,
                         pooled_minus_no_transfer_pp=100*(pooled-separate),
                         countries_below_target=int(below.sum()),
                         demand_share_below_target=z.loc[below,'symptom_people'].sum()/n,
                         unused_capacity_equivalents=z.unused_equivalents.sum(),
                         total_capacity_equivalents=z.capacity_equivalents.sum(),
                         total_need_equivalents=n))
    coverage_summary = pd.DataFrame(rows)
    coverage_summary.to_csv(ROOT/'results/coverage_allocation_comparison.csv', index=False)
    scope_rows=[]
    scopes={'183_countries':set(ca.ISO3),'182_country_sensitivity':set(ca.loc[ca.legacy182,'ISO3']),'TGO':{'TGO'}}
    for scope,isos in scopes.items():
        for (scenario,year,g),z in cv[cv.ISO3.isin(isos)].groupby(['scenario','year','annual_expansion']):
            need=z.symptom_people.sum()
            scope_rows.append(dict(scope=scope,scenario=scenario,year=year,annual_expansion=g,
                pooled_capacity_coverage=min(1,z.capacity_equivalents.sum()/need),
                no_transfer_weighted_coverage=z.used_equivalents.sum()/need))
    pd.DataFrame(scope_rows).to_csv(ROOT/'results/coverage_scope_sensitivity.csv',index=False)
    # The mathematical no-transfer inequality and path-preservation property are tested independently.
    assert (coverage_summary.pooled_minus_no_transfer_pp >= -1e-10).all()
    summary = []
    for scenario, z in rates.groupby('scenario'):
        summary.append(dict(scenario=scenario,countries=len(z),zero_baseline=z.baseline_people.eq(0).sum(),
                            countries_path_above_endpoint=(z.g_path>z.g_endpoint+1e-10).sum(),
                            endpoint_median=z.g_endpoint.median(),path_median=z.g_path.median(),
                            path_min=z.g_path.min(),path_max=z.g_path.max(),
                            maximum_path_endpoint_difference_pp=z.path_minus_endpoint_pp.max()))
    pd.DataFrame(summary).to_csv(ROOT/'results/capacity_country_summary.csv', index=False)

    face = []; expanded = []
    for r in tot[tot.year.isin([2023,2040])].itertuples():
        for e,q,v in itertools.product([.25,.5,.75,1],[.25,.5,.75,1],[1,3]):
            meta = dict(scope=r.scope,year=r.year,scenario=r.scenario)
            face.append(dict(**meta,**activities(r.symptom_people,e,q,v)))
            for phone,doc,coord in itertools.product([10,15],[10,20],[0,15,30]):
                expanded.append(dict(**meta,**activities(r.symptom_people,e,q,v,phone,doc,coord)))
    pd.DataFrame(face).to_csv(ROOT/'results/service_face_and_contacts.csv', index=False)
    pd.DataFrame(expanded).to_csv(ROOT/'results/service_enumerated_workflow.csv', index=False)
    country_services = []
    for r in ca[ca.year.isin([2023,2040])].itertuples():
        for e,q,v in itertools.product([.25,.5,.75,1],[.25,.5,.75,1],[1,3]):
            country_services.append(dict(ISO3=r.ISO3,year=r.year,scenario=r.scenario,
                                         **activities(r.symptom_people,e,q,v,15,10,15)))
    pd.DataFrame(country_services).to_csv(ROOT/'results/country_service_reference_workflow.csv.gz', index=False, compression='gzip')
    standard = []
    for v in [1,3]:
        for phone,doc,coord in itertools.product([10,15],[10,20],[0,15,30]):
            for e,q in itertools.product([.25,.5,.75,1],[.25,.5,.75,1]):
                standard.append(dict(denominator='1000 symptomatic decedents',denominator_count=1000,
                                     **activities(1000,e,q,v,phone,doc,coord)))
            served = activities(1000,1,1,v,phone,doc,coord)
            served.update(symptom_people=np.nan,e=np.nan,q=np.nan,effective_receipt=np.nan,
                          eligibility_role='Conditioned on receiving service; no eligibility assumed')
            standard.append(dict(denominator='1000 service recipients',denominator_count=1000,**served))
    pd.DataFrame(standard).to_csv(ROOT/'results/resources_per_1000.csv', index=False)

    grid = []
    for r in tot[tot.year.isin([2023,2040])].itertuples():
        for p in sorted(set(np.round(np.arange(.5,1.001,.05),2))|{P}):
            grid.append(dict(scope=r.scope,year=r.year,scenario=r.scenario,p=p,
                             symptom_people=r.deaths*p,service_recipients_at_e_q_half=r.deaths*p*.25,
                             one_visit_face_hours_at_e_q_half=r.deaths*p*.25,
                             three_visit_face_hours_at_e_q_half=r.deaths*p*.75,
                             interpretation='Deterministic stress grid, not an empirical probability interval'))
    pd.DataFrame(grid).to_csv(ROOT/'results/symptom_parameter_grid.csv', index=False)
    timegrid = []; tipping = []
    for r in ag.itertuples():
        ratio = r.endpoint_people/r.baseline_people
        tipping.append(dict(scope=r.scope,scenario=r.scenario,baseline_p=P,future_p_no_growth=P/ratio,
                            relative_p_decline_no_growth=1-1/ratio))
        for m in [.5,.75,1,1.25]:
            pf = min(1,P*m)
            timegrid.append(dict(scope=r.scope,scenario=r.scenario,baseline_p=P,multiplier=m,future_p=pf,
                                 future_people=r.endpoint_people*pf/P,
                                 growth_pct=100*(ratio*pf/P-1)))
    pd.DataFrame(timegrid).to_csv(ROOT/'results/time_varying_symptom_sensitivity.csv', index=False)
    pd.DataFrame(tipping).to_csv(ROOT/'results/symptom_tipping_thresholds.csv', index=False)
    pb = ca[ca.year.eq(2040)].pivot(index='ISO3',columns='scenario',values='symptom_people').reset_index()
    pb['population_basis_difference'] = pb.GHE_baseline_WPP_future_sensitivity-pb.fixed_WPP
    pb['population_basis_relative_difference'] = pb.population_basis_difference/pb.fixed_WPP
    pb.to_csv(ROOT/'results/population_basis_country_sensitivity.csv', index=False)
    log('capacity_services','New whole-path and country-allocation models; all lung service/parameter sensitivities retained')
    print(ag[ag.scope.eq('183_countries')].to_string(index=False))
    print(pd.DataFrame(summary).to_string(index=False))
    print(coverage_summary[coverage_summary.scenario.eq('fixed_WPP')&coverage_summary.year.eq(2040)].to_string(index=False))


if __name__ == '__main__':
    main()
