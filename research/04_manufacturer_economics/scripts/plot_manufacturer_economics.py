#!/usr/bin/env python3
"""Reproduce descriptive figures from Module 04 manufacturer evidence.
No paraphrase is presented as a direct quotation. Counts represent records, not plants.
"""
from pathlib import Path
import argparse
import textwrap
import pandas as pd
import matplotlib.pyplot as plt

p=argparse.ArgumentParser()
p.add_argument('--csv',type=Path,default=Path('research/04_manufacturer_economics/data/manufacturer_economics_evidence.csv'))
p.add_argument('--outdir',type=Path,default=Path('research/04_manufacturer_economics/figures'))
a=p.parse_args();a.outdir.mkdir(parents=True,exist_ok=True)
d=pd.read_csv(a.csv).fillna('')
d['year']=pd.to_numeric(d['source_date'].astype(str).str[:4],errors='coerce')
# Only PLC-specific manufacturer statements; retrospective industry report excluded.
q=d[(d['plc_specific'].astype(str).str.lower()=='yes') & (~d['company'].astype(str).str.contains('US cement manufacturers',case=False))].sort_values(['year','company']).copy()
# Figure 1: source-grounded summaries, not invented verbatim quotes.
fig,ax=plt.subplots(figsize=(15, max(7,len(q)*1.05+1.6)))
ys=list(range(len(q)))[::-1]
ax.scatter(q['year'],ys,s=70,zorder=3)
for y,(_,r) in zip(ys,q.iterrows()):
    summary=str(r['evidence_summary']).strip()
    # Short summary with no quotation marks; full wording and URL in CSV.
    short=textwrap.shorten(summary,width=115,placeholder='…')
    ax.annotate(f"{r['company']} ({r['source_date']})\n{short}", (r['year'],y),xytext=(12,0),textcoords='offset points',va='center',fontsize=9)
ax.set_xlim(2009,2038);ax.set_ylim(-1,len(q));ax.set_yticks([]);ax.set_xticks([2010,2012,2014,2016,2018,2020,2022,2024]);ax.grid(axis='x',alpha=.25)
ax.set_xlabel('Source publication year');ax.set_title('Documented manufacturer statements about PLC: historical timeline',loc='left',fontweight='bold',pad=16)
fig.text(.12,.045,'Paraphrased source summaries, not verbatim quotations. See CSV for original source links. Dates reflect publication, not necessarily adoption.',fontsize=9)
fig.subplots_adjust(left=.12,right=.96,bottom=.11,top=.91)
fig.savefig(a.outdir/'plc_manufacturer_motivations_timeline.png',dpi=180,bbox_inches='tight');plt.close(fig)
# Figure 2: one primary thematic label per PLC-specific manufacturer record.
def category(r):
 s=str(r['economic_mechanism']).lower()
 if 'margin' in s or 'clinker input cost' in s:return 'Clinker costs / margins'
 if 'standard' in s or 'dot acceptance' in s:return 'Standards / market access'
 if 'demonstration' in s:return 'Product testing / demonstration'
 if 'differentiation' in s or 'carbon' in s or 'emissions' in s:return 'Lower-carbon product strategy'
 if 'scale' in s:return 'Production scale-up'
 return 'Other reported rationale'
q['theme']=q.apply(category,axis=1)
counts=q['theme'].value_counts().sort_values()
fig,ax=plt.subplots(figsize=(10,5.5));bars=ax.barh(counts.index,counts.values)
for b in bars:ax.text(b.get_width()+.06,b.get_y()+b.get_height()/2,str(int(b.get_width())),va='center')
ax.set_xlim(0,max(counts.values)+1);ax.set_xlabel('Number of source observations');ax.set_title('Themes documented in PLC-specific manufacturer evidence',loc='left',fontweight='bold')
fig.text(.12,.015,'Descriptive coding of source records; not counts of manufacturers or causal importance. One primary theme per observation.',fontsize=9)
fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(a.outdir/'plc_manufacturer_economic_mechanisms.png',dpi=180,bbox_inches='tight');plt.close(fig)
print(f'Plotted {len(q)} PLC-specific manufacturer records from {len(d)} total observations into {a.outdir}')
