#!/usr/bin/env python3
"""Create evidence-only figures from the frozen Module 03 CSVs.
Run: python research/lc3/03_regulations_standards/scripts/plot_regulatory_evidence.py
"""
from pathlib import Path
import csv
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
with open(ROOT/'data/lc3_documented_developments.csv',newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
# Only evidence explicitly describing LC3 DOT testing or DOT research; no DOE manufacturing or calcined-clay-only entries.
states=sorted({r['state_abbr'] for r in rows if r['activity'] in ('LC3 tested','LC3 evaluated for DOT','LC3-related implementation research')})
fig,ax=plt.subplots(figsize=(9,3.6))
ax.barh(states,[1]*len(states))
ax.set_xlim(0,1.2);ax.set_xticks([])
ax.set_xlabel('Documented LC3-specific testing or research (not approval)')
ax.set_title('States with explicit LC3 testing/research in reviewed sources')
for i,s in enumerate(states): ax.text(0.02,i,'NCC 2025 survey' if s!='VA' else 'VTRC 2026 report / project',va='center',color='white',fontweight='bold')
fig.tight_layout(); (ROOT/'figures').mkdir(exist_ok=True);fig.savefig(ROOT/'figures/lc3_specific_state_evidence.png',dpi=200);plt.close(fig)
fig,ax=plt.subplots(figsize=(8,3.5))
ax.barh(['LC3','Calcined clay'],[3,7]);ax.set_xlim(0,9);ax.set_xlabel('Survey responses (n=33; categories can overlap)');ax.set_title('Emerging materials tested — NCC Spring 2025 survey, Q8')
for i,v in enumerate([3,7]): ax.text(v+.15,i,str(v),va='center')
fig.tight_layout();fig.savefig(ROOT/'figures/ncc_2025_tested_materials.png',dpi=200);plt.close(fig)
print('Figures created in',ROOT/'figures')
