from plot_style import *

def fig1():
    fig=plt.figure(figsize=(185/25.4,195/25.4))
    a=axis(fig,[.105,.60,.35,.31],'A','Projected symptom-related\npopulation')
    x=frame('regional_annual');allx=x[x.group.eq('ALL')]
    b=allx[allx.year.eq(2023)].iloc[0]
    a.scatter([2023],[b.symptom_people/1e6],color=dark(LAVENDER),s=20,zorder=5)
    for sc,c,ls,dy in [('fixed_WPP',LAVENDER,'-',-.065),('damped_risk_WPP',ROSE,'--',.03)]:
        z=pd.concat([allx[allx.year.eq(2023)],allx[allx.scenario.eq(sc)]]).sort_values('year')
        a.plot(z.year,z.symptom_people/1e6,color=dark(c),ls=ls)
        val=z.iloc[-1].symptom_people/1e6
        a.annotate(f'{val:.3f}',(2040,val),(2038.5,val+dy) if sc=='damped_risk_WPP' else (2036,2.055),ha='right',fontsize=8.5,arrowprops={'arrowstyle':'-','color':dark(c),'lw':.5})
    a.text(2023.3,b.symptom_people/1e6-.055,f'{b.symptom_people/1e6:.3f}',va='top')
    a.axvline(2027,color='#999999',lw=.7,ls=':')
    a.text(2027.4,2.30,'2027 planning start',fontsize=8.5)
    a.set(xlim=(2022.7,2041),ylim=(1.25,2.38),xticks=[2023,2027,2033,2040],ylabel='People (millions)',xlabel='Year')
    a.legend([Line2D([0],[0],color=dark(LAVENDER)),Line2D([0],[0],color=dark(ROSE),ls='--')],['Fixed rate','Risk sensitivity'],loc='upper left',bbox_to_anchor=(-.02,.89),frameon=False,handlelength=1.8)
    a=axis(fig,[.60,.60,.30,.31],'B','Regional relative growth\n')
    ends={r:x[x.group.eq(r)&x.year.eq(2040)&x.scenario.eq('fixed_WPP')].index_2023_100.item() for r in REGIONS}
    targets={};last=-1e9
    for r,v in sorted(ends.items(),key=lambda p:p[1]):
        targets[r]=max(v,last+5.4);last=targets[r]
    for j,r in enumerate(REGIONS):
        z=x[x.group.eq(r)&(x.scenario.eq('fixed_WPP')|x.year.eq(2023))].sort_values('year')
        a.plot(z.year,z.index_2023_100,color=dark(REGION_COLORS[r]),ls=REGION_STYLES[j],lw=1.6)
        a.annotate(r,(2040,ends[r]),(2042,targets[r]),va='center',fontsize=8.5,annotation_clip=False,
                   arrowprops={'arrowstyle':'-','color':dark(REGION_COLORS[r]),'lw':.55})
    a.axhline(100,color='#b0b0b0',lw=.6)
    a.set(xlim=(2023,2040),ylim=(95,190),xticks=[2023,2027,2033,2040],ylabel='Index (2023 = 100)',xlabel='Year')
    base=axis(fig,[.105,.13,.35,.31],'C','Age and sex composition')
    base.axis('off')
    z=frame('F1B_age_sex');ages=['30-49','50-59','60-69','70+']
    ages_display=['30–49','50–59','60–69','70+']
    for sex,rect in [('Males',[.105,.13,.145,.27]),('Females',[.31,.13,.145,.27])]:
        a=fig.add_axes(rect)
        for year,off in [(2023,.17),(2040,-.17)]:
            v=z[z.year.eq(year)&z.sex.eq(sex)].set_index('age').loc[ages,'symptom_people'].to_numpy()/1000
            a.barh(np.arange(4)+off,v,height=.27,facecolor='white' if year==2023 else LAVENDER,
                   edgecolor=dark(LAVENDER),lw=.75)
        a.set(ylim=(-.6,3.7),xlim=(900,0) if sex=='Males' else (0,900),xticks=[0,400,800],yticks=[])
        a.set_title('Male' if sex=='Males' else 'Female',fontsize=8.5,pad=4)
        a.spines['left'].set_visible(False);grid(a)
    for j,label in enumerate(ages_display):
        fig.text(.28,.13+.27*(j+.6)/4.3,label,ha='center',va='center',fontsize=8.5)
    shares=[100*z[z.year.eq(y)&z.age.eq('70+')].symptom_people.sum()/z[z.year.eq(y)].symptom_people.sum() for y in [2023,2040]]
    fig.text(.28,.437,f'Age ≥70: {shares[0]:.1f}% → {shares[1]:.1f}%',ha='center',fontsize=8.5)
    fig.text(.28,.08,'People (thousands)',ha='center',fontsize=9)
    base.legend(handles=[Rectangle((0,0),1,1,facecolor='white',edgecolor=dark(LAVENDER),label='2023'),
                         patch(LAVENDER,'2040')],loc='upper center',bbox_to_anchor=(.5,-.22),ncol=2,frameon=False)
    a=axis(fig,[.60,.13,.35,.31],'D','Contributions to increase')
    yy=np.arange(6)
    dec=frame('regional_decomposition').query("start==2023 and scenario=='fixed_WPP'").set_index('group').loc[REGIONS]
    pos=np.zeros(6);neg=np.zeros(6)
    for k,c,h in [('population_size',LAVENDER,''),('age_sex_structure',PEACH,'///')]:
        v=dec[k].to_numpy()/1000;left=np.where(v>=0,pos,neg)
        a.barh(yy,v,left=left,height=.56,color=c,edgecolor=dark(c),lw=.5,hatch=h)
        pos+=np.maximum(v,0);neg+=np.minimum(v,0)
    for y,n in zip(yy,dec.total_change/1000):a.annotate(f'{n:,.1f}',(n,y),xytext=(3,0),textcoords='offset points',va='center',fontsize=8.5)
    a.set(yticks=yy,yticklabels=REGIONS,ylim=(5.6,-.6),xlim=(min(0,neg.min())-3,495),xlabel='Increase (thousands)');grid(a)
    a.legend(handles=[patch(LAVENDER,'Population size'),patch(PEACH,'Age–sex structure','///')],
             loc='upper center',bbox_to_anchor=(.5,-.22),ncol=1,frameon=False)
    export(fig,'Figure_1','Main_Figures')

def fig2():
    fig=plt.figure(figsize=(185/25.4,120/25.4))
    a=axis(fig,[.235,.23,.32,.60],'A','Service opportunities\nand attendance')
    b=axis(fig,[.66,.23,.30,.60],'B','Nursing activity hours\nfor the two targets')
    targets=frame('F2C_target_conversion');rows=[];hours=[]
    for i,r in enumerate(targets.itertuples()):
        values=[r.offered,r.first,r.second]
        for j,v in enumerate(values):
            y=i*4+j
            a.barh(y,v,height=.52,color=CONTACT_COLORS[j],edgecolor=dark(CONTACT_COLORS[j]),lw=.6)
            a.annotate(f'{v:,.1f}',(v,y),xytext=(4,0),textcoords='offset points',va='center')
            rows.append({'target':r.target,'stage':['Offered','First-contact attendees','Second-contact attendees'][j],'people_per_1000_eligible':v})
        a.text(0,i*4-.78,['50% offered a service','50% attend the second contact'][i],fontsize=8.5,va='center',fontweight='semibold')
        v=np.array([(r.first+r.second)*P['duration_mid']/60,
                    (r.first+r.second)*P['documentation_minutes']/60,r.offered*P['coordination_minutes']/60])
        assert np.isclose(v.sum(),r.hours)
        left=0
        for k,h in enumerate(v):
            b.barh(i*4+1,h,left=left,height=.78,color=ACT_COLORS[k],edgecolor=dark(ACT_COLORS[k]),lw=.6,hatch=['','///',''][k]);left+=h
        b.annotate(f'{left:,.1f}',(left,i*4+1),xytext=(4,0),textcoords='offset points',va='center')
        hours.append({'target':r.target,'direct_hours':v[0],'documentation_hours':v[1],'coordination_hours':v[2],'hours_per_1000_eligible':left})
    a.set(yticks=[0,1,2,4,5,6],yticklabels=['Offered','First-contact\nattendees','Second-contact\nattendees']*2,
          ylim=(6.75,-1.1),xlim=(0,1000),xticks=[0,500,1000],xlabel='People per 1000 eligible');grid(a)
    b.set(yticks=[],ylim=(6.75,-1.1),xlim=(0,1350),xticks=[0,500,1000],xlabel='Hours per 1000 eligible');grid(b)
    b.legend(handles=[patch(c,n,h) for c,n,h in zip(ACT_COLORS,['Direct contacts','Documentation','Coordination'],['','///',''])],
             loc='upper center',bbox_to_anchor=(.5,-.19),frameon=False,ncol=1,borderaxespad=0,labelspacing=.25)
    save('F2A_contacts_v8',pd.DataFrame(rows));save('F2B_activities_v8',pd.DataFrame(hours))
    export(fig,'Figure_2','Main_Figures')

def fig3():
    fig=plt.figure(figsize=(185/25.4,185/25.4));d=frame('main_regional_allocation');order=['ALL']+REGIONS
    limit=max(10,np.ceil(d.cumulative_shortfall_pct_target.max()/2)*2)
    covlimits=(min(35,np.floor(d.offer_coverage_pct.min()/5)*5),max(70,np.ceil(d.offer_coverage_pct.max()/5)*5))
    for rect,letter,g,k,title in [([.255,.58,.29,.32],'A',.02,'offer_coverage_pct','2040 offer coverage\n2% annual expansion'),([.665,.58,.29,.32],'B',.03,'offer_coverage_pct','2040 offer coverage\n3% annual expansion'),([.255,.14,.29,.32],'C',.02,'cumulative_shortfall_pct_target','Cumulative shortfall\n2% annual expansion'),([.665,.14,.29,.32],'D',.03,'cumulative_shortfall_pct_target','Cumulative shortfall\n3% annual expansion')]:
        a=axis(fig,rect,letter,title)
        for j,s in enumerate(STRATEGIES):
            z=d[d.annual_growth.eq(g)&d.strategy.eq(s)].set_index('group').loc[order]
            v=z[k].to_numpy();y=np.arange(7)+(j-1)*.25
            a.scatter(v,y,s=22,marker=MARKERS[j],facecolor=COLORS[s],edgecolor=dark(COLORS[s]),lw=.65,zorder=5,clip_on=False)
            for idx,(yy,vv) in enumerate(zip(y,v)):
                if j==0 and idx in [0,1,5]:
                    label='0' if abs(vv)<1e-9 else (f'{vv:.1f}' if k=='offer_coverage_pct' else f'{vv:.2f}')
                    a.annotate(label,(vv,yy),xytext=(5,-1),textcoords='offset points',fontsize=8.5,va='center')
        labels=['All included\ncountries','Africa','Americas','South-East\nAsia','Europe','Eastern\nMediterranean','Western\nPacific'] if letter in ['A','C'] else ['']*7
        a.set(yticks=np.arange(7),yticklabels=labels,ylim=(6.65,-.7));a.tick_params(axis='y',length=0,pad=6)
        a.axhline(.5,color='#b0b0b0',lw=.6)
        if k=='offer_coverage_pct':
            a.set(xlim=covlimits,xticks=[35,50,70],xlabel='Offer coverage (%)');a.axvline(50,color='#5b5b5b',lw=.75,ls=':')
        else:a.set(xlim=(0,limit),xticks=np.arange(0,limit+0.1,2),xlabel='Shortfall / target (%)')
        grid(a)
    legends(fig,[Line2D([0],[0],linestyle='none',marker=MARKERS[j],markerfacecolor=COLORS[s],markeredgecolor=dark(COLORS[s]),markersize=5,label=NAMES[s]) for j,s in enumerate(STRATEGIES)],.025,3)
    export(fig,'Figure_3','Main_Figures')

def s1():
    fig=plt.figure(figsize=(185/25.4,145/25.4));ax=fig.add_axes([.025,.04,.95,.93]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    boxes=[(.03,.78,.42,.17,'Mortality and population\nWHO GHE2023; UN WPP2024\n183 countries, age ≥30',LAVENDER),
           (.55,.78,.42,.17,'Future annual death cohorts\nFixed cell-specific rates\nDamped-risk sensitivity',LAVENDER),
           (.55,.51,.42,.17,'Symptom-related population\nN = deaths × p\np = 0.78',PEACH),
           (.03,.51,.42,.17,'Service-applicable population\nE = eN\nReference e = 0.50',PEACH),
           (.03,.23,.42,.18,'Opportunities and contacts\nO = min(E, K/h)\nFirst = c1O; second = c2O',ROSE),
           (.55,.23,.42,.18,'Country nursing-hour capacity\n2027 target-calibrated origin\nAnnual additions: three rules',ROSE)]
    for x,y,w,h,t,c in boxes:
        ax.add_patch(Rectangle((x,y),w,h,facecolor='white',edgecolor=dark(c),lw=1.1));ax.text(x+w/2,y+h/2,t,ha='center',va='center',linespacing=1.45,fontsize=9)
    for p,q in [((.45,.865),(.55,.865)),((.76,.78),(.76,.68)),((.55,.595),(.45,.595)),((.24,.51),(.24,.41)),((.55,.32),(.45,.32))]:
        ax.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>',mutation_scale=9,lw=.8,color='#555555'))
    ax.text(.5,.11,'Country offer coverage and positive target shortfalls',ha='center',fontweight='semibold',fontsize=10)
    ax.text(.5,.04,'Regional results: sums of country values under the same allocation paths',ha='center',fontsize=8.5)
    export(fig,'Fig_S1','Supplementary_Figures')

def s2():
    d=frame('FS2_regional_atlas');columns=[f'{int(g*100)}%_{s}' for g in [.02,.03] for s in ['Uniform','Demand','Minimum']]
    cmap=LinearSegmentedColormap.from_list('coverage',[dark(ROSE),ROSE,'#fffdfc',LAVENDER,dark(LAVENDER)])
    norm=TwoSlopeNorm(vmin=0,vcenter=50,vmax=100)
    for page in range(3):
        z=d.iloc[page*61:(page+1)*61]
        fig=plt.figure(figsize=(185/25.4,242/25.4));ax=fig.add_axes([.53,.095,.43,.83])
        im=ax.imshow(100*z[columns].to_numpy(),cmap=cmap,norm=norm,aspect='auto',interpolation='nearest')
        ax.set(yticks=np.arange(len(z)),yticklabels=z.country,xticks=np.arange(6),xticklabels=['Uniform','Demand','Minimum']*2)
        ax.xaxis.tick_top();ax.tick_params(length=0);ax.tick_params(axis='y',pad=5,labelsize=8.5);ax.tick_params(axis='x',pad=6,labelsize=8.5)
        for j,r in enumerate(z.itertuples()):
            fig.text(.025,.095+.83*(1-(j+.5)/61),r.WHO_region,va='center',fontsize=8.5)
            if j>0 and z.iloc[j].WHO_region!=z.iloc[j-1].WHO_region:ax.axhline(j-.5,color='#333333',lw=.8)
        ax.axvline(2.5,color='white',lw=3)
        for y in np.arange(.5,61,1):ax.axhline(y,color='white',lw=.18)
        for spine in ax.spines.values():spine.set_visible(False)
        fig.text(.64,.965,'2% annual expansion',ha='center',fontsize=9)
        fig.text(.85,.965,'3% annual expansion',ha='center',fontsize=9)
        cb=fig.colorbar(im,cax=fig.add_axes([.55,.041,.36,.013]),orientation='horizontal',ticks=[0,25,50,75,100])
        cb.set_label('Offer coverage (%)',fontsize=8.5,labelpad=1);cb.ax.tick_params(labelsize=8.5,length=2,pad=1)
        name='Fig_S2'+('' if page==0 else f'_continued_{page+1}')
        export(fig,name,'Supplementary_Figures')

def s3():
    fig=plt.figure(figsize=(185/25.4,105/25.4));d=frame('F3AB_ECDF')
    for rect,l,g in [([.105,.24,.37,.57],'A',.02),([.60,.24,.37,.57],'B',.03)]:
        a=axis(fig,rect,l,f'{int(g*100)}% annual expansion')
        for j,s in enumerate(STRATEGIES):
            z=d[d.annual_growth.eq(g)&d.strategy.eq(s)]
            a.step(np.r_[0,z.coverage_pct,100],np.r_[0,z.countries_at_or_below_pct,100],where='post',color=dark(COLORS[s]),ls=STYLES[j],marker=MARKERS[j],markevery=[0,46,92,138,184],markersize=3)
        a.axvline(50,color='#888888',lw=.7,ls=':');a.set(xlim=(0,100),ylim=(0,102),xticks=[0,25,50,75,100],xlabel='Offer coverage (%)')
        if l=='A':a.set_ylabel('Countries at or below coverage (%)')
    legends(fig,[Line2D([0],[0],color=dark(COLORS[s]),ls=STYLES[j],marker=MARKERS[j],markersize=3,label=NAMES[s]) for j,s in enumerate(STRATEGIES)],.015,3)
    export(fig,'Fig_S3','Supplementary_Figures')

def s4():
    fig=plt.figure(figsize=(185/25.4,170/25.4));d=frame('FS3_hindcast')
    for rect,letter,o,t in [([.11,.58,.35,.32],'A',2015,2019),([.61,.58,.35,.32],'B',2019,2023)]:
        a=axis(fig,rect,letter,f'Backcast {o}–{t}')
        z=d[d.origin.eq(o)]
        lo=min(z.reference_deaths.min(),z.predicted_deaths.min())*.8;hi=max(z.reference_deaths.max(),z.predicted_deaths.max())*1.3
        for sc,col,m in [('fixed_WPP',LAVENDER,'o'),('damped_risk_WPP',ROSE,'^')]:
            zz=z[z.scenario.eq(sc)];a.scatter(zz.reference_deaths,zz.predicted_deaths,s=11,marker=m,facecolors='none' if m=='^' else col,edgecolors=dark(col),lw=.5)
        a.plot([lo,hi],[lo,hi],ls=':',color='#888888',lw=.6);a.set(xscale='log',yscale='log',xlim=(lo,hi),ylim=(lo,hi),xlabel='Later GHE estimate',ylabel='Backcast deaths')
    for rect,letter,o,t in [([.20,.14,.26,.24],'C',2015,2019),([.70,.14,.26,.24],'D',2019,2023)]:
        a=axis(fig,rect,letter,f'Error summaries {o}–{t}');x=frame('S5_hindcast');x=x[x.origin.eq(o)]
        for j,(sc,c) in enumerate([('fixed_WPP',LAVENDER),('damped_risk_WPP',ROSE)]):
            r=x[x.scenario.eq(sc)].iloc[0];v=100*r[['WAPE','median_absolute_relative_error','max_absolute_relative_error']].to_numpy(dtype=float)
            a.barh(np.arange(3)+(j-.5)*.30,v,height=.27,color=c,edgecolor=dark(c),lw=.5)
            for y,val in zip(np.arange(3)+(j-.5)*.30,v):a.annotate(f'{val:.1f}',(val,y),xytext=(3,0),textcoords='offset points',va='center')
        a.set(yticks=[0,1,2],yticklabels=['WAPE','Median absolute','Maximum absolute'],ylim=(2.6,-.6),xlim=(0,150),xticks=[0,50,100,150],xlabel='Error (%)');grid(a)
    legends(fig,[patch(LAVENDER,'Fixed rate'),patch(ROSE,'Risk sensitivity')],.02,2)
    export(fig,'Fig_S4','Supplementary_Figures')

def s5():
    fig=plt.figure(figsize=(185/25.4,200/25.4))
    a=axis(fig,[.105,.61,.35,.30],'A','Symptom-parameter change')
    d=frame('FS4A_symptom');base=frame('regional_population').query("group=='ALL'").people_2023.item()
    for sc,c,ls in [('fixed_WPP',LAVENDER,'-'),('damped_risk_WPP',ROSE,'--')]:
        z=d[d.scenario.eq(sc)].sort_values('multiplier');a.plot(z.multiplier,z.future_people/1e6,color=dark(c),ls=ls,marker='o',ms=3,label='Fixed' if sc=='fixed_WPP' else 'Risk')
    a.axhline(base/1e6,color='#999999',lw=.7,ls=':');a.text(.51,base/1e6+.06,'2023',fontsize=8.5)
    a.set(xlabel='Future / baseline symptom proportion',ylabel='2040 people (millions)',xticks=[.5,.75,1,1.25]);a.legend(frameon=False,loc='upper left',ncol=2,handlelength=1.6)
    a=axis(fig,[.625,.61,.34,.30],'B','Activity-time scenarios');d=frame('FS4B_activity')
    for cs,c in [('Low',WARM),('Trial',LAVENDER),('High',ROSE)]:
        for den,ls,m in [('1000 offered','-','o'),('1000 completed','--','^')]:
            z=d[d.completion_scenario.eq(cs)&d.denominator.eq(den)].sort_values('duration');a.plot(z.duration,z.specified_hours,color=dark(c),ls=ls,marker=m,ms=3)
    a.set(xlabel='Minutes per contact',ylabel='Hours per 1000 people',xticks=[30,37.5,45])
    a.legend(handles=[Line2D([0],[0],color=dark(c),label=n) for c,n in [(WARM,'Low'),(LAVENDER,'Reference'),(ROSE,'High')]],frameon=False,ncol=3,loc='upper left',bbox_to_anchor=(-.01,1.02),handlelength=.7,columnspacing=.6)
    a.text(.5,-.23,'Solid: offered; dashed: second contact',transform=a.transAxes,ha='center')
    a=axis(fig,[.105,.15,.35,.28],'C','Joint-attendance bounds');d=frame('FS4C_bounds')
    lower=d.joint_completion.min();upper=d.joint_completion.max()
    for j,z in enumerate([.25,.5,.75]):
        lo=100*z/upper;hi=100*z/lower;a.barh(j,hi-lo,left=lo,height=.38,color=LAVENDER,edgecolor=dark(LAVENDER),lw=.7)
        a.text((lo+hi)/2,j-.28,f'{lo:.1f}–{hi:.1f}%',ha='center',va='bottom')
    a.axvline(100,color='#777777',ls=':',lw=.7);a.set(yticks=[0,1,2],yticklabels=['25%','50%','75%'],ylim=(2.6,-.8),xlim=(0,140),xticks=[0,50,100,140],xlabel='Required offer coverage (%)',ylabel='Joint-completion target');grid(a)
    a=axis(fig,[.72,.15,.245,.28],'D','Committed budget: 3%');d=frame('FS4D_budget');stresses=list(d.stress.unique())
    labels=['Reference','p = 0.50','p = 1.00','e = 0.25','e = 0.75','30 min','45 min','Low attendance','High attendance']
    for j,s in enumerate(STRATEGIES):
        z=d[d.strategy.eq(s)].set_index('stress').loc[stresses];a.barh(np.arange(len(stresses))+(j-1)*.21,z.cumulative_shortfall/1000,height=.19,color=COLORS[s],edgecolor=dark(COLORS[s]),lw=.4,hatch=HATCHES[j])
    a.set(yticks=range(len(stresses)),yticklabels=labels,ylim=(len(stresses)-.4,-.7),xlim=(0,None),xlabel='Cumulative shortfall\n(thousands)');grid(a)
    strategies(fig,.018);export(fig,'Fig_S5','Supplementary_Figures')

if __name__=='__main__':
    fig1();fig2();fig3();s1();s2();s3();s4();s5()
    (ROOT/'author_records/qa/figure_layout_checks.json').write_text(json.dumps(AUDIT,indent=2))
    print(json.dumps(AUDIT,indent=2))
