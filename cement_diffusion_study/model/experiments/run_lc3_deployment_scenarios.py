#!/usr/bin/env python3
"""Endogenous LC3 introduction and RMX uptake on the recorded PLC shipment network.

EXPLORATORY PLC-to-LC3 behavioral transfer, NOT validated LC3 forecast.
OPC/PLC/LC3 monthly shipment quantities are conserved on baseline supplier-RMX
links; 2024 demand and link totals are held fixed. Project candidates are assumed commissioned on their scenario dates;
other manufacturer introductions are endogenous. LC3 proportionally substitutes OPC and PLC on existing supplier-RMX links.
The proportional displacement rule is a transparent scenario assumption, not evidence.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

A0=-7.3300033902879465
AM=1.63628618303928
AP=0.22808233636341518
B0=-3.2474584986091823
BD=0.21484194767766054
BP=0.9471521955379223

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plc-output',type=Path,required=True)
    p.add_argument('--projects',type=Path,required=True)
    p.add_argument('--capacity-file',type=Path,required=True)
    p.add_argument('--peer-file',type=Path,required=True)
    p.add_argument('--mfr-peer-file',type=Path,required=True)
    p.add_argument('--baseline-month',default='2024-12')
    p.add_argument('--start',default='2025-01')
    p.add_argument('--end',default='2035-12')
    p.add_argument('--extra-plants',type=int,default=5)
    p.add_argument('--candidate-ceiling-fraction',type=float,default=1.)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not 0<a.candidate_ceiling_fraction<=1: p.error('candidate-ceiling-fraction must be in (0,1]')
    a.out.mkdir(parents=True,exist_ok=True)
    f=pd.read_csv(a.plc_output/'manufacturer_rmx_shipments.csv',dtype={'mfr_src_id':str,'rmx_src_id':str})
    f=f[f.yyyy_mm==a.baseline_month].copy()
    if f.empty: raise ValueError('Missing baseline shipments')
    f=f.groupby(['mfr_src_id','rmx_src_id','material'],as_index=False).tons.sum()
    if not set(f.material).issubset({'OPC','PLC'}): raise ValueError('Expected OPC/PLC baseline shipments')
    r=pd.read_csv(a.plc_output/'rmx_monthly_states.csv',dtype={'rmx_src_id':str})
    r=r[r.yyyy_mm==a.baseline_month].copy()
    if r.empty: raise ValueError('Missing baseline RMX records')
    caps=pd.read_csv(a.capacity_file,dtype={'mfr_src_id':str}).set_index('mfr_src_id').capacity_tpm_model.astype(float)
    caps=caps[caps.notna()&(caps>0)]
    proj=pd.read_csv(a.projects,dtype={'mfr_src_id':str})
    for col in ['mfr_src_id','lc3_ceiling_tpm']:
        if col not in proj: raise ValueError('Project CSV missing '+col)
    if 'activation_month' not in proj.columns: raise ValueError('Project CSV requires activation_month for conditional commissioning')
    proj=proj.drop_duplicates('mfr_src_id')
    for date in proj.activation_month:
        try: pd.Period(str(date),freq='M')
        except Exception as exc: raise ValueError(f'Invalid project activation_month: {date}') from exc
    if not set(proj.mfr_src_id).issubset(set(caps.index)): raise ValueError('Unknown project plant')
    rids=r.rmx_src_id.astype(str).tolist(); ridx={v:i for i,v in enumerate(rids)}
    mids=sorted(set(f.mfr_src_id)&set(caps.index)); midx={v:i for i,v in enumerate(mids)}
    f=f[f.mfr_src_id.isin(mids)&f.rmx_src_id.isin(ridx)].copy()
    # Each baseline shipment is a fixed supplier-specific material ledger entry.
    i=f.rmx_src_id.map(ridx).to_numpy(int); j=f.mfr_src_id.map(midx).to_numpy(int)
    plc=(f.material=='PLC').to_numpy(); opc=(f.material=='OPC').to_numpy()
    qty=f.tons.to_numpy(float)
    base_plc=np.where(plc,qty,0.); base_opc=np.where(opc,qty,0.)
    baseline_total=qty.sum()
    if baseline_total<=0: raise ValueError('No baseline shipments')
    plant_capacity=caps.reindex(mids).to_numpy(float)
    base_production=np.bincount(j,weights=qty,minlength=len(mids))
    if np.any(base_production>plant_capacity+1e-3): raise ValueError('Baseline plant production exceeds capacity')
    # Use real peer pairs; handle either peer_src_id or peer_rmx_src_id.
    rp=pd.read_csv(a.peer_file,dtype=str)
    rc=next((c for c in ['peer_rmx_src_id','peer_src_id','rmx_peer_src_id'] if c in rp),None)
    if rc is None or 'rmx_src_id' not in rp: raise ValueError('RMX peer columns not recognized')
    ri=np.array([ridx[x] for x in rp.rmx_src_id if x in ridx],dtype=int)
    rp=rp[rp.rmx_src_id.isin(ridx)&rp[rc].isin(ridx)]
    rsrc=rp.rmx_src_id.map(ridx).to_numpy(int); rdst=rp[rc].map(ridx).to_numpy(int)
    mp=pd.read_csv(a.mfr_peer_file,dtype=str)
    mc=next((c for c in ['peer_mfr_src_id','peer_src_id','mfr_peer_src_id'] if c in mp),None)
    if mc is None or 'mfr_src_id' not in mp: raise ValueError('Manufacturer peer columns not recognized')
    mp=mp[mp.mfr_src_id.isin(midx)&mp[mc].isin(midx)]
    msrc=mp.mfr_src_id.map(midx).to_numpy(int); mdst=mp[mc].map(midx).to_numpy(int)
    # Candidates ranked by existing PLC shipments, not assumed LC3 feasibility.
    plc_by_plant=np.bincount(j,weights=base_plc,minlength=len(mids))
    project_ids=set(proj.mfr_src_id)
    ranked=sorted([x for x in mids if x not in project_ids],key=lambda x:(-min(plc_by_plant[midx[x]],float(caps[x])*a.candidate_ceiling_fraction),x))
    selected=ranked[:a.extra_plants]
    scenarios={'project_candidates':set(project_ids),'projects_plus_optimized':set(project_ids)|set(selected),'full_network':set(mids)}
    project_ceiling=dict(zip(proj.mfr_src_id,pd.to_numeric(proj.lc3_ceiling_tpm,errors='raise')))
    project_dates=dict(zip(proj.mfr_src_id,proj.activation_month.astype(str)))
    if any(x not in midx for x in project_ids): raise ValueError('Project candidate missing from baseline manufacturer network')
    # DOT: NO verified LC3 eligibility data here. This is an all-eligible scenario.
    state=r.state.to_numpy(); demand=r.D_i.to_numpy(float)
    if np.any(np.bincount(i,weights=qty,minlength=len(r))>demand+1e-3): raise ValueError('Baseline shipments exceed RMX demand')
    # Monthly accessible market exposure: count each RMX only once per manufacturer.
    unique=f[['mfr_src_id','rmx_src_id']].drop_duplicates()
    ui=unique.rmx_src_id.map(ridx).to_numpy(int); uj=unique.mfr_src_id.map(midx).to_numpy(int)
    access=np.bincount(uj,weights=demand[ui],minlength=len(mids))
    baseline_ratio=np.divide(access,plant_capacity,out=np.zeros(len(mids)),where=plant_capacity>0)
    # Project records are eligibility evidence, NOT verified commissioning.
    # Their identifiers and capacity ceilings are preserved without forcing adoption.
    project_audit=proj.copy()
    project_audit['baseline_plc_tons']=[plc_by_plant[midx[x]] if x in midx else 0. for x in project_audit.mfr_src_id]
    project_audit['has_baseline_plc_shipments']=project_audit.baseline_plc_tons>0
    project_audit['eligible_in_network']=project_audit.mfr_src_id.isin(mids)
    project_audit.to_csv(a.out/'project_candidate_diagnostics.csv',index=False)
    dates=pd.period_range(a.start,a.end,freq='M').astype(str)
    national=[]; states=[]; events=[]; shipments=[]; diagnostics=[]; commissioning_events=[]
    for scenario,eligible_ids in scenarios.items():
        eligible=np.array([x in eligible_ids for x in mids],bool)
        ceiling=np.array([min(float(caps[x]),float(project_ceiling.get(x,float(caps[x])*a.candidate_ceiling_fraction))) if x in eligible_ids else 0. for x in mids])
        active=np.zeros(len(mids),bool)
        adoption=np.zeros(len(r),bool)
        rng=np.random.default_rng(a.seed)
        for ym in dates:
            # Manufacturer decisions: historical PLC equation transferred to LC3.
            prev_active=active.copy()
            peer_count=np.bincount(msrc,minlength=len(mids))
            peer_sum=np.bincount(msrc,weights=prev_active[mdst].astype(float),minlength=len(mids))
            peer=np.divide(peer_sum,peer_count,out=np.zeros(len(mids)),where=peer_count>0)
            # Existing accessible cement market is the opportunity for initial
            # manufacturer introduction; no prior LC3 adopter is required.
            # Track realized LC3-adopter demand separately for diagnostics.
            adopted_access=np.bincount(uj,weights=demand[ui]*adoption[ui],minlength=len(mids))
            ratio=np.divide(adopted_access,plant_capacity,out=np.zeros(len(mids)),where=plant_capacity>0)
            z=np.clip(A0+AM*np.log1p(baseline_ratio)+AP*peer,-35,35)
            probability=1/(1+np.exp(-z))
            # CONDITIONAL PROJECT REALIZATION, not observed commissioning.
            # Only project candidates activate at their input scenario month.
            # Nonproject manufacturers still use stochastic behavioral decisions.
            commissioned=np.array([x in project_ids and ym>=project_dates[x] for x in mids],bool)&eligible&(~active)
            newly=eligible&(~active)&(~np.array([x in project_ids for x in mids],bool))&(rng.random(len(mids))<probability)
            active|=(newly|commissioned)
            for k in np.flatnonzero(commissioned):
                commissioning_events.append((scenario,ym,mids[k],'ASSUMED_PROJECT_COMMISSIONING_NOT_VERIFIED'))
                events.append((scenario,ym,mids[k],float('nan'),float(baseline_ratio[k]),float(peer[k])))
            for k in np.flatnonzero(newly): events.append((scenario,ym,mids[k],float(probability[k]),float(baseline_ratio[k]),float(peer[k])))
            # RMX procurement: persistent endogenous binary adoption, based on
            # prior-month LC3 adoption among its actual peers.
            reachable=np.bincount(i,weights=(active[j]&(qty>0)).astype(float),minlength=len(r))>0
            prev=adoption.copy()
            rcount=np.bincount(rsrc,minlength=len(r))
            rsum=np.bincount(rsrc,weights=prev[rdst].astype(float),minlength=len(r))
            rpeer=np.divide(rsum,rcount,out=np.zeros(len(r)),where=rcount>0)
            rz=np.clip(B0+BD*1.+BP*rpeer,-35,35)
            rp_prob=1/(1+np.exp(-rz))
            adoption|=reachable&(~adoption)&(rng.random(len(r))<rp_prob)
            # Proportional OPC/PLC displacement on each existing supplier-RMX link.
            # This is a scenario allocation rule, NOT an empirically established
            # preference for replacing OPC versus PLC. Total deliveries stay fixed.
            allowed=active[j]&adoption[i]&(qty>0)
            candidate=np.where(allowed,qty,0.)
            potential=np.bincount(j,weights=candidate,minlength=len(mids))
            scale=np.divide(ceiling,potential,out=np.zeros(len(mids)),where=potential>0)
            lc3=np.minimum(1.,scale[j])*candidate
            remaining_plc=base_plc-np.where(plc,lc3,0.)
            remaining_opc=base_opc-np.where(opc,lc3,0.)
            if np.any(remaining_plc< -1e-6) or np.any(remaining_opc< -1e-6):
                raise RuntimeError('Negative OPC or PLC')
            if abs((lc3+remaining_plc+remaining_opc).sum()-baseline_total)>1e-5: raise RuntimeError('Mass balance failed')
            if np.any(np.bincount(j,weights=lc3+remaining_plc+remaining_opc,minlength=len(mids))>plant_capacity+1e-3): raise RuntimeError('Capacity exceeded')
            totals=np.array([remaining_opc.sum(),remaining_plc.sum(),lc3.sum()])
            national.append((scenario,ym,*totals,totals[2]/baseline_total,int(active.sum()),int(adoption.sum())))
            for k in np.flatnonzero(eligible):
                diagnostics.append((scenario,ym,mids[k],int(active[k]),float(probability[k]),
                                    float(baseline_ratio[k]),float(ratio[k]),float(peer[k]),
                                    float(plc_by_plant[k]),float(ceiling[k])))
            for st in np.unique(state):
                mask=(state[i]==st)
                op,pl,lc=remaining_opc[mask].sum(),remaining_plc[mask].sum(),lc3[mask].sum()
                states.append((scenario,ym,st,op,pl,lc,lc/(op+pl+lc) if op+pl+lc else 0.))
            # Shipment-level output at final month only (all materials).
            if ym==dates[-1]:
                for k in range(len(f)):
                    for mat,v in [('OPC',remaining_opc[k]),('PLC',remaining_plc[k]),('LC3',lc3[k])]:
                        if v>1e-9: shipments.append((scenario,ym,mids[j[k]],rids[i[k]],mat,float(v)))
    n=pd.DataFrame(national,columns=['scenario','yyyy_mm','opc_tons','plc_tons','lc3_tons','lc3_share','active_manufacturers','adopting_rmx'])
    n.to_csv(a.out/'national_lc3_endogenous.csv',index=False)
    pd.DataFrame(states,columns=['scenario','yyyy_mm','state','opc_tons','plc_tons','lc3_tons','lc3_share']).to_csv(a.out/'state_lc3_endogenous.csv',index=False)
    pd.DataFrame(events,columns=['scenario','yyyy_mm','mfr_src_id','introduction_probability','accessible_market_capacity_ratio','peer_active_share']).to_csv(a.out/'manufacturer_introduction_events.csv',index=False)
    pd.DataFrame(commissioning_events,columns=['scenario','yyyy_mm','mfr_src_id','assumption_status']).to_csv(a.out/'assumed_project_commissioning_events.csv',index=False)
    pd.DataFrame(diagnostics,columns=['scenario','yyyy_mm','mfr_src_id','active','introduction_probability','baseline_accessible_market_capacity_ratio','adopted_customer_demand_capacity_ratio','peer_active_share','baseline_plc_tons','lc3_ceiling_tpm']).to_csv(a.out/'manufacturer_monthly_diagnostics.csv',index=False)
    pd.DataFrame(shipments,columns=['scenario','yyyy_mm','mfr_src_id','rmx_src_id','material','tons']).to_csv(a.out/'manufacturer_rmx_shipments_2035.csv',index=False)
    pd.DataFrame({'mfr_src_id':selected,'baseline_plc_tons':[plc_by_plant[midx[x]] for x in selected]}).to_csv(a.out/'selected_additional_manufacturers.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,5.5))
    for scenario,label in [('project_candidates','Project candidates'),('projects_plus_optimized','Projects + 5 selected plants'),('full_network','Full network eligible')]:
        q=n[n.scenario==scenario]
        ax.plot(pd.to_datetime(q.yyyy_mm+'-01'),100*q.lc3_share,label=label,lw=2)
    ax.set(xlabel='Year',ylabel='LC3 share of delivered cement (%)',title='Conditional project commissioning and endogenous LC3 procurement')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(a.out/'figure_endogenous_lc3_2035.png',dpi=200);plt.close(fig)
    print(n[n.yyyy_mm==a.end][['scenario','lc3_share','active_manufacturers','adopting_rmx']].to_string(index=False))
    print('CAUTION: 2024 supplier links and total quantities frozen; LC3 proportionally replaces OPC and PLC; all states assumed eligible; PLC coefficients are unvalidated LC3 transfer hypotheses.')
    print('CONDITIONAL SCENARIO: project plants are ASSUMED commissioned at project CSV activation_month; NOT verified operating facilities.')
    print('Additional manufacturer introductions and RMX adoption are endogenous; project commissioning is exogenous.')
    print('Manufacturer introduction uses baseline accessible demand; prior-month RMX adoption is diagnostic only. Project commissioning is imposed as a counterfactual assumption, not inferred evidence.')
if __name__=='__main__':main()
