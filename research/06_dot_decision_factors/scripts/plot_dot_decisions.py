#!/usr/bin/env python3
"""Reproduce descriptive DOT evidence figures from the Module 06 master CSV.
Run from repository root: python research/06_dot_decision_factors/scripts/plot_dot_decisions.py
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[1]
df=pd.read_csv(ROOT/'data/dot_decision_evidence.csv',keep_default_na=False)
out=ROOT/'figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'savefig.dpi':190})

# Plot 1: all dated documentary observations; one marker per CSV row, not independent DOT decisions.
sub=df[(df.state!='US') & (df.document_year.astype(str).str.match(r'^\d{4}$'))].copy()
sub['year']=pd.to_numeric(sub.document_year)
states=sorted(sub.state.unique()); y={s:i for i,s in enumerate(states)}
fig,ax=plt.subplots(figsize=(12,5.6))
for state,g in sub.groupby('state'):
    for j,(_,r) in enumerate(g.sort_values(['year','source_title']).iterrows()):
        yy=y[state]+(j%3-1)*0.12
        is_formal=('specification_acceptance' in r.decision_factor or 'transition_procedure' in r.decision_factor)
        ax.scatter(r.year,yy,marker='s' if is_formal else 'o',s=85 if is_formal else 54,alpha=.85)
ax.set_yticks(list(y.values()),states);ax.set_xlim(2005,2025);ax.set_xticks(range(2006,2025,2))
ax.set_xlabel('Year represented by evidence (not necessarily approval year)')
ax.set_title('Historical development of PLC evaluation and implementation in transportation projects, 2007–2023')
ax.grid(axis='x',alpha=.2)
ax.legend(handles=[Line2D([0],[0],marker='s',linestyle='',color='0.3',label='Explicit specification/procedure record'),Line2D([0],[0],marker='o',linestyle='',color='0.3',label='Other research, field or retrospective evidence')],loc='upper left',fontsize=8)
fig.text(.09,.01,'Each point is a documented observation. Retrospective dates and early ASTM C1157 field uses are not Type IL acceptance dates.',fontsize=8)
fig.tight_layout(rect=[0,.045,1,1]);fig.savefig(out/'01_dot_historical_evidence_timeline.png');plt.close(fig)

# Plot 2: coded themes, counting unique source URLs per theme, not agencies or causal weight.
def theme(x):
    x=x.lower()
    if any(k in x for k in ['qualification','transition_procedure']):return 'Qualification / transition procedures'
    if any(k in x for k in ['supply_shortage','supply_transition']):return 'Supply conditions'
    if 'environmental' in x:return 'Environmental objectives'
    if any(k in x for k in ['technical','research_investment','field_performance']):return 'Technical evaluation / performance'
    if any(k in x for k in ['field','demonstration','trial']):return 'Field demonstrations / trials'
    return 'Standards / acceptance / guidance'
df['theme']=df.decision_factor.map(theme)
counts=df.groupby('theme').source_url.nunique().sort_values()
fig,ax=plt.subplots(figsize=(10.5,5.2));bars=ax.barh(counts.index,counts.values)
for b,v in zip(bars,counts.values):ax.text(v+.08,b.get_y()+b.get_height()/2,str(v),va='center')
ax.set_xlim(0,max(counts.values)+1.5);ax.set_xlabel('Distinct source URLs with at least one coded observation')
ax.set_title('Themes documented in the collected DOT evidence')
fig.text(.08,.015,'Non-systematic collection; one source may support multiple themes. Counts are not DOT prevalence or mechanism importance.',fontsize=8)
fig.tight_layout(rect=[0,.045,1,1]);fig.savefig(out/'02_dot_evidence_themes.png');plt.close(fig)

# Plot 3: two agency-specific pathways, directly sourced to records in the master CSV.
fig,axs=plt.subplots(2,1,figsize=(12,5.7),sharex=True)
items=[('CA',[(2020,'Scoping: Type IL not permitted; evaluation proposed'),(2021,'Directive: Type IL permitted; older contracts via change order')]),('UT',[(2009,'SR 201 comparative field use (retrospective account)'),(2023,'Agency report: supply shortages; expedited qualification')])]
for ax,(state,events) in zip(axs,items):
    ax.hlines(0,2007,2024,color='0.75',linewidth=2)
    for k,(year,label) in enumerate(events):
        ax.scatter(year,0,s=120,zorder=3)
        ax.annotate(label,(year,0),xytext=(0,22 if k%2==0 else -30),textcoords='offset points',ha='center',va='center',fontsize=8,wrap=True)
    ax.set_ylim(-.8,.8);ax.set_yticks([]);ax.set_ylabel(state,rotation=0,labelpad=20,weight='bold');ax.spines[['left','right','top']].set_visible(False)
axs[-1].set_xlim(2005,2025);axs[-1].set_xticks(range(2006,2025,2));axs[-1].set_xlabel('Documented event / account year')
fig.suptitle('    Contrasting documented pathways to PLC acceptance: California and Utah',fontsize=13)
fig.text(.08,.015,'California: documented evaluation-to-specification sequence. Utah: 2009 field experience and a separate 2023 supply-related decision account; no causal link inferred.',fontsize=8)
fig.tight_layout(rect=[0,.05,1,.94]);fig.savefig(out/'03_dot_case_pathways.png');plt.close(fig)

# Every original evidence row and its plot theme preserved for synthesis and review.
df[['state','agency','document_year','evidence_type','decision_factor','theme','documented_fact','source_title','source_url','interpretation_limit']].to_csv(out/'figure_source_index.csv',index=False)
print('Wrote 3 figures and figures/figure_source_index.csv')
