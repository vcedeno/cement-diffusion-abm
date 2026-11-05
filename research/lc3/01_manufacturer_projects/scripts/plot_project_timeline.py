#!/usr/bin/env python3
"""Plot source-reported announcement and projected production years.

Run from repository root:
python research/lc3/01_manufacturer_projects/scripts/plot_project_timeline.py
"""
from pathlib import Path
import csv
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / 'data/documented_project_sites.csv').open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

fig, ax = plt.subplots(figsize=(10, 5.8))
for i, r in enumerate(rows):
    label = f"{r['company']} — {r['location']}, {r['state']}"
    announced = int(r['announcement_year'])
    ax.scatter(announced, i, marker='o', s=60, color='tab:blue', zorder=3)
    if r['announced_start_year']:
        projected = int(r['announced_start_year'])
        ax.plot([announced, projected], [i, i], color='0.45', linewidth=2)
        ax.scatter(projected, i, marker='D', s=65, color='tab:orange', zorder=3)
        ax.text(projected + .12, i, f'{projected} (projected)', va='center', fontsize=8)

ax.set_yticks(range(len(rows)), [f"{r['company']} — {r['location']}, {r['state']}" for r in rows])
ax.invert_yaxis()
ax.set_xlim(2023.4, 2030.5)
ax.set_xticks(range(2024, 2031))
ax.set_xlabel('Year')
ax.set_title('U.S. LC3 and calcined-clay project announcements and projected starts')
ax.scatter([], [], marker='o', color='tab:blue', label='Announcement')
ax.scatter([], [], marker='D', color='tab:orange', label='Published projected start')
ax.legend(loc='lower right')
ax.grid(axis='x', alpha=.25)
fig.tight_layout()
output = ROOT / 'figures/projected_start_timeline.png'
fig.savefig(output, dpi=200, bbox_inches='tight')
print(output)
