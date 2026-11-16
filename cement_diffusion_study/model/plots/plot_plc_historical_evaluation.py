#!/usr/bin/env python3
"""Publication Figure 1, 2010–2024. Read-only; requires the SAME simulation for every panel.
Run from repository root. 2023–24 USGS values come from the raw USGS file,
not the development-only comparison file. Optional production-strategy comparison and seed ranges; no invented uncertainty.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle

P=argparse.ArgumentParser()
P.add_argument('--run',type=Path,default=Path('outputs/simple_abm/PLC_aggressive_corporate_rollout'))
P.add_argument('--calibrated-run',type=Path,default=None)
P.add_argument('--usgs',type=Path,default=Path('data/usgs_all_state_type_month.csv'))
P.add_argument('--states',nargs=3,default=['FL','NC','VA'])
P.add_argument('--without-run',type=Path,default=None,help='Accepted for compatibility but not plotted in Figure 1')
P.add_argument('--seed-runs',type=Path,nargs='*',default=[],help='Two or more completed stronger-response runs differing only in random seed')

P.add_argument('--out',type=Path,default=Path('outputs/simple_abm/PLC_frozen_reference/Figure_1'))
a=P.parse_args()

def load(name,cols):
 f=a.run/name
 if not f.exists():raise SystemExit(f'Missing {f}. Use the completed reference run (no rerun needed).')
 d=pd.read_csv(f)
 miss=set(cols)-set(d.columns)
 if miss:raise SystemExit(f'{f}: missing {sorted(miss)}')
 d['date']=pd.to_datetime(d.yyyy_mm.astype(str),format='%Y-%m')
 return d

state=load('state_month_market_share.csv',['yyyy_mm','state','market_share','material_tons','delivered_tons'])
mfr_name=next((n for n in ['mfr_monthly_states.csv','E18_manufacturer_monthly_states.csv'] if (a.run/n).exists()),None)
if mfr_name is None:raise SystemExit('Missing manufacturer monthly states in '+str(a.run))
mfr=load(mfr_name,['yyyy_mm','mfr_src_id','operating','scenario_capable','material_tons','opc_tons'])
rmx=load('rmx_monthly_states.csv',['yyyy_mm','rmx_src_id','material_tons'])
if not a.usgs.exists():raise SystemExit(f'Missing raw USGS data: {a.usgs}')
u=pd.read_csv(a.usgs)
for c in ['STATE','YYYY_MM','TYPE','TONS']:
 if c not in u:raise SystemExit('USGS file missing '+c)
# Explicit state names to prevent silent joins/missing states.
state_names=dict(zip(
 ['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'],
 ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']))
u['state']=u.STATE.map(state_names)
u=u[u.state.notna() & u.TYPE.isin(['Blended','Portland'])].copy()
u['TONS']=pd.to_numeric(u.TONS,errors='coerce')
u=u.pivot_table(index=['YYYY_MM','state'],columns='TYPE',values='TONS',aggfunc='sum').reset_index()
u['observed']=u['Blended']/(u['Blended']+u['Portland'])
u['date']=pd.to_datetime(u.YYYY_MM,format='%Y-%m')
# Only aggregate states simulated by the model. No filling missing observations.
covered=sorted(state.state.unique())
obs=u[u.state.isin(covered)].copy()
obs_nat=obs.groupby('date')[['Blended','Portland']].sum(min_count=1)
obs_nat['share']=obs_nat.Blended/(obs_nat.Blended+obs_nat.Portland)
# Validate 2023–24 are genuinely present, not blank values.
if obs_nat.loc['2023-01-01':'2024-12-01','share'].notna().sum()!=24:
 raise SystemExit('Raw USGS observations do not cover all 24 evaluation months.')
# Validate state totals against manufacturer production, using full time series.
by_state=state.groupby('date')[['material_tons','delivered_tons']].sum()
by_mfr=mfr.groupby('date')['material_tons'].sum()
common=by_state.index.intersection(by_mfr.index)
rel=((by_state.loc[common,'material_tons']-by_mfr.loc[common]).abs()/by_mfr.loc[common].clip(lower=1)).max()
if rel>1e-5:raise SystemExit(f'ERROR: state PLC totals do not reconcile with manufacturer output (max relative difference {rel:.2%}). Do not mix runs.')
# Optional comparison specifications and seed runs use their own completed state-level flows.
def scenario_share(folder):
    f=folder/'state_month_market_share.csv'
    if not f.exists():raise SystemExit(f'Missing scenario file: {f}')
    d=pd.read_csv(f)
    required={'yyyy_mm','state','material_tons','delivered_tons'}
    if not required.issubset(d.columns):raise SystemExit(f'{f} missing {required-set(d.columns)}')
    d['date']=pd.to_datetime(d.yyyy_mm.astype(str),format='%Y-%m')
    d=d[d.state.isin(covered)]
    g=d.groupby('date')[['material_tons','delivered_tons']].sum()
    if g.index.min()>pd.Timestamp('2010-01-01') or g.index.max()<pd.Timestamp('2024-12-01'):
        raise SystemExit(f'{f} does not span 2010–2024')
    if (g.delivered_tons<=0).any():raise SystemExit(f'{f} has zero deliveries')
    return 100*g.material_tons/g.delivered_tons

without=None  # Mechanism ablation is intentionally excluded from Figure 1.
calibrated=scenario_share(a.calibrated_run) if a.calibrated_run else None
seed_shares=[]
for folder in a.seed_runs:
    seed_shares.append(scenario_share(folder).rename(str(folder)))
if len(seed_shares)==1:raise SystemExit('Ranges need at least TWO independent seed runs; one is not a range.')
if len({str(f.resolve()) for f in a.seed_runs})!=len(a.seed_runs):raise SystemExit('Duplicate seed directories are not independent runs.')
if seed_shares:
    ensemble=pd.concat(seed_shares,axis=1,join='inner')
    if len(ensemble)<180:raise SystemExit('Seed series do not cover all 180 months.')
    seed_low=ensemble.min(axis=1)
    seed_high=ensemble.max(axis=1)

# Per-state envelopes from the same frozen configuration, not alternative calibrations.
# The shaded envelopes are min–max across supplied seed runs, NOT confidence intervals.
state_envelopes={}
if seed_shares:
 for st in a.states:
  columns=[]
  for folder in a.seed_runs:
   df=pd.read_csv(folder/'state_month_market_share.csv')
   df=df[df.state==st].copy()
   df['date']=pd.to_datetime(df.yyyy_mm.astype(str),format='%Y-%m')
   df=df.set_index('date').sort_index()
   if 'market_share' in df.columns:series=100*df.market_share
   else:series=100*df.material_tons/df.delivered_tons.replace(0,np.nan)
   columns.append(series.rename(str(folder)))
  e=pd.concat(columns,axis=1,join='inner').sort_index()
  if len(e)<180:raise SystemExit(f'Seed runs missing months for {st}')
  state_envelopes[st]=(e.min(axis=1),e.max(axis=1))
state['share']=100*state.market_share
obs['share']=100*obs.observed
nat=(by_state.material_tons/by_state.delivered_tons*100)
capable=mfr.assign(is_capable=(mfr.operating>0)&(mfr.scenario_capable>0)).groupby('date').is_capable.sum()
receiving=rmx.assign(receives=rmx.material_tons>1e-9).groupby('date').receives.sum()
production=mfr.groupby('date')[['material_tons','opc_tons']].sum()/1e6

# Choose states explicitly; do not imply selected examples represent all states.
for s in a.states:
 if s not in covered:raise SystemExit(f'State {s} absent from simulation.')
 if obs[(obs.state==s)&(obs.date>='2023-01-01')].share.notna().sum()<20:
  raise SystemExit(f'Insufficient evaluation USGS observations for {s}.')

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
fig=plt.figure(figsize=(15.8,12.2),layout='constrained')
grid=fig.add_gridspec(3,2,height_ratios=[1.05,1.55,1.08],hspace=.10)
axA=fig.add_subplot(grid[0,:])
axesB=[fig.add_subplot(grid[1,0].subgridspec(3,1,hspace=.10)[i,0]) for i in range(3)]
axesC=[fig.add_subplot(grid[1,1].subgridspec(3,1,hspace=.10)[i,0]) for i in range(3)]
map_grid=grid[2,:].subgridspec(2,3,height_ratios=[0.14,0.86],hspace=0.02,wspace=0.10)
map_heading=fig.add_subplot(map_grid[0,:]);map_heading.axis('off')
map_heading.text(0,0.5,'D   Simulated PLC market share by state (December)',ha='left',va='center',fontweight='bold',fontsize=10,transform=map_heading.transAxes)
axesD=[fig.add_subplot(map_grid[1,i]) for i in range(3)]

held=pd.Timestamp('2023-01-01');end=pd.Timestamp('2025-01-01')
red='#b21f36';blue='#2166ac';gray='#777777'
def decorate(ax,hide=False):
 ax.axvspan(held,end,color='#ededed',zorder=-5)
 ax.axvline(held,color='#777777',ls=':',lw=.9)
 ax.set_xlim(pd.Timestamp('2010-01-01'),pd.Timestamp('2024-12-01'))
 ax.xaxis.set_major_locator(mdates.YearLocator(2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
 if hide:ax.tick_params(axis='x',labelbottom=False)
 ax.grid(axis='y',alpha=.17)

axA.plot(obs_nat.index,100*obs_nat.share,color='black',lw=2,label='Observed blended-cement share (USGS; PLC proxy)')
axA.plot(nat.index,nat,color=red,ls='-.',lw=2.2,label='Simulated PLC market share')
if calibrated is not None:axA.plot(calibrated.index,calibrated,color=blue,lw=1.8,label='Calibrated PLC market share')
# The production-priority ablation belongs in the mechanism figure, not Figure 1.
if seed_shares:axA.fill_between(seed_low.index,seed_low.to_numpy(),seed_high.to_numpy(),color=red,alpha=.17,label=f'Simulation range ({len(seed_shares)} seeds; min–max)')
# Use one continuous monthly time axis through 2024, with identical year spacing
# in Panels A–C. Do not crop 2023–2024 or truncate observed values.
decorate(axA)
# Show development and held-out evaluation on the same national axis.
axA.set_ylim(bottom=0)
axA.set_ylabel(r'National PLC share, $y_{US}^{(m)}(t)$ (%)')
axA.set_title('A   National market share (2010–2024)',loc='left',fontweight='bold')
axA.legend(frameon=False,loc='upper left',ncol=2,fontsize=8)
for i,(s,ax) in enumerate(zip(a.states,axesB)):
 o=obs[obs.state==s].sort_values('date');d=state[state.state==s].sort_values('date')
 ax.plot(o.date,o.share,color='black',lw=1.6)
 ax.plot(d.date,d.share,color=red,ls='-.',lw=1.6)
 if s in state_envelopes:
  low,high=state_envelopes[s];ax.fill_between(low.index,low.to_numpy(),high.to_numpy(),color=red,alpha=.17)
 decorate(ax,hide=i<2);ax.text(.02,.84,s,transform=ax.transAxes,fontweight='bold')
 ax.set_ylabel(r'$y_s^{(m)}(t)$ (%)')
axesB[0].set_title('B   State market shares (Florida, North Carolina, Virginia)',loc='left',fontweight='bold')
axesC[0].plot(capable.index,capable,color=blue,lw=1.8)
axesC[1].plot(receiving.index,receiving,color='#16836b',lw=1.8)
axesC[2].plot(production.index,production.material_tons,color=red,lw=1.6,label='PLC')
axesC[2].plot(production.index,production.opc_tons,color=gray,lw=1.3,label='OPC (comparison)')
for i,ax in enumerate(axesC):decorate(ax,hide=i<2)
axesC[0].set_ylabel('Number of plants',fontsize=8,labelpad=5)
axesC[1].set_ylabel('Number of plants',fontsize=8,labelpad=5)
axesC[2].set_ylabel('Mt/month',fontsize=8,labelpad=5)
for ax,label in zip(axesC,['PLC-capable cement plants','Concrete plants receiving PLC','Cement production']):
 ax.text(0.015,0.91,label,transform=ax.transAxes,ha='left',va='top',fontsize=8,fontweight='medium',bbox=dict(facecolor='white',alpha=.8,edgecolor='none',pad=1.5))
 ax.tick_params(axis='y',labelsize=8)
axesC[0].set_title('C   Simulated cement plants, concrete producers, and production',loc='left',fontweight='bold')
# Keep the production legend clear of the in-panel heading and time series.
axesC[2].legend(frameon=False,loc='upper center',bbox_to_anchor=(0.65,1.01),
                ncol=2,fontsize=8,handlelength=1.8,columnspacing=1.0)
# Clearly identify the shaded evaluation interval on each time-series panel group.
for evaluation_ax in (axA, axesB[0], axesC[0]):
 evaluation_ax.text(pd.Timestamp('2023-12-01'), .94, 'Validation\n2023–2024',
                    transform=evaluation_ax.get_xaxis_transform(), ha='center',va='top',
                    fontsize=7.5,color='#555555',fontweight='bold',
                    bbox=dict(facecolor='#ededed',edgecolor='none',alpha=.85,pad=2))


# D. Geographic tile maps: simulated state shares for the SAME stronger-response
# scenario as the red curves in A and B. Tiles are schematic, not boundaries.
tiles = [
'AK:0:0','WA:0:1','MT:0:2','ND:0:3','MN:0:4','WI:0:5','MI:0:6','VT:0:9','ME:0:10',
'OR:1:1','ID:1:2','SD:1:3','IA:1:4','IL:1:5','IN:1:6','OH:1:7','PA:1:8','NY:1:9','NH:1:10',
'CA:2:1','NV:2:2','WY:2:3','NE:2:4','MO:2:5','KY:2:6','WV:2:7','VA:2:8','NJ:2:9','MA:2:10',
'AZ:3:2','UT:3:3','CO:3:4','KS:3:5','AR:3:6','TN:3:7','NC:3:8','MD:3:9','CT:3:10',
'HI:4:0','NM:4:3','OK:4:5','LA:4:6','MS:4:7','AL:4:8','SC:4:9','DE:4:10','RI:4:11',
'TX:5:4','GA:5:8','FL:5:9']
coords={part.split(':')[0]:(int(part.split(':')[1]),int(part.split(':')[2])) for part in tiles}
for ax,month in zip(axesD,['2018-12','2022-12','2024-12']):
 snap=state[state.yyyy_mm==month].set_index('state').market_share
 if snap.empty:raise SystemExit(f'Missing model state share for {month}')
 for st,(row,col) in coords.items():
  val=float(snap[st]) if st in snap and pd.notna(snap[st]) else np.nan
  face=plt.cm.YlOrRd(np.clip(val,0,1)) if np.isfinite(val) else '#ececec'
  ax.add_patch(Rectangle((col,row),.94,.94,facecolor=face,edgecolor='white',lw=.8))
  ax.text(col+.47,row+.47,st,ha='center',va='center',fontsize=6.5,
          color='white' if np.isfinite(val) and val>.70 else 'black')
 ax.set_xlim(-.2,12);ax.set_ylim(6.1,-.25);ax.set_aspect('equal');ax.axis('off')
 ax.set_title(month[:4],fontsize=10,fontweight='bold',pad=8)

sm=plt.cm.ScalarMappable(cmap='YlOrRd',norm=Normalize(0,100));sm.set_array([])
cb=fig.colorbar(sm,ax=axesD,location='bottom',fraction=.035,pad=.02,shrink=.58,aspect=35)
cb.set_label('Simulated PLC market share (%)')

# Framework-consistent labels: y_US^(m)(t), y_s^(m)(t), q_j^(m)(t), Q_j^(m)(t).
# Counts of receiving RMXs are descriptive diagnostics, not separately defined symbols.
# No overall figure title; panel headings provide context.
fig.supxlabel('Panels A–C show 2010–2022 model development and 2023–2024 out-of-sample validation (gray shading).\nUSGS blended-cement share is an imperfect PLC proxy. The red and blue simulations use different coefficient sets.',fontsize=8)
a.out.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(str(a.out)+'.png',dpi=250,bbox_inches='tight')
fig.savefig(str(a.out)+'.pdf',bbox_inches='tight')
plt.close(fig)
print('Saved',str(a.out)+'.png and .pdf')
print('Seed runs:',len(seed_shares),'(min–max; not a confidence interval)')
