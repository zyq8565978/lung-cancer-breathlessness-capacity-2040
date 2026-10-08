"""Aggregate national outputs using a fixed official mapping."""
from common import *

def grouped(df,m,field,all_rows=True):
    x=df.merge(m[['ISO3',field]],on='ISO3',validate='many_to_one').rename(columns={field:'group'})
    if all_rows:
        z=df.copy();z['group']='ALL';x=pd.concat([x,z],ignore_index=True)
    return x


def population(m,field):
    cp=read('country_paths.csv');cp=cp[(cp.year.eq(2023)&cp.scenario.eq('historical_GHE_estimate'))|((cp.year>=2024)&cp.scenario.isin(['fixed_WPP','damped_risk_WPP']))]
    cp=grouped(cp,m,field)
    annual=cp.groupby(['group','year','scenario'],as_index=False).agg(symptom_people=('symptom_people','sum'),countries=('ISO3','nunique'))
    base=annual[annual.year.eq(2023)].set_index('group').symptom_people
    annual['index_2023_100']=annual.symptom_people/annual.group.map(base)*100
    hist=read('historical_cells.csv');fut=read('future_cells_2024_2040.csv.gz')
    cells=pd.concat([hist[hist.year.eq(2023)][['ISO3','age','sex','year','scenario','symptom_people']],fut[fut.year.isin([2027,2040])&fut.scenario.isin(['fixed_WPP','damped_risk_WPP'])][['ISO3','age','sex','year','scenario','symptom_people']]])
    cells=grouped(cells,m,field)
    demographics=cells.groupby(['group','year','scenario','age','sex'],as_index=False).symptom_people.sum()
    demographics['share']=demographics.symptom_people/demographics.groupby(['group','year','scenario']).symptom_people.transform('sum')
    rows=[]
    for name,z in annual.groupby('group',sort=False):
        n23=z[z.year.eq(2023)].symptom_people.item();n27=z[z.year.eq(2027)&z.scenario.eq('fixed_WPP')].symptom_people.item()
        n40=z[z.year.eq(2040)&z.scenario.eq('fixed_WPP')].symptom_people.item()
        path=z[z.year.gt(2027)&z.scenario.eq('fixed_WPP')].copy();path['requirement']=(path.symptom_people/n27)**(1/(path.year-2027))-1
        binding=path.loc[path.requirement.idxmax()]
        rec={'group':name,'countries':int(z.countries.iloc[0]),'people_2023':n23,'people_2027':n27,'people_2040':n40,
             'people_2040_risk':z[z.year.eq(2040)&z.scenario.eq('damped_risk_WPP')].symptom_people.item(),
             'absolute_change':n40-n23,'growth_pct':100*(n40/n23-1),'g_end_2027_pct':100*((n40/n27)**(1/13)-1),
             'g_path_2027_pct':100*binding.requirement,'binding_year':int(binding.year)}
        for year,n in [(2023,n23),(2027,n27),(2040,n40)]:
            a=demographics[demographics.group.eq(name)&demographics.year.eq(year)&~demographics.scenario.eq('damped_risk_WPP')]
            rec[f'aged70_{year}_pct']=100*a[a.age.eq('70+')].symptom_people.sum()/n
            rec[f'female_{year}_pct']=100*a[a.sex.eq('Females')].symptom_people.sum()/n
            total=annual[annual.group.eq('ALL')&annual.year.eq(year)&~annual.scenario.eq('damped_risk_WPP')].symptom_people.item()
            rec[f'share_{year}_pct']=100*n/total
            rec[f'eligible_{year}']=n*P['eligibility'];rec[f'offered_{year}']=n*P['eligibility']*P['q_offer']
            rec[f'first_{year}']=rec[f'offered_{year}']*P['c1'];rec[f'second_{year}']=rec[f'offered_{year}']*P['c2']
            rec[f'target_hours_{year}']=rec[f'offered_{year}']*P['h_hours_per_offered']
        rows.append(rec)
    return annual,demographics,pd.DataFrame(rows)


def allocation(m,field):
    ac=read('allocation_country.csv.gz')
    ac=ac[ac.risk.isin(['fixed_WPP','damped_risk_WPP'])].copy()
    assert sorted(ac.year.unique())==list(range(2027,2041))
    assert not ac.duplicated(['ISO3','year','risk','annual_growth','strategy','local_cap']).any()
    assert np.allclose(ac.completed,ac.offered*P['c2'],atol=1e-8)
    ac['positive_shortfall']=(P['q_offer']*ac.eligible-ac.offered).clip(lower=0)
    ac['below']=ac.coverage.lt(P['q_offer']-1e-10)
    ac['eligible_below']=ac.eligible.where(ac.below,0)
    ac['target']=P['q_offer']*ac.eligible
    assert np.allclose(ac.positive_shortfall,ac.shortfall,atol=1e-8)
    ac=grouped(ac,m,field)
    keys=['risk','local_cap','annual_growth','strategy','group','year']
    out=ac.groupby(keys,as_index=False).agg(countries=('ISO3','nunique'),eligible=('eligible','sum'),offered=('offered','sum'),
         hours=('capacity_hours','sum'),second_contacts=('completed','sum'),shortfall=('positive_shortfall','sum'),target=('target','sum'),
         below_n=('below','sum'),need_below=('eligible_below','sum'),coverage_min=('coverage','min'),
         coverage_p05=('coverage',lambda x:x.quantile(.05)),coverage_p25=('coverage',lambda x:x.quantile(.25)),coverage_median=('coverage','median'))
    out['offer_coverage_pct']=100*out.offered/out.eligible
    out['second_coverage_pct']=100*out.second_contacts/out.eligible
    out['shortfall_pct_target']=100*out.shortfall/out.target
    out['below_pct']=100*out.below_n/out.countries
    out['demand_share_below_pct']=100*out.need_below/out.eligible
    out['used_hours']=out.offered*P['h_hours_per_offered']
    out['idle_hours']=(out.hours-out.used_hours).clip(lower=0)
    out=out.sort_values(keys)
    out['cumulative_shortfall']=out.groupby(keys[:-1]).shortfall.cumsum()
    out['cumulative_target']=out.groupby(keys[:-1]).target.cumsum()
    out['cumulative_shortfall_pct_target']=100*out.cumulative_shortfall/out.cumulative_target
    return out


def main():
    m=pd.read_csv(REPOSITORY/'data/inputs/country_region_income_mapping.csv')
    assert len(m)==183 and m.ISO3.nunique()==183
    assert m.loc[m.ISO3.eq('IDN'),'WHO_region'].item()=='WPR'
    for field,prefix in [('WHO_region','regional'),('World_Bank_income_group','income')]:
        annual,demo,pop=population(m,field)
        if prefix=='regional':
            rank={'ALL':0}|{r:j+1 for j,r in enumerate(REGIONS)}
            pop=pop.sort_values('group',key=lambda c:c.map(rank)).reset_index(drop=True)
        save(prefix+'_annual',annual);save(prefix+'_age_sex',demo);save(prefix+'_population',pop)
        alloc=allocation(m,field);save(prefix+'_allocation_annual',alloc)
        if prefix=='regional':
            end=alloc[alloc.year.eq(2040)].copy();save('regional_allocation_endpoint',end)
            selected=end[end.risk.eq('fixed_WPP')&end.local_cap.eq('Unconstrained new capacity')&end.annual_growth.isin([.02,.03])]
            save('main_regional_allocation',selected)
            save('Table_1_values',pop);save('Table_2_values',selected[selected.group.eq('ALL')])
    dec=grouped(read('decomposition_countries.csv'),m,'WHO_region')
    save('regional_decomposition',dec.groupby(['group','start','end','scenario'],as_index=False)[['population_size','age_sex_structure','mortality_risk','total_change']].sum())
    print('National outputs aggregated by WHO region and income group.')

if __name__=='__main__': main()
