"""Recalculate the lung-cancer model from country-age-sex source cells."""
from common import ROOT, P, KEY, SCENARIOS, log
import itertools
import numpy as np
import pandas as pd


def fit_trends(cells, origin):
    rows = []
    for key, g in cells[cells.year.between(origin-15, origin)].groupby(KEY):
        z = g[g.death_rate > 0].sort_values('year')
        enough = len(z) >= 3 and z.year.max()-z.year.min() >= 5
        raw = float(np.polyfit(z.year-origin, np.log(z.death_rate), 1)[0]) if enough else 0.
        b = float(np.clip(raw, -.05, .05))
        rows.append(dict(zip(KEY, key), origin=origin, positive_anchors=len(z),
                         anchor_years=';'.join(map(str, z.year)), log_slope_raw=raw,
                         log_slope_used=b, slope_capped=raw != b, fallback=not enough,
                         half_life_years=10))
    return pd.DataFrame(rows)


def multiplier(slope, years):
    lam = np.log(2)/10
    return np.exp(slope * (-np.expm1(-lam*years))/lam)


def shapley(p0, p1, r0, r1):
    a = [p0.sum(), p0/p0.sum(), r0]
    b = [p1.sum(), p1/p1.sum(), r1]
    f = lambda s: float(s[0]*np.sum(s[1]*s[2]))
    out = np.zeros(3)
    for order in itertools.permutations(range(3)):
        state = a.copy()
        for j in order:
            v = f(state)
            state[j] = b[j]
            out[j] += f(state)-v
    out /= 6
    assert np.isclose(out.sum(), f(b)-f(a), atol=1e-7, rtol=1e-10)
    return out


def main():
    deaths = pd.read_csv(ROOT/'data/lung_deaths_anchors.csv')
    pop = pd.read_csv(ROOT/'data/population_WPP2024.csv')
    gp = pd.read_csv(ROOT/'data/population_GHE.csv')
    countries = pd.read_csv(ROOT/'data/country_ledger.csv')
    assert deaths.cause.eq('lung_cancer').all() and deaths.ghe_code.eq(680).all()
    x = deaths.merge(pop[KEY+['year', 'population']], on=KEY+['year'], validate='one_to_one')
    x['death_rate'] = x.deaths/x.population
    x['symptom_people'] = x.deaths*P
    x['scenario'] = 'historical_GHE_estimate'
    x.to_csv(ROOT/'results/historical_cells.csv', index=False)
    trends = fit_trends(x, 2023)
    trends.to_csv(ROOT/'results/risk_trend_parameters.csv', index=False)
    base = x[x.year.eq(2023)][KEY+['deaths','death_rate']].rename(columns={'deaths':'baseline_deaths'})
    base = base.merge(trends, on=KEY, validate='one_to_one')
    base = base.merge(gp[gp.year.eq(2023)][KEY+['ghe_population']], on=KEY, validate='one_to_one')
    rows = []
    for year in range(2024, 2041):
        a = base.merge(pop[pop.year.eq(year)][KEY+['population']], on=KEY, validate='one_to_one')
        for scenario in SCENARIOS:
            z = a.copy()
            if scenario == 'fixed_WPP':
                z['model_rate'] = z.death_rate
            elif scenario == 'damped_risk_WPP':
                z['model_rate'] = z.death_rate*multiplier(z.log_slope_used, year-2023)
            else:
                z['model_rate'] = z.baseline_deaths/z.ghe_population
            z['deaths'] = z.model_rate*z.population
            z['symptom_people'] = z.deaths*P
            z['year'] = year
            z['scenario'] = scenario
            rows.append(z[KEY+['year','scenario','population','model_rate','deaths','symptom_people']])
    future = pd.concat(rows, ignore_index=True)
    future.to_csv(ROOT/'results/future_cells_2024_2040.csv.gz', index=False, compression='gzip')
    future[future.year.eq(2040)].to_csv(ROOT/'results/future_cells_2040.csv', index=False)
    assert np.isfinite(future.deaths).all() and future.deaths.ge(0).all()
    country = pd.concat([x, future], ignore_index=True).groupby(['ISO3','year','scenario'], as_index=False)[['deaths','symptom_people']].sum()
    country = country.merge(countries[['ISO3','country','legacy182']], on='ISO3', validate='many_to_one')
    country.to_csv(ROOT/'results/country_paths.csv', index=False)
    scopes = {'183_countries':set(countries.ISO3), '182_country_sensitivity':set(countries.loc[countries.legacy182,'ISO3']), 'TGO':{'TGO'}}
    totals = []
    for scope, isos in scopes.items():
        g = country[country.ISO3.isin(isos)].groupby(['year','scenario'], as_index=False).agg(
            deaths=('deaths','sum'), symptom_people=('symptom_people','sum'), countries=('ISO3','nunique'))
        totals.append(g.assign(scope=scope))
    totals = pd.concat(totals, ignore_index=True)
    totals.to_csv(ROOT/'results/scope_totals.csv', index=False)
    endpoints = country[country.year.eq(2040)].merge(country[country.year.eq(2023)][['ISO3','symptom_people']].rename(columns={'symptom_people':'baseline_people'}), on='ISO3', validate='many_to_one')
    endpoints['absolute_change'] = endpoints.symptom_people-endpoints.baseline_people
    endpoints['growth_ratio'] = np.where(endpoints.baseline_people>0, endpoints.symptom_people/endpoints.baseline_people, np.nan)
    endpoints['growth_pct'] = 100*(endpoints.growth_ratio-1)
    endpoints.to_csv(ROOT/'results/country_endpoint_changes.csv', index=False)
    agesex = pd.concat([x[x.year.isin([2019,2023])], future[future.year.eq(2040)]], ignore_index=True).groupby(['year','scenario','age','sex'], as_index=False)[['deaths','symptom_people']].sum()
    agesex['share_of_year_scenario'] = agesex.symptom_people/agesex.groupby(['year','scenario']).symptom_people.transform('sum')
    agesex.to_csv(ROOT/'results/age_sex_composition.csv', index=False)

    dec = []
    for start, end, scenario in [(2019,2023,'historical_GHE_estimate'), (2023,2040,'fixed_WPP'), (2023,2040,'damped_risk_WPP')]:
        d0 = x[x.year.eq(start)]
        d1 = x[x.year.eq(end)] if end==2023 else future[future.year.eq(end)&future.scenario.eq(scenario)]
        for iso, a in d0.groupby('ISO3'):
            a = a.set_index(['age','sex']).sort_index()
            b = d1[d1.ISO3.eq(iso)].set_index(['age','sex']).sort_index()
            assert a.index.equals(b.index)
            c = shapley(a.population.to_numpy(), b.population.to_numpy(),
                        (a.symptom_people/a.population).to_numpy(), (b.symptom_people/b.population).to_numpy())
            dec.append(dict(ISO3=iso,start=start,end=end,scenario=scenario,population_size=c[0],
                            age_sex_structure=c[1],mortality_risk=c[2],total_change=b.symptom_people.sum()-a.symptom_people.sum()))
    dec = pd.DataFrame(dec)
    dec.to_csv(ROOT/'results/decomposition_countries.csv', index=False)
    dc = dec.groupby(['start','end','scenario'], as_index=False)[['population_size','age_sex_structure','mortality_risk','total_change']].sum()
    dc['structure_share_of_change'] = dc.age_sex_structure/dc.total_change
    dc.to_csv(ROOT/'results/decomposition_summary.csv', index=False)
    ds=[]
    for scope,isos in scopes.items():
        z=dec[dec.ISO3.isin(isos)].groupby(['start','end','scenario'],as_index=False)[['population_size','age_sex_structure','mortality_risk','total_change']].sum()
        ds.append(z.assign(scope=scope))
    pd.concat(ds,ignore_index=True).to_csv(ROOT/'results/decomposition_scope_sensitivity.csv',index=False)

    holdouts = []
    for origin, test in [(2015,2019),(2019,2023)]:
        a = x[x.year.eq(origin)][KEY+['death_rate']].merge(fit_trends(x, origin), on=KEY, validate='one_to_one')
        a = a.merge(x[x.year.eq(test)][KEY+['population','deaths']], on=KEY, validate='one_to_one').rename(columns={'deaths':'reference_deaths'})
        for scenario in ['fixed_WPP','damped_risk_WPP']:
            z = a.copy()
            m = 1 if scenario=='fixed_WPP' else multiplier(z.log_slope_used, test-origin)
            z['predicted_deaths'] = z.death_rate*m*z.population
            holdouts.append(z.assign(origin=origin,test=test,scenario=scenario))
    hc = pd.concat(holdouts, ignore_index=True)
    hc['error'] = hc.predicted_deaths-hc.reference_deaths
    hc.to_csv(ROOT/'results/hindcast_cells.csv', index=False)
    h = hc.groupby(['ISO3','origin','test','scenario'], as_index=False)[['reference_deaths','predicted_deaths']].sum()
    h['error'] = h.predicted_deaths-h.reference_deaths
    h['relative_error'] = np.where(h.reference_deaths>0,h.error/h.reference_deaths,np.nan)
    h['absolute_relative_error'] = h.relative_error.abs()
    h['zero_reference'] = h.reference_deaths.eq(0)
    h.to_csv(ROOT/'results/hindcast_countries.csv', index=False)
    summary = []
    for key, z in h.groupby(['origin','test','scenario']):
        summary.append(dict(zip(['origin','test','scenario'],key),countries=len(z),
                            WAPE=z.error.abs().sum()/z.reference_deaths.sum(),
                            median_signed_relative_error=z.relative_error.median(),
                            median_absolute_relative_error=z.absolute_relative_error.median(),
                            median_absolute_error=z.error.abs().median(),
                            aggregate_bias=z.error.sum()/z.reference_deaths.sum(),
                            zero_reference_countries=z.zero_reference.sum(),
                            max_absolute_relative_error=z.absolute_relative_error.max()))
    pd.DataFrame(summary).to_csv(ROOT/'results/hindcast_summary.csv', index=False)
    hs=[]
    for scope,isos in scopes.items():
        for key,z in h[h.ISO3.isin(isos)].groupby(['origin','test','scenario']):
            hs.append(dict(zip(['origin','test','scenario'],key),scope=scope,countries=len(z),
                WAPE=z.error.abs().sum()/z.reference_deaths.sum(),median_absolute_relative_error=z.absolute_relative_error.median(),
                aggregate_bias=z.error.sum()/z.reference_deaths.sum(),max_absolute_relative_error=z.absolute_relative_error.max()))
    pd.DataFrame(hs).to_csv(ROOT/'results/hindcast_scope_sensitivity.csv',index=False)
    hc.drop_duplicates(KEY+['origin']).groupby('origin',as_index=False).agg(cells=('ISO3','size'),
        capped=('slope_capped','sum'),fallback=('fallback','sum')).to_csv(ROOT/'results/hindcast_risk_fit_counts.csv',index=False)
    rt = future[future.year.eq(2040)].merge(x[x.year.eq(2023)][KEY+['death_rate']], on=KEY, validate='many_to_one')
    rt['rate_ratio'] = np.where(rt.death_rate>0,rt.model_rate/rt.death_rate,np.nan)
    rt['rate_over_one'] = rt.model_rate.gt(1)
    rt.to_csv(ROOT/'results/extrapolation_checks.csv', index=False)
    pd.DataFrame([dict(cells=len(trends), capped=trends.slope_capped.sum(), fallback=trends.fallback.sum(),
                       zero_origin_rates=base.death_rate.eq(0).sum())]).to_csv(ROOT/'results/risk_model_counts.csv', index=False)
    log('model_lung','Recalculated all lung-cancer cells, country paths, decomposition and holdouts')
    print(totals[totals.scope.eq('183_countries')&totals.year.isin([2023,2040])].to_string(index=False))
    print(dc.to_string(index=False))
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == '__main__':
    main()
