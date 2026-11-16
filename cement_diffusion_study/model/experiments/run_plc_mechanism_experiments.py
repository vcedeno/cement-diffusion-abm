#!/usr/bin/env python3
"""Run one-factor PLC mechanism experiments without modifying the simulator.
Run from the cement-diffusion-abm repository root. Requires pandas/matplotlib.
"""
import argparse, csv, json, subprocess, sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = dict(mfr_alpha0=-7.3300033902879465, mfr_alpha_market=1.63628618303928,
            mfr_alpha_peer=0.22808233636341518, rmx_beta0=-3.2474584986091823,
            rmx_beta_dot=0.21484194767766054, rmx_beta_peer=0.9471521955379223)
FLAGS = {'mfr_alpha0':'--mfr-alpha0','mfr_alpha_market':'--mfr-alpha-market',
         'mfr_alpha_peer':'--mfr-alpha-peer','rmx_beta0':'--rmx-beta0',
         'rmx_beta_dot':'--rmx-beta-dot','rmx_beta_peer':'--rmx-beta-peer'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='outputs/simple_abm/PLC_mechanism_experiments')
    ap.add_argument('--seeds',type=int,nargs='+',default=[42])
    ap.add_argument('--states',nargs='+',default=['FL','NC','VA'])
    ap.add_argument('--skip-existing',action='store_true')
    a=ap.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=True)
    sim=Path('model/cement_diffusion_model.py')
    files=[sim,Path('data/plc/01_observed_inputs'),Path('data/mfr_capacity_for_model.csv'),
           Path('data/plc/01_observed_inputs/mfr_plc_evidence_constraints_prospective_corrected.csv'),
           Path('data/usgs_all_state_type_month.csv'),Path('data/plc/01_observed_inputs/rmx_peer_pairs.csv'),
           Path('data/plc/01_observed_inputs/mfr_peer_pairs.csv')]
    missing=[str(p) for p in files if not p.exists()]
    if missing:sys.exit('Missing inputs:\n'+'\n'.join(missing))
    scenarios={'baseline':({},True),
       'no_mfr_peer':({'mfr_alpha_peer':0},True),
       'no_rmx_peer':({'rmx_beta_peer':0},True),
       'no_dot_response':({'rmx_beta_dot':0},True),
       'no_mfr_market_response':({'mfr_alpha_market':0},True),
       'no_corporate_priority':({},False)}
    # One-at-a-time coefficient perturbations: illustrative sensitivity, NOT recalibration.
    for key in BASE:
        for factor in (0.5,1.5):
            scenarios[f'{key}_x{str(factor).replace(".","p")}']=({key:BASE[key]*factor},True)
    manifest=[]
    for name,(overrides,corporate) in scenarios.items():
        coeff=BASE|overrides
        for seed in a.seeds:
            dest=root/name/f'seed_{seed}'
            national=dest/'national_month_market_share.csv'
            if a.skip_existing and national.exists():
                print('SKIP',name,seed,flush=True)
            else:
                dest.mkdir(parents=True,exist_ok=True)
                cmd=[sys.executable,str(sim),'--empirical-dir','data/plc/01_observed_inputs',
                     '--capacity-file','data/mfr_capacity_for_model.csv',
                     '--evidence-file','data/plc/01_observed_inputs/mfr_plc_evidence_constraints_prospective_corrected.csv',
                     '--observed','data/usgs_all_state_type_month.csv',
                     '--rmx-peer-file','data/plc/01_observed_inputs/rmx_peer_pairs.csv',
                     '--mfr-peer-file','data/plc/01_observed_inputs/mfr_peer_pairs.csv',
                     '--start','2010-01','--end','2024-12','--seed',str(seed),
                     '--availability','unresolved_possible','--integrated-behavior',
                     '--endogenous-network-capability','--future-exogs','provided_scenario',
                     '--production-policy','opc_first','--announced-conversion-strategy',
                     '--out',str(dest)]
                if corporate:cmd.append('--corporate-rollout-scenario')
                for key,value in coeff.items():cmd.extend([FLAGS[key],str(value)])
                (dest/'batch_command.json').write_text(json.dumps(cmd,indent=2))
                print('RUN',name,seed,flush=True)
                with (dest/'batch_run.log').open('w') as log:
                    subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
            manifest.append(dict(scenario=name,seed=seed,corporate_rollout=corporate,**coeff))
    pd.DataFrame(manifest).to_csv(root/'scenario_manifest.csv',index=False)
    curves=[];state_curves=[]
    for row in manifest:
        name=row['scenario'];seed=row['seed'];dest=root/name/f'seed_{seed}'
        n=pd.read_csv(dest/'national_month_market_share.csv');n['scenario']=name;n['seed']=seed;curves.append(n)
        s=pd.read_csv(dest/'state_month_market_share.csv');s['scenario']=name;s['seed']=seed
        state_curves.append(s[s.state.isin(a.states)])
    n=pd.concat(curves,ignore_index=True);s=pd.concat(state_curves,ignore_index=True)
    n.to_csv(root/'national_all_scenarios.csv',index=False)
    s.to_csv(root/'selected_states_all_scenarios.csv',index=False)
    final=n[n.yyyy_mm=='2024-12'][['scenario','seed','market_share']].rename(columns={'market_share':'share_2024_12'})
    base=final[final.scenario=='baseline'][['seed','share_2024_12']].rename(columns={'share_2024_12':'baseline_share'})
    summary=final.merge(base,on='seed');summary['delta_percentage_points']=100*(summary.share_2024_12-summary.baseline_share)
    summary.to_csv(root/'effect_summary_2024.csv',index=False)
    # A separate comparison plot per intervention, with identical seed and unaltered baseline.
    for name in scenarios:
        if name=='baseline':continue
        fig,ax=plt.subplots(figsize=(10,4.7))
        for label,style in [('baseline',dict(color='black',linewidth=2.1)),(name,dict(color='tab:red',linewidth=2.1))]:
            subset=n[(n.scenario==label)&(n.seed==a.seeds[0])].sort_values('yyyy_mm')
            ax.plot(pd.to_datetime(subset.yyyy_mm),100*subset.market_share,label=label.replace('_',' '),**style)
        ax.axvspan(pd.Timestamp('2023-01-01'),pd.Timestamp('2024-12-31'),color='0.9',alpha=0.8)
        ax.set(xlabel='Year',ylabel='Simulated PLC market share (%)',title=name.replace('_',' '))
        ax.legend(frameon=False);fig.tight_layout()
        fig.savefig(root/f'national_{name}.png',dpi=180);plt.close(fig)
        fig,axs=plt.subplots(len(a.states),1,figsize=(10,2.8*len(a.states)),sharex=True,squeeze=False)
        for ax,state in zip(axs[:,0],a.states):
            for label,color in [('baseline','black'),(name,'tab:red')]:
                sub=s[(s.scenario==label)&(s.seed==a.seeds[0])&(s.state==state)].sort_values('yyyy_mm')
                ax.plot(pd.to_datetime(sub.yyyy_mm),100*sub.market_share,label=label.replace('_',' '),color=color)
            ax.set(ylabel=f'{state} PLC share (%)');ax.axvspan(pd.Timestamp('2023-01-01'),pd.Timestamp('2024-12-31'),color='0.9',alpha=0.8)
        axs[0,0].legend(frameon=False);axs[-1,0].set_xlabel('Year');fig.tight_layout()
        fig.savefig(root/f'states_{name}.png',dpi=180);plt.close(fig)
    print('COMPLETE:',root.resolve())
    print(summary.groupby('scenario').delta_percentage_points.mean().sort_values(key=abs,ascending=False).to_string())
if __name__=='__main__':main()
