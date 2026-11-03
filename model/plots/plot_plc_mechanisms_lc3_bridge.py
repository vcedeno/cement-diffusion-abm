#!/usr/bin/env python3
"""Two-panel PLC mechanisms figure connecting historical behavior to LC3 scenarios.
Run from the ABM repository root:
    python model/plots/plot_plc_mechanisms_lc3_bridge.py
Uses existing frozen simulation outputs. No simulation or calibration.
"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path('outputs/plc_final_2026')
BLUE, ORANGE, GREEN, GRAY = '#17647C', '#C07036', '#238263', '#333333'
plt.rcParams.update({'font.size':10,'axes.titlesize':11,'axes.spines.top':False,
                     'axes.spines.right':False,'pdf.fonttype':42})

def load_rmx(path):
    columns=['yyyy_mm','D_i','phi_s','r_i','x_i','a_i']
    df=pd.read_csv(path,usecols=columns)
    if df[columns].isna().any().any() or (df.D_i<=0).any():
        raise ValueError(f'Invalid RMX input: {path}')
    rows=[]
    for month,g in df.groupby('yyyy_mm',sort=True):
        w=g['D_i'].to_numpy()
        rows.append({'date':pd.Timestamp(month+'-01'),
                     **{k:np.average(g[k],weights=w) for k in ['phi_s','r_i','x_i','a_i']}})
    return pd.DataFrame(rows).set_index('date').sort_index().loc['2010':'2024']

def load_observed(path):
    if not path.exists():
        print(f'Observed USGS CSV not found ({path}); plotting simulations only.')
        return None
    usgs=pd.read_csv(path)
    required={'YYYY_MM','TYPE','TONS'}
    if not required.issubset(usgs.columns):
        raise ValueError(f'Expected USGS columns {required}; got {list(usgs.columns)}')
    usgs['TYPE']=usgs.TYPE.astype(str).str.strip().str.lower()
    wide=usgs.groupby(['YYYY_MM','TYPE']).TONS.sum().unstack(fill_value=0)
    if not {'blended','portland'}.issubset(wide.columns):
        raise ValueError('USGS data needs blended and portland categories')
    share=wide['blended']/(wide['blended']+wide['portland'])
    share.index=pd.to_datetime(share.index+'-01')
    return share.sort_index().loc['2010':'2024']

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--reference',type=Path,default=ROOT/'18_E01_controlled_corrected')
    p.add_argument('--no-response',type=Path,default=ROOT/'19_PLC02_B_historical_no_response')
    p.add_argument('--usgs',type=Path,default=Path('data/usgs_all_state_type_month.csv'))
    p.add_argument('--outdir',type=Path,default=ROOT/'figures_corrected')
    args=p.parse_args()
    ref=load_rmx(args.reference/'rmx_monthly_states.csv')
    no=load_rmx(args.no_response/'rmx_monthly_states.csv')
    if not ref.index.equals(no.index):
        raise ValueError('Scenario month indices do not match')
    obs=load_observed(args.usgs)
    fig,(a,b)=plt.subplots(2,1,figsize=(10.8,7.4),sharex=True,
                           gridspec_kw={'height_ratios':[1,1.1],'hspace':.24})
    # Descriptive reference-model mechanisms; not independent causal estimates.
    a.plot(ref.index,100*ref['phi_s'],color=ORANGE,lw=2.3,
           label=r'DOT implementation maturity $\overline{\phi}(t)$')
    a.plot(ref.index,100*ref['r_i'],color=GREEN,lw=2.3,
           label=r'Behavioral readiness $\overline{r}(t)$')
    a.plot(ref.index,100*ref['x_i'],color=BLUE,lw=2.3,
           label=r'Local PLC access $\overline{x}(t)$')
    a.set_title('(a) Regulatory readiness, behavioral response, and supply access',
                loc='left',fontweight='bold',pad=11)
    a.set_ylabel('Demand-weighted mean (%)')
    a.set_ylim(0,103)
    a.legend(loc='upper left',frameon=False,ncol=2,fontsize=9)

    # Controlled manufacturer-response ablation; not PLC-specific empirical validation.
    b.plot(ref.index,100*ref['a_i'],color=BLUE,lw=2.5,
           label='Simulated PLC adoption: response enabled')
    b.plot(no.index,100*no['a_i'],color=ORANGE,lw=2.5,
           label='Simulated PLC adoption: response disabled')
    if obs is not None:
        b.plot(obs.index,100*obs,color=GRAY,lw=1.9,ls=':',
               label='USGS blended-cement shipment share (broader benchmark)')
    b.set_title('(b) Manufacturer response and national PLC diffusion',
                loc='left',fontweight='bold',pad=11)
    b.set_ylabel('National share (%)')
    b.set_ylim(0,103)
    b.legend(loc='upper left',frameon=False,fontsize=8.8)
    for ax in (a,b):
        ax.set_xlim(pd.Timestamp('2010-01-01'),pd.Timestamp('2024-12-31'))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.grid(axis='y',alpha=.19)
    b.set_xlabel('Year')
    args.outdir.mkdir(parents=True,exist_ok=True)
    for ext in ('png','pdf'):
        output=args.outdir/f'plc_mechanisms_lc3_bridge.{ext}'
        fig.savefig(output,dpi=300,bbox_inches='tight',facecolor='white')
        print('Saved:',output)
    last=ref.index[-1]
    print(f'Dec 2024: DOT maturity {100*ref.loc[last,"phi_s"]:.2f}%, '
          f'behavioral readiness {100*ref.loc[last,"r_i"]:.2f}%, '
          f'local access {100*ref.loc[last,"x_i"]:.2f}%')
    print(f'Dec 2024 adoption: response enabled {100*ref.loc[last,"a_i"]:.2f}%, '
          f'disabled {100*no.loc[last,"a_i"]:.2f}% '
          f'(difference {100*(ref.loc[last,"a_i"]-no.loc[last,"a_i"]):+.2f} pp)')
    plt.close(fig)

if __name__=='__main__': main()
