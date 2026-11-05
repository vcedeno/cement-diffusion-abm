#!/usr/bin/env python3
"""Regenerate two verified published-scenario charts. Run from any directory."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parents[1]
DATA=BASE/'data'; FIG=BASE/'figures'; FIG.mkdir(exist_ok=True)
def read(name):
 with (DATA/name).open(newline='') as fh: return list(csv.DictReader(fh))
rmi={r['record_id']:r for r in read('lc3_manufacturer_economic_evidence.csv')}
plants=[rmi[f'RMI_PLANT_{i}'] for i in range(1,8)]
vals=[float(r['value']) for r in plants]
labels=[f"Plant {i}\n{r['geography']}" for i,r in enumerate(plants,1)]
fig,ax=plt.subplots(figsize=(10.5,5.3))
ax.bar(range(7),vals)
ax.set_xticks(range(7),labels)
ax.set_ylabel('Modeled cost (USD / metric ton of calcined clay)')
ax.set_title('RMI: modeled calcined-clay cost by region (2024)')
ax.set_ylim(0,51)
for i,v in enumerate(vals): ax.text(i,v+0.8,f'${v:g}',ha='center',fontsize=10)
fig.text(.04,.025,'Plant 7 (North America) is higher; RMI attributes this to higher suitable raw-clay prices.\nSource: RMI (2024), Exhibits 7–8. Modeled cases, not observed U.S. plant costs.',fontsize=9)
fig.tight_layout(rect=(0,.105,1,1));fig.savefig(FIG/'rmi_modeled_calcined_clay_costs.png',dpi=190);plt.close(fig)
rows=read('lc3_clay_sourcing_scenarios.csv')
fig,ax=plt.subplots(figsize=(9.5,5.3))
techs=['Flash calciner','Rotary kiln']
for i,tech in enumerate(techs):
 for j,distance in enumerate([10,200]):
  r=next(r for r in rows if r['technology']==tech and int(r['clay_distance_km'])==distance)
  x=i*3+j
  v=float(r['payback_years']);ax.bar(x,v,width=.85)
  ax.text(x,v+.12,f'{v:g} years',ha='center')
ax.set_xticks([0,1,3,4],['10 km\nFlash','200 km\nFlash','10 km\nRotary','200 km\nRotary'])
ax.set_ylim(0,7);ax.set_ylabel('Modeled payback (years)')
ax.set_title('2019 LC3 greenfield scenario: clay sourcing and payback')
fig.text(.04,.025,'Modeled non-U.S. greenfield case; near/far raw-clay costs: $4/$17 per ton.\nSource: LC3 Financial Attractiveness (2019), Table 1 and §7.5.',fontsize=9)
fig.tight_layout(rect=(0,.105,1,1));fig.savefig(FIG/'clay_sourcing_payback_sensitivity.png',dpi=190);plt.close(fig)
print('Generated 2 source-backed figures in',FIG)
