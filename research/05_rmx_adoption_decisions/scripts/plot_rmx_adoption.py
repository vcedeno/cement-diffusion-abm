#!/usr/bin/env python3
"""Reproduce source-specific descriptive figures from Module 05's master evidence CSV.
Run at repository root: python research/05_rmx_adoption_decisions/scripts/plot_rmx_adoption.py
No external data or manually entered plot counts. Not an adoption-rate analysis.
"""
from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/rmx_adoption_evidence.csv'
OUT = ROOT / 'figures'
OUT.mkdir(parents=True, exist_ok=True)
with DATA.open(newline='', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

def subset(source, categories):
    result = [r for r in rows if source in r['source_url'] and r['evidence_category'] in categories]
    missing = set(categories) - {r['evidence_category'] for r in result}
    if missing: raise ValueError(f'Missing categories from {source}: {missing}')
    if len(result) != len(categories): raise ValueError('Duplicate categories; inspect source rows before plotting')
    return {r['evidence_category']:r for r in result}

def numeric(row):
    try: return float(row['quantitative_value'])
    except ValueError: raise ValueError(f'Non-numeric quantitative_value: {row["evidence_category"]}')

def horizontal_plot(items, title, subtitle, name, xlabel, max_x=None):
    fig, ax = plt.subplots(figsize=(10.8, max(4.6, len(items)*.56+1.8)))
    labels, values = zip(*items)
    bars = ax.barh(range(len(items)), values, color='#337e8c', height=.68)
    ax.set_yticks(range(len(items)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, max_x or max(values)*1.2)
    for b, val in zip(bars, values): ax.text(val+.15 if max_x is None else val+.3, b.get_y()+b.get_height()/2, f'{val:g}', va='center', fontsize=10)
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc='left', fontsize=14, weight='bold', pad=26)
    ax.text(0, 1.025, subtitle, transform=ax.transAxes, fontsize=9, color='#4b5563', va='bottom')
    ax.spines[['top','right','left']].set_visible(False)
    ax.grid(axis='x', alpha=.15)
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=.30, right=.95, top=.78, bottom=.16)
    fig.savefig(OUT/name, dpi=210, bbox_inches='tight', facecolor='white')
    plt.close(fig)

carb = subset('ww2.arb.ca.gov', ['storage_barrier','qualification_barrier','contractor_hesitancy','liability_concern','plc_cost_concern'])
barrier_labels = {'storage_barrier':'Additional storage','qualification_barrier':'Extra testing / processes','contractor_hesitancy':'Contractor hesitation','liability_concern':'Liability concerns','plc_cost_concern':'Cost concerns'}
barriers = sorted([(barrier_labels[k],numeric(v)) for k,v in carb.items()], key=lambda t:-t[1])
horizontal_plot(barriers,'Operational and market barriers reported by California concrete producers (2023)','CARB survey, 2023; multi-select question; 22 survey responses; not plant prevalence.','01_carb_barriers.png','Number of selections',max_x=13)

nr = subset('ascconline.org', ['supply_availability','mix_design_adjustment','strength_performance','admixture_adjustment'])
nr_labels={'supply_availability':'Only PLC available from suppliers','mix_design_adjustment':'Reported 1:1 replacement','strength_performance':'Reported lower 28-day strength','admixture_adjustment':'Increased water-reducer dosage'}
# These values are approximate percentages as stated by the source; do not reconstruct respondent counts.
metrics=[(nr_labels[k],numeric(v)) for k,v in nr.items()]
horizontal_plot(metrics,'Supply conditions and technical adjustments reported by ready-mix producers (2023)','2023 NRMCA phone survey of 22 companies, reported in ACI–ASCC (2024); percentages, not plant shares.','02_nrmca_producer_experiences.png','Reported percentage (%)',max_x=110)

carb_demand = subset('ww2.arb.ca.gov', ['plc_demand_dot_acceptance','plc_demand_owner','plc_demand_absence'])
demand_labels={'plc_demand_dot_acceptance':'Caltrans approval cited','plc_demand_owner':'Owner low-carbon choice cited','plc_demand_absence':'No inquiries / did not sell PLC'}
horizontal_plot([(demand_labels[k],numeric(v)) for k,v in carb_demand.items()], 'Reported demand signals for PLC among California concrete producers (2023)','CARB survey, 2023; distinct response selections, not mutually exclusive or an adoption funnel.','03_carb_demand_signals.png','Number of selections',max_x=10)

# Audit chart: counts of rows by source, not counts of independent adoption decisions.
counts=Counter(r['source_url'] for r in rows)
with (OUT/'04_source_coverage.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['source_url','observation_rows']);w.writerows(sorted(counts.items(),key=lambda kv:-kv[1]))

# Keep source-index for each plotted quantity, so Module 08 can trace claims to original rows.
figure_categories={
 '01_carb_barriers.png':list(barrier_labels),
 '02_nrmca_producer_experiences.png':list(nr_labels),
 '03_carb_demand_signals.png':list(demand_labels),
}
with (OUT/'figure_source_index.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['figure','evidence_category','source_title','source_url','evidence_summary','interpretation_limit'])
    for fig,cats in figure_categories.items():
        for r in rows:
            if r['evidence_category'] in cats:
                w.writerow([fig,r['evidence_category'],r['source_title'],r['source_url'],r['evidence_summary'],r['interpretation_limit']])
print('Created 3 figures, figure_source_index.csv, and 04_source_coverage.csv in', OUT)
