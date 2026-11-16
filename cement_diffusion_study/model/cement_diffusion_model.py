#!/usr/bin/env python3
"""Locked simplified PLC structural model: evidence-bounded capability, exposure diagnostics, quantity-based utilization.

This is a STRUCTURAL SCENARIO, not a calibrated PLC model.
Manufacturer-led OPC withdrawal is allowed ONLY through explicit documented
product-offering records; PLC capability alone never establishes withdrawal.
Compare only 2010-2022 development outcomes.

Original description: One shared, quantity-based PLC/LC3 supply-network ABM.

Evidence-bounded scenario simulator, NOT a calibrated point forecast. No adoption
response period, manufacturer expansion delay, moving-window trigger, fitted
utilization fraction, or use of 2023-24 observations in model decisions.

Supply quantities are capacity-constrained and geographically routed; all
eligible demand is requested. Capacity is TOTAL cement capacity, so the
'full_capability' assumption is explicitly an upper-bound scenario, not an
estimate of observed PLC or LC3 output. Binary adoption is persistent and
records receipt of a positive amount of the material.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_csv(path, columns):
    p = Path(path)
    if not p.exists(): raise FileNotFoundError(p)
    d = pd.read_csv(p)
    missing = set(columns) - set(d.columns)
    if missing: raise ValueError(f'{p}: missing columns {sorted(missing)}')
    return d


def observed_shares(path):
    d = load_csv(path, ['YYYY_MM', 'STATE', 'TYPE', 'TONS'])
    d['yyyy_mm'] = d.YYYY_MM.astype(str).str[:7]
    # Convert USGS full state names to the two-letter codes used by the ABM.
    state_names = """
    Alabama:AL
    Alaska:AK
    Arizona:AZ
    Arkansas:AR
    California:CA
    Colorado:CO
    Connecticut:CT
    Delaware:DE
    Florida:FL
    Georgia:GA
    Hawaii:HI
    Idaho:ID
    Illinois:IL
    Indiana:IN
    Iowa:IA
    Kansas:KS
    Kentucky:KY
    Louisiana:LA
    Maine:ME
    Maryland:MD
    Massachusetts:MA
    Michigan:MI
    Minnesota:MN
    Mississippi:MS
    Missouri:MO
    Montana:MT
    Nebraska:NE
    Nevada:NV
    New Hampshire:NH
    New Jersey:NJ
    New Mexico:NM
    New York:NY
    North Carolina:NC
    North Dakota:ND
    Ohio:OH
    Oklahoma:OK
    Oregon:OR
    Pennsylvania:PA
    Rhode Island:RI
    South Carolina:SC
    South Dakota:SD
    Tennessee:TN
    Texas:TX
    Utah:UT
    Vermont:VT
    Virginia:VA
    Washington:WA
    West Virginia:WV
    Wisconsin:WI
        Wyoming:WY
    """

    state_map = dict(
        line.strip().split(":")
        for line in state_names.strip().splitlines()
    )

    d['state'] = d.STATE.astype(str).str.strip().replace(state_map)
    d['TONS'] = pd.to_numeric(d.TONS, errors='coerce')
    p = d.pivot_table(index=['yyyy_mm', 'state'], columns='TYPE', values='TONS', aggfunc='sum')
    if not {'Blended', 'Portland'}.issubset(p.columns):
        raise ValueError('USGS TYPE requires Blended and Portland')
    p = p[['Blended','Portland']].dropna().reset_index()
    p['total_tons'] = p.Blended + p.Portland
    p = p[p.total_tons > 0]
    p['observed_blended_share'] = p.Blended / p.total_tons
    return p[['yyyy_mm','state','observed_blended_share','total_tons']]


def allocate(demand, cap, edges, iterations=150, tolerance=1e-7, return_flows=False):
    """Lexicographic LP: maximize feasible deliveries, then minimize ton-miles.

    Each call respects a previously established material-priority tier.
    Distances are taken from the original MFR-RMX network, never fitted.
    """
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix
    ni,nj=len(demand),len(cap)
    delivered=np.zeros(ni); supplied=np.zeros(nj)
    if len(edges)==0 or not np.any(demand>0) or not np.any(cap>0):
        return (delivered,supplied,[]) if return_flows else (delivered,supplied)
    i,j=edges[:,0],edges[:,1]
    good=(demand[i]>1e-10)&(cap[j]>1e-10)
    i,j=i[good],j[good]
    if not len(i):return (delivered,supplied,[]) if return_flows else (delivered,supplied)
    distances=np.array([EDGE_DISTANCE[(int(a),int(b))] for a,b in zip(i,j)])
    cols=np.arange(len(i))
    A=coo_matrix((np.ones(2*len(i)),(np.r_[i,ni+j],np.r_[cols,cols])),
                 shape=(ni+nj,len(i))).tocsr()
    bounds=np.r_[demand,cap]
    first=linprog(-np.ones(len(i)),A_ub=A,b_ub=bounds,bounds=(0,None),method='highs')
    if not first.success:raise RuntimeError('Fulfillment LP: '+first.message)
    fulfilled=first.x.sum()
    # The first-stage optimum is enforced to solver tolerance, not traded
    # against transportation distance through an arbitrary cost weight.
    second=linprog(distances,A_ub=A,b_ub=bounds,A_eq=np.ones((1,len(i))),
                   b_eq=[fulfilled],bounds=(0,None),method='highs')
    if not second.success:raise RuntimeError('Distance LP: '+second.message)
    delivered=np.bincount(i,weights=second.x,minlength=ni)
    supplied=np.bincount(j,weights=second.x,minlength=nj)
    if np.any(delivered>demand+1e-4) or np.any(supplied>cap+1e-4):
        raise RuntimeError('Allocation conservation violation')
    flows=[(int(ri),int(mj),float(tons)) for ri,mj,tons in zip(i,j,second.x) if tons>1e-8]
    return (delivered,supplied,flows) if return_flows else (delivered,supplied)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--empirical-dir',type=Path,required=True)
    ap.add_argument('--rmx-peer-file',type=Path,help='Existing 20-mile RMX peer pairs; required')
    ap.add_argument('--mfr-peer-file',type=Path,help='Shared-market manufacturer peer pairs; required')
    ap.add_argument('--integrated-behavior',action='store_true',help='Enable explicitly hypothetical binary network-response rules')
    ap.add_argument('--capacity-file',type=Path,required=True)
    ap.add_argument('--evidence-file',type=Path,required=True)
    ap.add_argument('--material',choices=['PLC','LC3'],default='PLC')
    ap.add_argument('--manufacturer-economics',type=Path,
        help='Optional independently sourced plant economics: mfr_src_id,plc_incremental_margin_per_ton,annualized_retrofit_cost,source_basis. Required for endogenous retrofit decisions; missing rows stay unresolved.')
    ap.add_argument('--economic-retrofits',action='store_true',
        help='Enable deterministic break-even capability investment based on sourced economics, independent of RMX PLC adoption. Requires --manufacturer-economics.')
    ap.add_argument('--economic-production',action='store_true',
        help='Choose PLC-vs-OPC production priority from sourced incremental unit margins, not blanket producer_first. Requires --manufacturer-economics.')
    ap.add_argument('--capability-file',type=Path,help='LC3: CSV mfr_src_id,feasible_tpm (independently justified scenario ceiling)')
    ap.add_argument('--availability',choices=['documented_lower','unresolved_possible'],default='documented_lower',help='PLC evidence-consistent capability scenarios; neither is a historical reconstruction')
    ap.add_argument('--endogenous-network-capability',action='store_true',help='Enable endogenous transitions for plants explicitly feasible under the selected scenario; no historical transition dates inferred')
    ap.add_argument('--capability-feasibility',type=Path,help='Optional independent plant feasibility CSV: mfr_src_id,feasible,evidence_basis. Required for unknown plants to become eligible in conservative mode.')
    ap.add_argument('--observed',type=Path,required=True,help='USGS series, for AFTER-run evaluation only; never used in model decisions')
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--start',default='2010-01')
    ap.add_argument('--end',default='2024-12')
    ap.add_argument('--evaluate-heldout',action='store_true',help='Explicitly unlock 2023-24 outcome comparison ONLY after model specification is frozen; viewing and revising forfeits independent validation')
    ap.add_argument('--production-policy',choices=['producer_first','opc_first'],default='opc_first',help='Structural scenario: capable producers offer PLC first, or OPC first; neither is empirically identified')
    ap.add_argument('--corporate-rollout-scenario',action='store_true',help='Aggressive hypothetical company-wide PLC-first strategy from earliest dated company plant announcement; NOT evidence of other plants converting.')
    ap.add_argument('--announced-conversion-strategy',action='store_true',help='Scenario: PLC-first priority only at plants with pre-2023 dated announcements of full conversion, from announcement month; does NOT assert actual completion or PLC-only offering.')
    ap.add_argument('--future-exogs',choices=['freeze_2022','provided_scenario'],default='freeze_2022',help='Forecast: freeze 2022-12 inputs, or use predeclared post-2022 exogenous scenario rows; never use USGS outcomes')
    ap.add_argument('--seed',type=int,default=42,help='Random seed for manufacturer transition draws')
    ap.add_argument('--mfr-alpha0',type=float,default=-9.0,help='Illustrative monthly introduction log-odds; NOT calibrated')
    ap.add_argument('--mfr-alpha-market',type=float,default=1.0,help='Coefficient on log1p(accessible monthly market / plant monthly capacity); NOT calibrated')
    ap.add_argument('--mfr-alpha-peer',type=float,default=2.0,help='Coefficient on prior-month offering share of overlapping-market manufacturers; NOT calibrated')
    ap.add_argument('--rmx-beta0',type=float,default=-2.0,help='Illustrative baseline PLC procurement log-odds; NOT calibrated')
    ap.add_argument('--rmx-beta-dot',type=float,default=1.0,help='Illustrative DOT acceptance influence; NOT calibrated')
    ap.add_argument('--rmx-beta-peer',type=float,default=2.0,help='Illustrative local peer PLC utilization influence; NOT calibrated')
    ap.add_argument('--mfr-base-hazard',type=float,default=0.0,help='DEPRECATED: must be zero; unsupported hazard removed')
    ap.add_argument('--mfr-peer-effect',type=float,default=0.0,help='DEPRECATED: must be zero; unsupported peer hazard removed')
    ap.add_argument('--manufacturer-offerings',type=Path,help='Source-backed monthly offering observations: yyyy_mm,mfr_src_id,offering (OPC_only,both,PLC_only,PLC_primary),evidence_basis. PLC_primary means PLC is documented as primary product, not sole product.')
    ap.add_argument('--rmx-material-constraints',type=Path,help='Optional documented hard OPC requirements: yyyy_mm,rmx_src_id,opc_required_tons,evidence_basis; unspecified compatibility remains unknown, not proven PLC-compatible')
    ap.add_argument('--rmx-requirements',type=Path,help='Optional independently supported monthly RMX PLC requirements: yyyy_mm,rmx_src_id,plc_required_tons,evidence_basis')
    ap.add_argument('--manufacturer-led', action='store_true', help='Legacy E02 flag; E03 rejects automatic OPC withdrawal. Use evidence-backed --manufacturer-offerings instead.')
    ap.add_argument('--rmx-initiated', action='store_true', help='Enable RMX-initiated PLC requests only where --rmx-requirements supplies independently supported quantities; DOT acceptance alone never generates orders.')
    ap.add_argument('--rmx-adoption-events',type=Path,help='Documented operational qualification: yyyy_mm,rmx_src_id,evidence_basis; persistent after event')
    a=ap.parse_args()
    if a.integrated_behavior and (not a.rmx_peer_file or not a.mfr_peer_file):
        ap.error('Integrated behavior requires BOTH --rmx-peer-file and --mfr-peer-file')
    if (a.economic_retrofits or a.economic_production) and a.manufacturer_economics is None:
        ap.error('Endogenous economic behavior requires independently sourced --manufacturer-economics. No costs/margins will be fabricated.')
    if a.manufacturer_led:
        ap.error('E05 removes automatic PLC-only conversion. Supply source-backed offerings with --manufacturer-offerings instead.')
    if a.start < '2010-01':
        ap.error('Start must be >= 2010-01')
    if a.end > '2024-12':
        ap.error('Only 2010-2024 supported')
    # Predictions through 2024 are allowed without unlocking held-out observations.
    # Observed 2023-24 shares are never loaded unless explicitly unlocked.
    if a.evaluate_heldout and not a.observed:
        ap.error('--evaluate-heldout requires --observed USGS file')
    if a.evaluate_heldout and a.end <= '2022-12':
        ap.error('--evaluate-heldout requires a simulation ending after 2022-12')
    if a.material=='LC3' and a.capability_file is None:
        ap.error('LC3 requires --capability-file; total cement capacity alone does not establish LC3 capability')
    a.out.mkdir(parents=True,exist_ok=True)
    inp=a.empirical_dir
    dm=load_csv(inp/'rmx_month_demand_exposure.csv',['yyyy_mm','rmx_src_id','state','D_i'])
    edges=load_csv(inp/'mfr_rmx_pairs.csv',['mfr_src_id','rmx_src_id'])
    dot=load_csv(inp/'dot_monthly_state.csv',['yyyy_mm','state','phi_s'])
    cap=load_csv(a.capacity_file,['mfr_src_id','capacity_tpm_model'])
    evidence=load_csv(a.evidence_file,['mfr_src_id','model_evidence_class','supported_month_if_dated'])
    for d,col in [(dm,'rmx_src_id'),(edges,'rmx_src_id'),(edges,'mfr_src_id'),(cap,'mfr_src_id'),(evidence,'mfr_src_id')]:
        d[col]=d[col].astype(str).str.strip()
    dm['D_i']=pd.to_numeric(dm.D_i,errors='raise')
    dot['phi_s']=pd.to_numeric(dot.phi_s,errors='raise')
    cap['capacity_tpm_model']=pd.to_numeric(cap.capacity_tpm_model,errors='coerce')
    # Unknown capacity is NOT zero production. Exclude such plants from
    # quantity allocation and explicitly record the omitted plant(s).
    # This yields a conditional scenario, not a verified market-share bound.
    unknown = cap[cap.capacity_tpm_model.isna()].copy()
    if not unknown.empty:
        unknown.to_csv(a.out/'manufacturers_excluded_unknown_capacity.csv', index=False)
        print(f'WARNING: excluding {len(unknown)} manufacturer(s) with unknown capacity from quantity allocation; '
              'results omit their potential supply, including during operating years.')
        cap = cap[cap.capacity_tpm_model.notna()].copy()
        if cap.empty: raise ValueError('No manufacturer has known capacity')
    if (cap.capacity_tpm_model < 0).any() or (dm.D_i < 0).any(): raise ValueError('Negative capacity/demand')
    cap=cap.drop_duplicates('mfr_src_id').set_index('mfr_src_id')
    evidence=evidence.drop_duplicates('mfr_src_id').set_index('mfr_src_id')
    if a.material=='LC3':
        lc=load_csv(a.capability_file,['mfr_src_id','feasible_tpm'])
        lc['mfr_src_id']=lc.mfr_src_id.astype(str).str.strip()
        lc=lc.set_index('mfr_src_id')
        if not cap.index.isin(lc.index).all(): raise ValueError('LC3 capability must explicitly cover every manufacturer (zero allowed)')
        ceilings=pd.to_numeric(lc.reindex(cap.index).feasible_tpm,errors='raise').to_numpy(float)
        if (ceilings < 0).any(): raise ValueError('Negative LC3 feasible_tpm')
        ceilings=np.minimum(ceilings,cap.capacity_tpm_model.to_numpy(float))
    else:
        ceilings=cap.capacity_tpm_model.to_numpy(float)
    # Optional economic decision data. Unknown is UNKNOWN, never assigned zero.
    economics=None
    if a.manufacturer_economics:
        economics=load_csv(a.manufacturer_economics,
            ['mfr_src_id','plc_incremental_margin_per_ton','annualized_retrofit_cost','source_basis'])
        economics['mfr_src_id']=economics.mfr_src_id.astype(str).str.strip()
        if economics.mfr_src_id.duplicated().any():
            raise ValueError('Duplicate plant economics rows')
        for col in ['plc_incremental_margin_per_ton','annualized_retrofit_cost']:
            economics[col]=pd.to_numeric(economics[col],errors='coerce')
        if economics.source_basis.isna().any() or economics.source_basis.astype(str).str.strip().eq('').any():
            raise ValueError('Economic source_basis must identify the independent source or declared scenario')
        if (economics.annualized_retrofit_cost.dropna()<0).any():
            raise ValueError('Negative retrofit cost')
        economics=economics.set_index('mfr_src_id')
    mids=cap.index.tolist(); midx={x:i for i,x in enumerate(mids)}
    feasibility=None
    if a.capability_feasibility:
        feasibility=load_csv(a.capability_feasibility,['mfr_src_id','feasible','evidence_basis'])
        feasibility['mfr_src_id']=feasibility.mfr_src_id.astype(str).str.strip()
        if feasibility.mfr_src_id.duplicated().any(): raise ValueError('Duplicate feasibility records')
        if not feasibility.feasible.isin([0,1,True,False]).all(): raise ValueError('feasible must be 0/1')
        if feasibility.evidence_basis.isna().any() or feasibility.evidence_basis.astype(str).str.strip().eq('').any(): raise ValueError('Feasibility requires evidence_basis')
        feasibility=feasibility.set_index('mfr_src_id')
    margin=np.full(len(mids),np.nan)
    annual_cost=np.full(len(mids),np.nan)
    if economics is not None:
        margin=economics.plc_incremental_margin_per_ton.reindex(mids).to_numpy(float)
        annual_cost=economics.annualized_retrofit_cost.reindex(mids).to_numpy(float)
    # A plant's accessible market is computed from unique RMX links, not
    # from prior PLC orders. It can therefore initiate supply-driven diffusion.
    rids=sorted(dm.rmx_src_id.unique()); ridx={x:i for i,x in enumerate(rids)}
    edges=edges[edges.rmx_src_id.isin(ridx)&edges.mfr_src_id.isin(midx)].drop_duplicates(subset=['rmx_src_id','mfr_src_id'])
    if 'distance_mi' not in edges: raise ValueError('MFR-RMX network requires distance_mi for locked distance allocation')
    global EDGE_DISTANCE
    EDGE_DISTANCE={(ridx[i],midx[j]):float(d) for j,i,d in zip(edges.mfr_src_id,edges.rmx_src_id,edges.distance_mi)}
    ee=np.array([(ridx[i],midx[j]) for j,i in zip(edges.mfr_src_id,edges.rmx_src_id)],dtype=int).reshape(-1,2)
    starts=cap.operating_start.to_dict() if 'operating_start' in cap else {}
    ends=cap.operating_end.to_dict() if 'operating_end' in cap else {}
    def operating(j,ym):
        st=starts.get(j); en=ends.get(j)
        return (pd.isna(st) or str(st)[:7]<=ym) and (pd.isna(en) or ym<str(en)[:7])
    # Evidence is an observation/constraint, NOT a manufacturer decision date.
    # Known positive evidence includes dated, latest-known, and undated reports.
    # Only dated positive evidence certifies availability *by* the given month;
    # it says nothing about the months before it. Undated reports do not fix
    # a historical monthly capability state.
    positive_classes = {
        'plant_dated_availability_boundary',
        'plant_latest_known_availability_bound',
        'plant_availability_without_monthly_transition_date',
    }
    contrary_classes = {'current_contrary_evidence'}
    evidence_class = evidence.model_evidence_class.fillna('unresolved').to_dict()
    boundaries = {}
    # Only contemporary, affirmative, completed availability evidence can
    # impose a by-date capability constraint. Scheduled announcements are NOT
    # proof of completion. Missing source dates remain unresolved for this rule.
    for j, row in evidence.iterrows():
        if row.model_evidence_class != 'plant_dated_availability_boundary' or pd.isna(row.supported_month_if_dated):
            continue
        boundary = str(row.supported_month_if_dated)[:7]
        source_date = pd.to_datetime(row.get('source_date'), errors='coerce')
        interpretation = str(row.get('date_interpretation', '')).lower()
        if ('scheduled' in interpretation or 'planned' in interpretation or
                pd.isna(source_date) or source_date > pd.Timestamp('2022-12-31') or
                boundary > '2022-12'):
            continue
        boundaries[j] = boundary
    if a.material == 'PLC':
        evidence.to_csv(a.out/'manufacturer_evidence_snapshot.csv')
        audit = evidence.reset_index().copy()
        audit['positive_evidence'] = audit.model_evidence_class.isin(positive_classes)
        audit['monthly_activation_identified'] = False
        audit['date_is_activation_date'] = False
        audit['interpretation'] = audit.model_evidence_class.map({
            'plant_dated_availability_boundary': 'Documented capable by month; earlier state unknown',
            'plant_latest_known_availability_bound': 'Documented capability by a latest-known bound; monthly onset unknown',
            'plant_availability_without_monthly_transition_date': 'Capability documented; monthly onset unknown',
            'unresolved': 'Capability unknown; not evidence of absence',
            'current_contrary_evidence': 'Contrary evidence; temporal scope requires manual review',
        }).fillna('Unrecognized evidence class; manual review required')
        audit.to_csv(a.out/'manufacturer_evidence_interpretation.csv', index=False)
        print('PLC evidence classes:', audit.model_evidence_class.value_counts().to_dict())
        print('CAUTION: Evidence dates are not activation dates; neither capability scenario identifies historical adoption.')
    # V5 BEHAVIORAL CONTRACT: explicitly testable hypotheses, not empirical facts
    # No transition hazard, delay, threshold, assumed PLC percentage or
    # automatic conversion from DOT acceptance. Undocumented plant capability
    # is UNKNOWN; this default scenario uses only dated positive evidence as
    # a conservative operational envelope, NOT a historical lower bound.
    # For earlier dates, documented-by evidence is NOT a transition date.
    # To explore manufacturer-led changes, provide a plant/month offering file
    # with evidence_basis distinguishing source-backed from scenario rows.
    # A plant offering BOTH has a SHARED total capacity across OPC and PLC;
    # product quantities are decided by orders, not preset mix percentages.
    # RMX-initiated PLC demand requires an independently justified requirement
    # file. DOT acceptance is a permission signal, NOT a demand fraction.
    # Supplier-driven PLC occurs only when the reachable suppliers offer PLC
    # but no OPC; receipt is tracked separately from operational adoption.
    if a.mfr_base_hazard != 0 or a.mfr_peer_effect != 0:
        raise ValueError('Unsupported manufacturer hazard parameters removed in V3')
    # Keep announced production STRATEGY separate from verified product OFFERINGS.
    # A prospective announcement is not evidence of completed conversion.
    announced_strategy = {}
    if a.corporate_rollout_scenario and not a.announced_conversion_strategy:
        ap.error('--corporate-rollout-scenario requires --announced-conversion-strategy')
    if a.announced_conversion_strategy:
        if a.material != 'PLC' or a.production_policy != 'opc_first':
            ap.error('--announced-conversion-strategy requires PLC and --production-policy opc_first')
        ev = load_csv(a.evidence_file, ['mfr_src_id','date_evidence_class','date_interpretation','source_date','source_url'])
        for row in ev.itertuples(index=False):
            if str(row.date_evidence_class).strip() != 'prospective_only':
                continue
            desc = str(row.date_interpretation).lower()
            # Restrict to explicitly full / 100% conversions, not generic PLC availability.
            if not (('full' in desc or '100%' in desc) and ('conversion' in desc or 'transition' in desc)):
                continue
            published = pd.to_datetime(row.source_date, errors='coerce')
            if pd.isna(published) or published > pd.Timestamp('2022-12-31'):
                continue
            if not str(row.source_url).startswith(('http://','https://')):
                continue
            mid = str(row.mfr_src_id).strip()
            announced_strategy[mid] = dict(start=published.strftime('%Y-%m'),
                evidence_class='prospective_only', source_date=str(row.source_date),
                source_url=str(row.source_url), date_interpretation=str(row.date_interpretation))
        if a.corporate_rollout_scenario:
            # Hypothetical company-wide strategy propagation, NOT a factual
            # offering, completion, or plant-specific announcement record.
            company_by_id = {str(row.mfr_src_id).strip(): str(row.company).strip()
                             for row in ev.itertuples(index=False)} if 'company' in ev.columns else {}
            # Load the company field directly from the original evidence file.
            company_ev = pd.read_csv(a.evidence_file, usecols=['mfr_src_id','company'])
            company_by_id = {str(row.mfr_src_id).strip(): str(row.company).strip()
                             for row in company_ev.itertuples(index=False)}
            company_starts = {}
            for mid, record in announced_strategy.items():
                company = company_by_id.get(mid)
                if company:
                    company_starts[company] = min(company_starts.get(company, '9999-99'), record['start'])
            original_ids = set(announced_strategy)
            for mid, company in company_by_id.items():
                if mid not in original_ids and company in company_starts:
                    announced_strategy[mid] = dict(start=company_starts[company],
                        evidence_class='HYPOTHETICAL_COMPANY_ROLLOUT',
                        source_date='', source_url='',
                        date_interpretation='Scenario: company-wide priority inferred from another plant announcement; not observed at this plant')
            print(f'Corporate rollout scenario: {len(original_ids)} announced plants; '
                  f'{len(announced_strategy)-len(original_ids)} additional same-company plants (hypothetical).')
        pd.DataFrame([dict(mfr_src_id=k, **v) for k,v in announced_strategy.items()],
            columns=['mfr_src_id','start','evidence_class','source_date','source_url','date_interpretation']).to_csv(
            a.out/'announced_conversion_strategy_audit.csv',index=False)
        print(f'Announced-conversion strategy scenario: {len(announced_strategy)} dated pre-2023 plant announcements; not confirmed conversions.')
    offerings = None
    if a.manufacturer_offerings:
        offerings=load_csv(a.manufacturer_offerings,['yyyy_mm','mfr_src_id','offering','evidence_basis'])
        offerings['mfr_src_id']=offerings.mfr_src_id.astype(str).str.strip()
        if not offerings.offering.isin(['OPC_only','both','PLC_only','PLC_primary']).all():
            raise ValueError('offering must be OPC_only, both, PLC_only, or PLC_primary')
        if offerings.duplicated(['yyyy_mm','mfr_src_id']).any():
            raise ValueError('Duplicate manufacturer offering records')
        if offerings.evidence_basis.isna().any() or offerings.evidence_basis.astype(str).str.strip().eq('').any():
            raise ValueError('Missing offering evidence_basis')
        # Reject unsupported product-offering histories and post-cutoff records.
        if not offerings.evidence_basis.astype(str).str.startswith('documented:').all():
            raise ValueError('E05 requires evidence_basis beginning documented: for every offering; scenario transitions cannot be treated as historical evidence')
        if (~offerings.yyyy_mm.astype(str).between(a.start,a.end)).any():
            raise ValueError('Offering dates must be within the development simulation interval')
    # E05: automatically derive only strongly worded, plant-specific,
    # retrospectively CONFIRMED PLC-only offering records from the EXISTING
    # evidence constraints file. Never turn availability into conversion dates.
    # The input audit is a compiled secondary register, not independent source
    # verification. Exclude missing publication dates and future information.
    if a.material == 'PLC' and a.manufacturer_offerings is None:
        audit_rows = []
        inferred = []
        source_rows = pd.read_csv(a.evidence_file)
        for row in source_rows.itertuples(index=False):
            plant_id = str(getattr(row, 'mfr_src_id', '')).strip()
            interpretation = str(getattr(row, 'date_interpretation', '') or '')
            src_date = str(getattr(row, 'source_date', '') or '')
            src_url = str(getattr(row, 'source_url', '') or '')
            title = str(getattr(row, 'source_title', '') or '')
            supported = str(getattr(row, 'supported_date', '') or '')
            scope = str(getattr(row, 'evidence_scope', '') or '')
            # Require a dated source that was available during development.
            published = pd.to_datetime(src_date, errors='coerce')
            publication_ok = pd.notna(published) and published <= pd.Timestamp('2022-12-31')
            # Require explicit completed full/100% conversion language.
            # Announcements, planned conversions and primary-product claims
            # do not establish withdrawal of OPC.
            wording = interpretation.lower()
            confirmed = ('100% plc production' in wording or
                         'full conversion of both u.s. cement plants' in wording)
            eligible = (publication_ok and confirmed and bool(src_url.startswith('http'))
                        and plant_id in midx and a.start <= published.strftime('%Y-%m') <= a.end)
            reason = ('eligible_provisional_compiled_evidence' if eligible else
                      'not_a_dated_confirmed_full_conversion')
            audit_rows.append(dict(mfr_src_id=plant_id,plant=getattr(row,'plant',''),
                 source_title=title,source_date=src_date,supported_date=supported,
                 date_interpretation=interpretation,evidence_scope=scope,
                 source_url=src_url,decision=reason,
                 limitation='Compiled evidence; source not independently reverified; month is first model-observable confirmation, NOT historical conversion date'))
            if eligible:
                # Start only when a contemporaneous publication confirms the
                # completed transition. Persist afterwards as an explicit
                # observational-envelope assumption, not an inferred event date.
                for ym in pd.period_range(published.strftime('%Y-%m'), a.end, freq='M'):
                    inferred.append(dict(yyyy_mm=str(ym),mfr_src_id=plant_id,
                       offering='PLC_only',evidence_basis='documented:compiled_confirmed_full_conversion:'+src_url))
        pd.DataFrame(audit_rows).to_csv(a.out/'E05_manufacturer_offering_evidence_audit.csv',index=False)
        if inferred:
            offerings = pd.DataFrame(inferred).drop_duplicates(['yyyy_mm','mfr_src_id'])
            offerings.to_csv(a.out/'E05_auto_manufacturer_offerings.csv',index=False)
        else:
            offerings = pd.DataFrame(columns=['yyyy_mm','mfr_src_id','offering','evidence_basis'])
        print(f'E05: {offerings.mfr_src_id.nunique()} manufacturers with provisionally confirmed PLC-only offerings from dated pre-2023 evidence. See E05_manufacturer_offering_evidence_audit.csv.')
    requirements = None
    if a.rmx_requirements:
        requirements=load_csv(a.rmx_requirements,['yyyy_mm','rmx_src_id','plc_required_tons','evidence_basis'])
        requirements['rmx_src_id']=requirements.rmx_src_id.astype(str).str.strip()
        requirements['plc_required_tons']=pd.to_numeric(requirements.plc_required_tons,errors='raise')
        if (requirements.plc_required_tons<0).any() or requirements.duplicated(['yyyy_mm','rmx_src_id']).any():
            raise ValueError('Invalid RMX requirements')
        if requirements.evidence_basis.isna().any(): raise ValueError('Missing RMX evidence_basis')
    material_constraints=None
    if a.rmx_material_constraints:
        material_constraints=load_csv(a.rmx_material_constraints,['yyyy_mm','rmx_src_id','opc_required_tons','evidence_basis'])
        material_constraints['rmx_src_id']=material_constraints.rmx_src_id.astype(str).str.strip()
        material_constraints['opc_required_tons']=pd.to_numeric(material_constraints.opc_required_tons,errors='raise')
        if (material_constraints.opc_required_tons<0).any() or material_constraints.duplicated(['yyyy_mm','rmx_src_id']).any():
            raise ValueError('Invalid hard OPC constraints')
        if material_constraints.evidence_basis.isna().any() or material_constraints.evidence_basis.astype(str).str.strip().eq('').any():
            raise ValueError('Missing material-constraint evidence_basis')
        if not set(material_constraints.rmx_src_id).issubset(set(rids)):
            raise ValueError('Unknown RMX ID in material constraints')
    feasibility_rows=[]
    adoption_events = None
    if a.rmx_adoption_events:
        adoption_events=load_csv(a.rmx_adoption_events,['yyyy_mm','rmx_src_id','evidence_basis'])
        adoption_events['rmx_src_id']=adoption_events.rmx_src_id.astype(str).str.strip()
        if adoption_events.evidence_basis.isna().any(): raise ValueError('Missing adoption evidence_basis')
    adopted=np.zeros(len(rids),dtype=bool)  # operational adoption requires independently supported evidence
    has_used=np.zeros(len(rids),dtype=bool) # receipt history, distinct from adoption
    capable=np.zeros(len(mids),dtype=bool)
    # E15: one-month-lagged local experience is a behavioral state, not a fitted
    # diffusion curve. PLC quantities delivered in month t influence neighboring
    # RMX requests in t+1. No response period, random hazard, or fixed PLC share.
    previous_plc_share=np.zeros(len(rids), dtype=float)
    # Endogenous manufacturer decisions use PREVIOUS delivered quantities only.
    # Eligibility is an explicit feasibility scenario, never an assertion of historical capability.
    previous_plc_received=np.zeros(len(rids),dtype=float)
    endogenous_events=[]
    # Structural networks: do not fit to PLC outcomes.
    if a.integrated_behavior:
        rp=pd.read_csv(a.rmx_peer_file)
        mp=pd.read_csv(a.mfr_peer_file)
        def peer_columns(df,kind):
            if kind=='rmx':
                options=[('rmx_src_id','peer_rmx_src_id'),('rmx_src_id','peer_src_id'),('rmx_src_id_i','rmx_src_id_j'),('source_rmx_src_id','target_rmx_src_id'),('rmx_i','rmx_j')]
            else:
                options=[('mfr_src_id','peer_mfr_src_id')]
            for x,y in options:
                if x in df and y in df:return x,y
            raise ValueError(f'{kind} peer file columns {list(df.columns)} not recognized; expected {options}')
        rx,ry=peer_columns(rp,'rmx'); mx,my=peer_columns(mp,'mfr')
        # Make directed and deduplicated even when source contains undirected pairs.
        rset=set(); mset=set()
        for x,y in zip(rp[rx].astype(str).str.strip(),rp[ry].astype(str).str.strip()):
            if x in ridx and y in ridx and x!=y:rset.update(((ridx[x],ridx[y]),(ridx[y],ridx[x])))
        for x,y in zip(mp[mx].astype(str).str.strip(),mp[my].astype(str).str.strip()):
            if x in midx and y in midx and x!=y:mset.update(((midx[x],midx[y]),(midx[y],midx[x])))
        neighbor_edges=np.array(sorted(rset),dtype=int).reshape(-1,2)
        manufacturer_peer_edges=np.array(sorted(mset),dtype=int).reshape(-1,2)
        print('Integrated peer edges:',len(neighbor_edges),'RMX directed,',len(manufacturer_peer_edges),'MFR directed')
        if not len(neighbor_edges) or not len(manufacturer_peer_edges):raise ValueError('Empty peer network')
    else:
        from collections import defaultdict
        supplier_customers=defaultdict(list)
        for ii,jj in ee:supplier_customers[int(jj)].append(int(ii))
        local_neighbors=[set() for _ in rids]
        for customers in supplier_customers.values():
            for ii in customers:local_neighbors[ii].update(customers)
        for ii,neighbors in enumerate(local_neighbors):neighbors.discard(ii)
        neighbor_edges=np.array([(ii,kk) for ii,neighbors in enumerate(local_neighbors)
                                 for kk in neighbors],dtype=int).reshape(-1,2)
        manufacturer_peer_edges=np.empty((0,2),dtype=int)
    previous_offer=np.zeros(len(mids),dtype=bool)
    mfr_rng=np.random.default_rng(a.seed)
    mfr_decision_rows=[]
    manufacturer_signal_rows=[]
    interaction_rows=[]
    supplier_led_rows=[]
    rr=[]; mm=[]
    months=sorted(x for x in dm.yyyy_mm.astype(str).unique() if a.start<=x<=a.end)
    reference_dm=dm[dm.yyyy_mm.astype(str)=='2022-12'].set_index('rmx_src_id').reindex(rids)
    reference_phi=dot[dot.yyyy_mm.astype(str)=='2022-12'].drop_duplicates('state').set_index('state').phi_s
    if any(x>'2022-12' for x in months) and a.future_exogs=='freeze_2022' and (reference_dm.D_i.isna().any() or reference_phi.empty):
        raise ValueError('2022-12 inputs required for leakage-free projection')
    ei,ej=ee[:,0],ee[:,1]
    shipment_rows=[]
    for ym in months:
        shipment_start=len(shipment_rows)
        rows=(reference_dm if ym>'2022-12' and a.future_exogs=='freeze_2022' else dm[dm.yyyy_mm.astype(str)==ym].set_index('rmx_src_id').reindex(rids))
        if rows.D_i.isna().any(): raise ValueError(f'Missing RMX demand for {ym}; provided_scenario requires complete future exogenous rows')
        D=rows.D_i.to_numpy(float)
        states=rows.state.astype(str).to_numpy()
        ph=(reference_phi if ym>'2022-12' and a.future_exogs=='freeze_2022' else dot[dot.yyyy_mm.astype(str)==ym].drop_duplicates('state').set_index('state').phi_s)
        if not set(states).issubset(ph.index): raise ValueError(f'Missing DOT states {ym}')
        policy=ph.reindex(states).to_numpy(float)
        if np.any(~np.isfinite(policy)) or np.any((policy<0)|(policy>1)):
            raise ValueError(f'Invalid DOT phi_s {ym}')
        # Binary DOT acceptance: nonzero phi_s is interpreted as evidence of
        # some acceptance, not as a fraction of cement purchased.
        accepted=(policy>0).astype(float)
        oper=np.array([operating(j,ym) for j in mids])
        # MFR capability: dated evidence constrains capability BY a date;
        # absent evidence is unresolved, not proven absent. Default dated-only
        # scenario is deliberately incomplete and not an empirical estimate.
        must_by=np.array([j in boundaries and ym>=boundaries[j] for j in mids])
        # A verified availability-by constraint applies even when the optional
        # endogenous network-response mechanism is enabled. E18 accidentally
        # disabled this empirical constraint in that configuration.
        capable |= oper & must_by
        capable &= oper
        # E15: manufacturer activation follows exposure to PLC deliveries in its
        # geographically reachable market, with NO arbitrary hazard or delay.
        # A source-backed manufacturer introduction can seed PLC independently
        # of RMX demand. This is an explicitly TESTABLE network-response rule,
        # not an observed plant decision or proof of investment feasibility.
        # Positive evidence-by dates are constraints, NOT automatic transitions.
        if a.endogenous_network_capability:
            if a.availability=='unresolved_possible':
                eligible=np.array([evidence_class.get(j) not in contrary_classes for j in mids],dtype=bool)  # explicit upper-feasibility scenario
            else:
                eligible=np.array([evidence_class.get(j) in positive_classes for j in mids],dtype=bool)
            if feasibility is not None:
                specified=feasibility.feasible.reindex(mids)
                eligible=np.where(specified.notna(),specified.fillna(False).to_numpy(dtype=bool),eligible)
            # Network exposure and DOT opportunity are information, not observed conversions.
            exposure=np.bincount(ej,weights=previous_plc_received[ei],minlength=len(mids))
            if a.integrated_behavior:
                pi,pj=manufacturer_peer_edges[:,0],manufacturer_peer_edges[:,1]
                peer_n=np.bincount(pi,minlength=len(mids))
                peer_offers=np.bincount(pi,weights=previous_offer[pj].astype(float),minlength=len(mids))
                peer_exposure=np.divide(peer_offers,peer_n,out=np.zeros(len(mids)),where=peer_n>0)
                # Demand and regulatory signals are computed from current observed exogenous inputs.
                accessible_demand=np.bincount(ej,weights=D[ei],minlength=len(mids))
                dot_exposure=np.divide(np.bincount(ej,weights=D[ei]*accepted[ei],minlength=len(mids)),
                    accessible_demand,out=np.zeros(len(mids)),where=accessible_demand>0)
                # EXPLICIT UNIDENTIFIED HYPOTHESIS: any prior peer PLC offering
                # OR prior PLC delivery in accessible market is sufficient to
                # trigger a feasible plant. DOT acceptance alone is NOT sufficient.
                # No fitted rate, delay, threshold or conversion cost is asserted.
                # Shared coefficients, plant-specific geographic opportunities and
                # peer networks. Monthly stochastic decision is a CALIBRATABLE
                # structural hypothesis, not an observed conversion date or cost.
                # Market demand is an opportunity signal, not a prerequisite:
                # the intercept permits supply-led introduction with zero peer use.
                # Do not count the same RMX's demand as actual manufacturer sales.
                market_ratio=np.divide(accessible_demand,cap.capacity_tpm_model.to_numpy(float),
                    out=np.zeros(len(mids)),where=cap.capacity_tpm_model.to_numpy(float)>0)
                score=np.clip(a.mfr_alpha0+a.mfr_alpha_market*np.log1p(market_ratio)
                              +a.mfr_alpha_peer*peer_exposure,-35,35)
                probability=1.0/(1.0+np.exp(-score))
                draws=mfr_rng.random(len(mids))
                candidate=oper & eligible & (~capable)
                trigger=candidate & (draws<probability)
                manufacturer_signal_rows.extend(dict(yyyy_mm=ym,mfr_src_id=mids[j],
                    accessible_demand_tons=accessible_demand[j],dot_exposure=dot_exposure[j],
                    manufacturer_peer_offer_share=peer_exposure[j],prior_connected_plc_tons=exposure[j],
                    scenario_trigger=int(trigger[j])) for j in range(len(mids)))
                mfr_decision_rows.extend(dict(yyyy_mm=ym,mfr_src_id=mids[j],
                    eligible=int(candidate[j]),market_to_capacity=float(market_ratio[j]),
                    peer_offer_share=float(peer_exposure[j]),probability=float(probability[j]),
                    random_draw=float(draws[j]),introduced=int(trigger[j]),
                    evidence_class=str(evidence_class.get(mids[j],''))) for j in range(len(mids)))
                newly=trigger
            else:
                newly=np.zeros(len(mids),dtype=bool)  # no conversion without independent feasibility/economic evidence
            for k in np.flatnonzero(newly):
                endogenous_events.append(dict(yyyy_mm=ym,mfr_src_id=mids[k],previous_network_plc_tons=float(exposure[k]),
                    eligibility_scenario=a.availability,interpretation='modeled network response, not historical conversion'))
            capable |= newly

        # Economic retrofit decision: positive *incremental* annual value,
        # compared with independently sourced annualized investment cost.
        # This is an explicit decision hypothesis, NOT an observed transition.
        # Accessible demand is counted ONCE per RMX for each manufacturer's
        # opportunity set. It is NOT allocated shipments or an RMX PLC request.
        # The 12 factor converts monthly demand to annual volume; it is not
        # an adoption response period or implementation delay.
        if a.economic_retrofits:
            # Divide each RMX's potential market among its reachable operating
            # manufacturers. Otherwise an RMX linked to five plants would
            # be counted five times as prospective sales opportunity.
            active_edges=oper[ej]
            active_degree=np.bincount(ei[active_edges],minlength=len(rids))
            potential=np.divide(D[ei[active_edges]],active_degree[ei[active_edges]],
                                out=np.zeros(active_edges.sum(),dtype=float),
                                where=active_degree[ei[active_edges]]>0)
            market_volume=np.bincount(ej[active_edges],weights=potential,minlength=len(mids))
            if market_volume.sum()>D[active_degree>0].sum()+1e-5:
                raise RuntimeError('Manufacturer opportunity double-counts RMX demand')
            identifiable=np.isfinite(margin)&np.isfinite(annual_cost)
            investment=(12.0*market_volume*np.maximum(margin,0.0)>annual_cost)&(margin>0)&identifiable
            capable |= oper & investment

        # Capability evidence is not a product-mix or withdrawal observation.
        # For unresolved plants, OPC-only is an explicit conservative allocation
        # assumption, NEVER a claim of historically absent PLC capability.
        # Dated positive evidence establishes capability by a date, NOT its
        # first month; the default scenario cannot reconstruct the onset.
        offer=np.where(capable,'both','OPC_only').astype(object)
        documented_offering=np.zeros(len(mids),dtype=bool)
        if offerings is not None:
            subset=offerings[offerings.yyyy_mm.astype(str)==ym]
            for row in subset.itertuples():
                if row.mfr_src_id not in midx:
                    raise ValueError(f'Unknown manufacturer in offering record: {row.mfr_src_id}')
                j=midx[row.mfr_src_id]
                if row.offering in ('both','PLC_only','PLC_primary'):
                    # Source-backed product offering is positive capability
                    # evidence for that month, not an inferred retrofit date.
                    capable[j]=True
                offer[j]=row.offering
                documented_offering[j]=True
        if a.availability == 'unresolved_possible' and not a.endogenous_network_capability:
            # Upper feasibility envelope: unknown capability is possible, NOT verified.
            # This does not establish plant-specific investment or historical timing.
            capable |= oper
            offer = np.where(oper, 'both', 'OPC_only').astype(object)
        # Source-backed OPC withdrawal affects the network without any prior
        # RMX PLC request; it is never inferred from capability alone.
        opc_available=oper & np.isin(offer,['OPC_only','both','PLC_primary'])
        plc_available=oper & np.isin(offer,['PLC_only','both','PLC_primary']) & capable
        # RMX demand: PLC requirements are EXOGENOUS, independently justified
        # quantities, never inferred from DOT acceptance or fitted to USGS.
        plc_req=np.zeros(len(rids))
        if requirements is not None:
            subset=requirements[requirements.yyyy_mm.astype(str)==ym]
            for row in subset.itertuples():
                if row.rmx_src_id in ridx: plc_req[ridx[row.rmx_src_id]]=row.plc_required_tons
        if np.any(plc_req>D+1e-6): raise ValueError(f'PLC requirements exceed demand: {ym}')
        independent_req=plc_req.copy()
        # Hard project constraints, if documented. All other demand remains
        # UNKNOWN compatibility: the baseline tests a permissive envelope,
        # never asserting that unknown demand is empirically PLC-qualified.
        opc_required=np.zeros(len(rids),dtype=float)
        if material_constraints is not None:
            subset=material_constraints[material_constraints.yyyy_mm.astype(str)==ym]
            for row in subset.itertuples():
                opc_required[ridx[row.rmx_src_id]]=row.opc_required_tons
        if np.any(opc_required>D+1e-6):
            raise ValueError(f'Hard OPC requirement exceeds demand: {ym}')
        plc_eligible=np.maximum(0.0,D-opc_required)
        if np.any(independent_req>plc_eligible+1e-6):
            raise ValueError(f'Conflicting documented PLC and OPC requirements: {ym}')
        # Supply-driven substitution: when an RMX has PLC supply but NO OPC
        # supplier, all feasible deliveries must be PLC. This is a constraint,
        # not a voluntary RMX preference or a fitted utilization fraction.
        reachable_opc=np.bincount(ei,weights=opc_available[ej].astype(float),minlength=len(rids))>0
        reachable_plc=np.bincount(ei,weights=plc_available[ej].astype(float),minlength=len(rids))>0
        forced=(~reachable_opc)&reachable_plc
        # PLC-02: RMX material-choice decision (retained).
        # DOT acceptance is permission, NOT evidence of PLC procurement.
        # Independent RMX requests require --rmx-requirements and the
        # --rmx-initiated switch; no unobserved preference is invented.
        # With no requirements file, independent PLC demand is zero by
        # conservative scenario assumption (NOT a historical estimate).
        # E15 peer mechanism: an RMX observes the *delivered PLC share* of
        # other RMXs connected to the same cement suppliers in the prior month.
        # The mean is a direct network statistic, not a calibrated coefficient.
        # DOT acceptance is a permissive condition for this illustrative
        # public-market pathway, not a fraction of orders.
        if len(neighbor_edges):
            peer_sum=np.bincount(neighbor_edges[:,0],
                weights=previous_plc_share[neighbor_edges[:,1]],minlength=len(rids))
            peer_count=np.bincount(neighbor_edges[:,0],minlength=len(rids))
            peer_share=np.divide(peer_sum,peer_count,out=np.zeros(len(rids)),where=peer_count>0)
        else:
            peer_share=np.zeros(len(rids))
        # Integrated structural hypothesis: local peer use signals an opportunity,
        # but the requested quantity is NOT numerically equated to peer share.
        # Without observed order sizes, this is an upper-demand scenario: an
        # RMX exposed to any peer use requests its full substitutable demand.
        # This is NOT an empirical prediction of PLC orders.
        # HYPOTHESIS: desired PLC share for eligible demand at RMXs with
        # reachable PLC suppliers. Coefficients are common, while DOT, peers,
        # and supplier access vary by RMX. These defaults are illustrative,
        # NOT estimates; calibrate using state-month development outcomes.
        z=np.clip(a.rmx_beta0+a.rmx_beta_dot*policy+a.rmx_beta_peer*peer_share,-35,35)
        desired_share=1.0/(1.0+np.exp(-z))
        peer_request=np.where(reachable_plc,plc_eligible*desired_share,0.0)
        # Preserve independently documented requirements as a lower bound,
        # not an additive order; never exceed eligible cement demand.
        plc_req=np.maximum(plc_req,peer_request)
        voluntary=(plc_req>0)&reachable_plc&(~forced)
        # --rmx-initiated gates only external requirements. Endogenous peer
        # requests operate in both cases. The mechanism is a structural
        # hypothesis, not measured procurement behavior.
        # Supplier-driven pathway: if accessible suppliers offer PLC but
        # none offer OPC, substitutable demand requests PLC. This assumes
        # no documented OPC-only requirement; such constraints need data.
        plc_req=np.where(forced,plc_eligible,plc_req)
        # Shared-capacity sequential allocation. First honor supported PLC
        # requirements and forced substitution. Remaining demand uses OPC.
        # If OPC is insufficient, residual can use PLC only at RMXs with
        # operational permission/requirements or forced supplier substitution.
        plc_edges=ee[plc_available[ej]]
        opc_edges=ee[opc_available[ej]]
        total_cap=cap.capacity_tpm_model.to_numpy(float)*oper
        # E18: allocate documented PLC-only supplier offerings BEFORE RMX PLC
        # requests. This makes the manufacturer-led pathway operationally
        # independent of peer-generated requests. Shared capacities and RMX
        # demand are reduced before allocating request-driven deliveries.
        # This is a transparent supplier-priority scenario, not observed contracts.
        exclusive=oper & capable & (offer == 'PLC_only')
        exclusive_edges=ee[exclusive[ej]]
        exclusive_received,exclusive_supplied,f_exclusive=allocate(plc_eligible,total_cap*exclusive,exclusive_edges,return_flows=True)
        remaining_demand=np.maximum(0.0,D-exclusive_received)
        remaining_cap=np.maximum(0.0,total_cap-exclusive_supplied)
        requested_after_supplier=np.minimum(plc_req,np.maximum(0.0,plc_eligible-exclusive_received))
        requested_received,requested_supplied,f_requested=allocate(requested_after_supplier,remaining_cap,plc_edges,return_flows=True)
        plc_received=exclusive_received+requested_received
        plc_supplied=exclusive_supplied+requested_supplied
        # Separate the manufacturer's independent allocation from RMX request
        # states. Peer requests may be nonzero almost everywhere; they must not
        # erase the existence of a supplier-led allocation.
        supplier_led_rows.append(dict(
            yyyy_mm=ym,
            documented_plc_only_operating=int(exclusive.sum()),
            supplier_led_plc_tons=float(exclusive_supplied.sum()),
            supplier_led_rmxs=int((exclusive_received>1e-9).sum()),
            supplier_led_without_request_tons=float(exclusive_received[plc_req<=1e-9].sum()),
            supplier_led_without_independent_requirement_tons=float(exclusive_received[independent_req<=1e-9].sum()),
            supplier_led_before_requests_tons=float(exclusive_received.sum()),
            request_driven_plc_tons=float(requested_received.sum()),
            note='PLC-only deliveries allocated before RMX requests; no claim of observed contracts or qualification'))
        # E07 structural producer-first hypothesis: capable plants may offer PLC
        # before independently documented RMX requests. No fixed mix fraction.
        # This is NOT an empirically identified profit-maximizing decision.
        # E05: source-documented PLC-primary supplier decisions are evaluated
        # BEFORE OPC procurement, without waiting for an RMX PLC request.
        # PLC_primary means documented PLC as primary product, NOT PLC-only.
        # This is an explicit, testable allocation-priority hypothesis; source
        # evidence does not establish the quantities actually manufactured.
        # E15 does not assume every dual-offering plant prioritizes PLC.
        # Source-documented PLC_primary remains a manufacturer-led seed;
        # otherwise manufacturers fill PLC requests and then OPC demand.
        if a.production_policy == 'producer_first':
            # Structural upper-envelope scenario, NOT documented historical behavior.
            # Prioritize PLC at all capable dual-offering plants; preserve capacity,
            # geography, and documented hard OPC constraints.
            primary=oper & capable & np.isin(offer, ['both', 'PLC_primary'])
        elif a.economic_production:
            # For dual-offering plants, an independently sourced positive
            # PLC-vs-OPC margin determines priority. No preset mix fractions.
            # Unknown margins never imply a PLC-first preference.
            primary=oper & capable & ((offer=='PLC_primary') | ((offer=='both') & np.isfinite(margin) & (margin>0)))
        else:
            primary=oper & capable & ((offer=='PLC_primary') | False)
        if a.announced_conversion_strategy:
            # Announcement establishes intent, not product withdrawal or conversion date.
            # Apply only once the manufacturer is independently/model-scenario PLC-capable.
            strategy_eligible=np.array([mid in announced_strategy and
                ym >= announced_strategy[mid]['start'] for mid in mids],dtype=bool)
            primary |= oper & capable & (offer == 'both') & strategy_eligible
        primary_edges=ee[primary[ej]]
        remaining=np.maximum(0,D-plc_received)
        primary_cap=np.maximum(0,total_cap-plc_supplied)*primary
        primary_received,primary_supplied,f_primary=allocate(np.minimum(remaining,np.maximum(0.0,plc_eligible-plc_received)),primary_cap,primary_edges,return_flows=True)
        plc_received+=primary_received
        plc_supplied+=primary_supplied
        residual_cap=np.maximum(0,total_cap-plc_supplied)
        opc_received,opc_supplied,f_opc=allocate(np.maximum(0,D-plc_received),residual_cap,opc_edges,return_flows=True)
        # PLC-03: manufacturer-led, demand-constrained alternative offering.
        # A capable manufacturer offers PLC alongside OPC. If the network
        # cannot fulfill residual cement demand as OPC, RMXs may procure PLC
        # from capable, geographically reachable manufacturers instead.
        # This is an explicit substitutability scenario, NOT evidence that
        # the RMX requested PLC or that a manufacturer withdrew OPC.
        # No production fraction, adoption probability, or conversion delay.
        residual_cap=np.maximum(0,total_cap-plc_supplied-opc_supplied)
        unmet_after_opc=np.maximum(0,D-plc_received-opc_received)
        plc_fallback,plc_fallback_supplied,f_fallback=allocate(np.minimum(unmet_after_opc,np.maximum(0.0,plc_eligible-plc_received)),residual_cap,plc_edges,return_flows=True)
        plc_received += plc_fallback
        plc_supplied += plc_fallback_supplied
        # Exact LP edge flows: not inferred from aggregate RMX or manufacturer totals.
        for tier,material,flows in (('exclusive','PLC',f_exclusive),
                                    ('requested','PLC',f_requested),
                                    ('primary','PLC',f_primary),
                                    ('opc','OPC',f_opc),
                                    ('fallback','PLC',f_fallback)):
            for ri,mj,tons in flows:
                shipment_rows.append((ym,str(mids[mj]),str(rids[ri]),material,tier,tons))
        # Reconstruct BOTH endpoints from the very same edge allocations.
        monthly_shipments=shipment_rows[shipment_start:]
        for material,recv,sup in (('PLC',plc_received,plc_supplied),('OPC',opc_received,opc_supplied)):
            reconstructed_r=np.zeros(len(rids)); reconstructed_m=np.zeros(len(mids))
            for _,mid,rid,mat,_,tons in monthly_shipments:
                if mat==material:
                    reconstructed_r[ridx[rid]]+=tons
                    reconstructed_m[midx[mid]]+=tons
            if not np.allclose(reconstructed_r,recv,rtol=1e-9,atol=1e-3):
                raise RuntimeError(f'{ym} {material} shipment-to-RMX conservation failed')
            if not np.allclose(reconstructed_m,sup,rtol=1e-9,atol=1e-3):
                raise RuntimeError(f'{ym} {material} shipment-to-manufacturer conservation failed')
        # Shared manufacturer capacity must hold across both materials.
        received=plc_received+opc_received
        if np.any(received>D+1e-4): raise RuntimeError('RMX quantity conservation failed')
        if np.any(plc_received>plc_eligible+1e-4): raise RuntimeError('Hard OPC requirement violated by PLC deliveries')
        if np.any(plc_supplied+opc_supplied>total_cap+1e-4):
            raise RuntimeError('Manufacturer total capacity exceeded')
        # Persistent modeled operational transition: voluntary choice or
        # supplier-only availability is a decision/constraint, not inferred
        # from a tiny shipment. The receipt history is separately recorded.
        # No persistent adoption inferred from deliveries or exposure.
        has_used |= plc_received>1e-9
        feasibility_rows.append(dict(yyyy_mm=ym,total_demand_tons=float(D.sum()),
            documented_opc_required_tons=float(opc_required.sum()),
            unknown_compatibility_tons=float(plc_eligible.sum()-independent_req.sum()),
            independently_requested_plc_tons=float(independent_req.sum()),
            plc_delivered_tons=float(plc_received.sum()),
            opc_delivered_tons=float(opc_received.sum()),
            hard_opc_shortfall_tons=float(np.maximum(0.0,opc_required-opc_received).sum()),
            warning='Unspecified project compatibility is UNKNOWN; permissive envelope is not evidence of qualification'))
        previous_offer=plc_available.copy()
        previous_plc_received=plc_received.copy()
        previous_plc_share=np.divide(plc_received,received,
            out=np.zeros(len(rids)),where=received>0)
        interaction_rows.append(dict(yyyy_mm=ym,rmxs_with_peer_interest=int((peer_share>0).sum()),rmxs_with_supply_interest=int(reachable_plc.sum()),peer_requested_tons=float(peer_request.sum()),
            total_plc_requested_tons=float(plc_req.sum()),
            rmxs_with_peer_request=int((peer_request>0).sum()),
            rmxs_receiving_plc=int((plc_received>1e-9).sum()),
            manufacturer_plc_tons=float(plc_supplied.sum())))
        if adoption_events is not None:
            for r_id in adoption_events.loc[adoption_events.yyyy_mm.astype(str)==ym,'rmx_src_id']:
                if r_id in ridx: adopted[ridx[r_id]]=True
        # Operational adoption is NOT inferred from any receipt. Supported
        # RMX qualification data can be added later as a separate state input.
        # Offering category is not a production fraction.
        plc_offer_fraction=np.full(len(mids),np.nan)
        for i,r in enumerate(rids):
            rr.append((ym,states[i],r,D[i],policy[i],opc_received[i],plc_received[i],int(adopted[i]),int(has_used[i]),int(forced[i]),float(plc_req[i]),int((peer_share[i]>0) or (reachable_plc[i]) or (accepted[i]>0)),float(peer_share[i]),float(plc_received[i]/received[i]) if received[i]>0 else 0.0))
        for j,m in enumerate(mids):
            mm.append((ym,m,int(oper[j]),int(capable[j]),float(plc_offer_fraction[j]),float(opc_supplied[j]),float(plc_supplied[j]),boundaries.get(m,''),evidence_class.get(m,'unresolved'),offer[j],int(documented_offering[j])))
    pd.DataFrame(supplier_led_rows).to_csv(a.out/'E18_supplier_led_diagnostics.csv',index=False)
    pd.DataFrame(feasibility_rows).to_csv(a.out/'E18_material_feasibility_diagnostics.csv',index=False)
    r=pd.DataFrame(rr,columns=['yyyy_mm','state','rmx_src_id','D_i','phi_s','opc_tons','material_tons','adopted','has_used_material','supply_forced','plc_requested_tons','plc_interest','peer_plc_share','plc_utilization'])
    m=pd.DataFrame(mm,columns=['yyyy_mm','mfr_src_id','operating','scenario_capable','plc_offer_fraction','opc_tons','material_tons','documented_availability_by','evidence_class','offering','offering_documented'])
    m.to_csv(a.out/'E18_manufacturer_monthly_states.csv',index=False)
    # Attribute discontinuities to plant capability/offering changes versus frozen exogenous inputs.
    m=m.sort_values(['mfr_src_id','yyyy_mm']).copy()
    m['capability_change']=m.groupby('mfr_src_id').scenario_capable.diff().fillna(0).ne(0)
    m['offering_change']=m.groupby('mfr_src_id').offering.shift().ne(m.offering)
    m.loc[m.groupby('mfr_src_id').head(1).index,'offering_change']=False
    m['plc_tons_change']=m.groupby('mfr_src_id').material_tons.diff().fillna(0)
    changes=m.groupby('yyyy_mm',as_index=False).agg(
        capability_changes=('capability_change','sum'),offering_changes=('offering_change','sum'),
        plc_tons_change=('plc_tons_change','sum'))
    changes.to_csv(a.out/'E18_monthly_manufacturer_change_diagnostics.csv',index=False)
    m.loc[m.capability_change|m.offering_change|m.plc_tons_change.abs().gt(1e-6),
          ['yyyy_mm','mfr_src_id','evidence_class','offering','scenario_capable','capability_change','offering_change','plc_tons_change']].to_csv(
          a.out/'E18_manufacturer_change_events.csv',index=False)
    s=r.groupby(['yyyy_mm','state'],as_index=False).agg(demand=('D_i','sum'),opc_tons=('opc_tons','sum'),material_tons=('material_tons','sum'),adoption_fraction=('adopted','mean'))
    s['delivered_tons']=s.opc_tons+s.material_tons
    # Denominator is delivered cement. Unmet demand is separately reported.
    s['market_share']=s.material_tons/s.delivered_tons.replace(0,np.nan)
    n=s.groupby('yyyy_mm',as_index=False)[['demand','opc_tons','material_tons','delivered_tons']].sum()
    n['market_share']=n.material_tons/n.delivered_tons.replace(0,np.nan)
    # National shares MUST emerge from state cement quantities, never a fitted national curve.
    check=s.groupby('yyyy_mm')[['material_tons','opc_tons','delivered_tons']].sum()
    for col in ['material_tons','opc_tons','delivered_tons']:
        if not np.allclose(check[col].to_numpy(),n.set_index('yyyy_mm')[col].to_numpy(),rtol=1e-10,atol=1e-5):
            raise RuntimeError(f'State-to-national aggregation failed for {col}')
    national_from_state=(s.assign(weighted_share=s.market_share.fillna(0)*s.delivered_tons).groupby('yyyy_mm').weighted_share.sum()/n.set_index('yyyy_mm').delivered_tons.replace(0,np.nan))
    if not np.allclose(national_from_state.to_numpy(),n.market_share.to_numpy(),equal_nan=True,atol=1e-9):
        raise RuntimeError('National share differs from delivered-ton weighted state shares')
    pd.DataFrame({'yyyy_mm':n.yyyy_mm,'national_share_from_state_weights':national_from_state.to_numpy(),'national_share_from_quantities':n.market_share}).to_csv(a.out/'E18_state_to_national_check.csv',index=False)
    # Mechanism audit: separate observed offerings from structural producer-first scenario.
    primary_count=int((m.offering=='PLC_primary').sum())
    withdrawn_count=int((m.offering=='PLC_only').sum())
    pd.DataFrame([{'documented_primary_plant_months':primary_count,
                   'documented_plc_only_plant_months':withdrawn_count,
                   'warning':'Producer-first is an explicit unidentified scenario, NOT observed manufacturer economics; no retrofit dates inferred' if a.production_policy=='producer_first' else 'OPC-first comparator; not historical reconstruction'}]).to_csv(a.out/'E05_mechanism_audit.csv',index=False)
    print(f'E15: network capability transitions={len(endogenous_events)}; structural hypothesis, NOT validated.')
    # Explicit monthly mass balance between manufacturers and RMXs.
    by_r = r.groupby('yyyy_mm')[['opc_tons','material_tons']].sum()
    by_m = m.groupby('yyyy_mm')[['opc_tons','material_tons']].sum()
    if not np.allclose(by_r.to_numpy(), by_m.to_numpy(), rtol=1e-9, atol=1e-3):
        raise RuntimeError('Manufacturer-to-RMX material mass balance failed')
    balance = n[['yyyy_mm','demand','opc_tons','material_tons','delivered_tons','market_share']].copy()
    balance['unmet_demand_tons'] = balance['demand']-balance['delivered_tons']
    if (balance['unmet_demand_tons'] < -1e-3).any():
        raise RuntimeError('Delivered more cement than requested')
    balance.to_csv(a.out/'E05_material_balance.csv', index=False)
    # Explicitly identify forecast input origin; constant extrapolation is NOT a dynamic forecast.
    if a.integrated_behavior:
        pd.DataFrame(manufacturer_signal_rows).to_csv(a.out/'integrated_manufacturer_signals.csv',index=False)
    pd.DataFrame([{'yyyy_mm':ym,'period':'development' if ym<='2022-12' else 'forecast','demand_dot_input_origin':'observed_development_inputs' if ym<='2022-12' else ('frozen_2022_12' if a.future_exogs=='freeze_2022' else 'user_provided_exogenous_scenario'),'observed_usgs_outcome_used_in_decisions':False} for ym in months]).to_csv(a.out/'E18_input_provenance.csv',index=False)
    pd.DataFrame(interaction_rows).to_csv(a.out/'E18_interaction_diagnostics.csv',index=False)
    pd.DataFrame(mfr_decision_rows).to_csv(a.out/'manufacturer_introduction_decisions.csv',index=False)
    pd.DataFrame(endogenous_events,columns=['yyyy_mm','mfr_src_id','previous_network_plc_tons','eligibility_scenario','interpretation']).to_csv(a.out/'E18_endogenous_capability_events.csv',index=False)
    pd.DataFrame(shipment_rows,columns=['yyyy_mm','mfr_src_id','rmx_src_id','material','allocation_tier','tons']).to_csv(a.out/'manufacturer_rmx_shipments.csv',index=False)
    r.to_csv(a.out/'rmx_monthly_states.csv',index=False)
    m.to_csv(a.out/'mfr_monthly_states.csv',index=False)
    s.to_csv(a.out/'state_month_market_share.csv',index=False)
    n.to_csv(a.out/'national_month_market_share.csv',index=False)
    pd.DataFrame([{'material':a.material,'model_type':'E18 manufacturer-led network feedback; producer_first is an unverified structural upper-envelope scenario, NOT historical reconstruction', 'production_policy':a.production_policy,'announced_conversion_strategy':a.announced_conversion_strategy,'corporate_rollout_scenario':a.corporate_rollout_scenario,'economic_retrofits':a.economic_retrofits,'economic_production':a.economic_production,'manufacturer_economics_file':str(a.manufacturer_economics or ''), 'capability_scenario':a.availability,
        'development_end':'2022-12','manufacturer_transition':'documented evidence plus optional stochastic heterogeneous introduction hypothesis; coefficients not calibrated',
        'manufacturer_offerings_file':str(a.manufacturer_offerings or ''),
        'rmx_requirements_file':str(a.rmx_requirements or ''),'rmx_material_constraints_file':str(a.rmx_material_constraints or ''),'unknown_project_compatibility':'permissive upper feasibility envelope; not documented PLC acceptance',
        'rmx_adoption_events_file':str(a.rmx_adoption_events or ''),
        'production_mix':'No fixed percentages; OPC/PLC shared plant capacity, quantities from constrained requests', 'economic_opportunity':'Each RMX demand is divided equally among accessible operating plants, avoiding duplicated opportunity volume',
        'rmx_choice':'Three-coefficient logistic desired PLC procurement share; coefficients not calibrated; deliveries capacity constrained.',
        'plc03_offering_rule':'Documented PLC-only supplier-led allocation before OPC, documented PLC-primary priority, otherwise PLC responds to orders; structural allocation assumption.', 'rmx_adoption':'No inferred persistent adoption; only independently evidenced operational events; primary outcome PLC utilization',
        'validation':'NOT independently validated; 2023-24 prediction requires frozen inputs before outcome comparison',
        'future_inputs':a.future_exogs if a.end>'2022-12' else 'Development inputs only', 'manufacturer_led_hypothesis':'source-backed PLC_primary priority or PLC_only withdrawal; no arbitrary fractions or timing','rmx_initiated_hypothesis':a.rmx_initiated,'mfr_alpha0':a.mfr_alpha0,'mfr_alpha_market':a.mfr_alpha_market,'mfr_alpha_peer':a.mfr_alpha_peer,'rmx_beta0':a.rmx_beta0,'rmx_beta_dot':a.rmx_beta_dot,'rmx_beta_peer':a.rmx_beta_peer,'seed':a.seed}]).to_csv(a.out/'run_specification.csv',index=False)
    # Audit manufacturer assumptions independently of production quantities.
    m.groupby(['yyyy_mm','evidence_class','offering','offering_documented'],dropna=False).size().rename('plant_months').reset_index().to_csv(a.out/'manufacturer_offering_audit.csv',index=False)
    # Observations are loaded AFTER simulation outputs are saved; they cannot
    # influence agent behavior. Held-out comparisons require an explicit flag.
    obs=None
    if a.observed:
        if a.material!='PLC': raise ValueError('USGS PLC proxy cannot evaluate LC3')
        obs=observed_shares(a.observed)
        # Do not load held-out outcomes into comparisons unless explicitly unlocked.
        obs_end = a.end if a.evaluate_heldout else min(a.end,'2022-12')
        obs=obs[obs.yyyy_mm.astype(str).between(a.start,obs_end)].copy()
        joined=s.merge(obs,on=['yyyy_mm','state'],how='left',validate='one_to_one')
        joined['period']=np.where(joined.yyyy_mm<='2022-12','development','heldout_2023_2024')
        joined['error']=joined.market_share-joined.observed_blended_share
        joined.to_csv(a.out/'state_vs_usgs_proxy.csv',index=False)
        matched=joined.dropna(subset=['error'])
        if not matched.empty:
            scores=matched.groupby(['period','state']).error.agg(
                n='count',bias='mean',mae=lambda x:float(np.abs(x).mean()),
                rmse=lambda x:float(np.sqrt(np.mean(x*x))))
            scores.to_csv(a.out/'state_scorecard.csv')
            totals=matched.groupby('period').error.agg(
                n='count',bias='mean',mae=lambda x:float(np.abs(x).mean()),
                rmse=lambda x:float(np.sqrt(np.mean(x*x))))
            totals.to_csv(a.out/'evaluation_metrics.csv')
        # STATE-FIRST evaluation: this objective is descriptive, NOT a fitted
        # calibration unless identifiable behavioral parameters are supplied.
        dev=joined[(joined.yyyy_mm<='2022-12') & joined.error.notna()].copy()
        if not dev.empty:
            state_errors=dev.groupby('state').error.agg(
                n='count', mse=lambda x:float(np.mean(np.square(x))),
                rmse=lambda x:float(np.sqrt(np.mean(np.square(x)))),
                mae=lambda x:float(np.mean(np.abs(x))), bias='mean').reset_index()
            state_errors.to_csv(a.out/'E18_state_development_errors.csv',index=False)
            # Equal weight per observed state-month, and separate equal-state
            # average, to avoid silently optimizing the national trajectory.
            summary=pd.DataFrame([{
                'period':'2010-01_to_2022-12',
                'objective':'equal_state_month_MSE',
                'value':float(np.mean(np.square(dev.error))),
                'rmse':float(np.sqrt(np.mean(np.square(dev.error)))),
                'equal_state_mean_MSE':float(state_errors.mse.mean()),
                'equal_state_mean_RMSE':float(state_errors.rmse.mean()),
                'states_evaluated':int(len(state_errors)),
                'state_months_evaluated':int(len(dev)),
                'fitted_parameters':0,
                'interpretation':'diagnostic only; USGS blended share is an imperfect PLC proxy'
            }])
            summary.to_csv(a.out/'E18_state_calibration_objective.csv',index=False)
        # National USGS series is weighted by observed tonnage and not fitted.
        obsn=obs.assign(blended_tons=lambda z:z.observed_blended_share*z.total_tons).groupby('yyyy_mm',as_index=False)[['blended_tons','total_tons']].sum()
        obsn['observed_blended_share']=obsn.blended_tons/obsn.total_tons
        n=n.merge(obsn[['yyyy_mm','observed_blended_share']],on='yyyy_mm',how='left')
        n.to_csv(a.out/'national_vs_usgs_proxy.csv',index=False)
    fig,ax=plt.subplots(figsize=(11,5))
    ax.plot(pd.to_datetime(n.yyyy_mm),n.market_share,color='#1769aa',label='Modeled PLC delivery share (structural scenario)')
    if obs is not None:
        ax.plot(pd.to_datetime(n.yyyy_mm),n.observed_blended_share,color='#e07a16',label='USGS blended shipments (imperfect PLC proxy)')
    if a.end>'2022-12': ax.axvline(pd.Timestamp('2023-01-01'),color='gray',ls='--',lw=1,label='Held-out evaluation begins')
    ax.set_ylim(0,1);ax.set_ylabel('Share');ax.set_xlabel('Year')
    scenario_label = 'E15 state-first supply-network scenario' if a.material == 'PLC' else 'LC3 capability scenario'
    ax.set_title(f'{a.material}: modeled capacity-constrained share ({scenario_label})')
    ax.legend(fontsize=8);fig.tight_layout();fig.savefig(a.out/'E18_national_vs_usgs.png',dpi=180);plt.close(fig)
    if True:
        joined=(joined if obs is not None else s).sort_values(['state','yyyy_mm'])
        states = sorted(joined.state.unique())

        if not states:
            raise ValueError(
                "No matching state-month observations between the model and USGS. "
                "Check state identifiers and YYYY-MM date formats. "
                "The simulation outputs were saved successfully."
            )

        cols = 5
        rows = (len(states) + cols - 1) // cols
        fig,axs=plt.subplots(rows,cols,figsize=(19,max(4,rows*2.1)),sharey=True)
        for ax,st in zip(np.asarray(axs).flat,states):
            z=joined[joined.state==st]
            
            if obs is not None: ax.plot(pd.to_datetime(z.yyyy_mm),z.observed_blended_share,color='#e07a16',lw=1,label='USGS proxy')
            if a.end>'2022-12': ax.axvline(pd.Timestamp('2023-01-01'),color='gray',ls='--',lw=.7)
            ax.plot(pd.to_datetime(z.yyyy_mm),z.market_share,color='#1769aa',lw=1,label='Model scenario')
            ax.set_title(st,fontsize=9);ax.set_ylim(0,1);ax.tick_params(axis='x',labelrotation=45,labelsize=7)
        for ax in list(np.asarray(axs).flat)[len(states):]:ax.axis('off')
        fig.suptitle('State market shares: modeled material flows vs broader USGS blended-cement proxy')
        fig.tight_layout();fig.savefig(a.out/'E18_states_vs_usgs.png',dpi=150);plt.close(fig)
    print(f'Wrote {a.out}; {len(months)} months, {len(rids)} RMXs, {len(mids)} MFRs')
    print('2023-24: forecast inputs are explicitly specified; held-out USGS outcomes hidden unless --evaluate-heldout.')
    print('E18: economic decisions are enabled only with sourced inputs; missing plant economics remain unresolved. NOT calibrated or validated.')
    print('Plots: E17_national_vs_usgs.png and E17_states_vs_usgs.png')

if __name__=='__main__':main()
