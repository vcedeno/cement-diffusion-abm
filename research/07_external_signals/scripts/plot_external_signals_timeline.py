#!/usr/bin/env python3
"""Reproduce Module 07 event timeline. Run from repository root."""
import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--input',default='research/07_external_signals/data/external_signals_master.csv');p.add_argument('--output',default='research/07_external_signals/figures/03_external_signals_timeline.png');a=p.parse_args()
df=pd.read_csv(a.input,dtype=str).fillna('')
labels={'01_scientific_technical_evidence':'Technical evidence','02_standards_regulation':'Standards & DOT','03_industry_manufacturing':'Industry & disclosure','04_market_demand_procurement':'Procurement','05_federal_policy_incentives':'Federal policy'}
fig,ax=plt.subplots(figsize=(16,8));colors=plt.rcParams['axes.prop_cycle'].by_key()['color'];cmap={k:colors[i] for i,k in enumerate(labels)}
for i,(cat,label) in enumerate(labels.items()):
 sub=df[df.category==cat].sort_values(['year','date']);seen={}
 for _,r in sub.iterrows():
  yr=int(r.year);j=seen.get(yr,0);seen[yr]=j+1;y=4-i+(j-0.5)*.14
  ax.scatter(yr,y,s=65,c=cmap[cat],edgecolors='white',linewidths=.7,zorder=3)
  ax.annotate(r.signal_id,(yr,y),xytext=(0,7 if j%2==0 else -12),textcoords='offset points',ha='center',fontsize=7)
ax.set_yticks(range(5));ax.set_yticklabels(list(reversed(list(labels.values()))));ax.set_xlim(2002,2027);ax.set_xticks(range(2004,2027,2));ax.set_ylim(-.6,4.7);ax.grid(axis='x',alpha=.25);ax.axvspan(2020,2022.99,color='grey',alpha=.10);ax.set_xlabel('Event year (some dates approximate; labels refer to evidence CSV)');ax.set_title('Documented external signals associated with PLC context, 2004–2025\nEvent inventory, not evidence of causal influence or exhaustive coverage',fontsize=13)
fig.tight_layout();out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,dpi=190)
