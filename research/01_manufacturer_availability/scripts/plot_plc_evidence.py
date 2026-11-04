#!/usr/bin/env python3
"""National and state-level summaries of public PLC manufacturer evidence."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data/mfr_plc_public_evidence_audit_completed.xlsx"
OUTPUT = ROOT / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(INPUT, sheet_name="Plant Evidence Audit")

assert len(df) == 100
assert df["mfr_src_id"].is_unique

def classify(status):
    if status == "Direct plant evidence":
        return "Plant-specific evidence"

    if status in [
        "Company-level evidence",
        "Company/state-level evidence",
        "Company/plant-current evidence",
    ]:
        return "Broader company evidence"

    if status in [
        "No PLC evidence found",
        "No plant-specific evidence",
        "No plant-level public evidence identified",
        "No PLC evidence / contrary current evidence",
    ]:
        return "No plant-specific evidence found"

    raise ValueError(f"Unrecognized evidence status: {status}")

df["category"] = df["evidence_status"].apply(classify)

categories = [
    "Plant-specific evidence",
    "Broader company evidence",
    "No plant-specific evidence found",
]

colors = {
    "Plant-specific evidence": "#287A62",
    "Broader company evidence": "#4F86C6",
    "No plant-specific evidence found": "#AAB4C3",
}

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

def save(fig, name):
    fig.savefig(OUTPUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

# National evidence

counts = df["category"].value_counts().reindex(
    categories, fill_value=0
)

fig, ax = plt.subplots(figsize=(9, 4))

bars = ax.barh(
    categories,
    counts.values,
    color=[colors[c] for c in categories]
)

ax.bar_label(bars, padding=5)
ax.invert_yaxis()
ax.set_xlabel("Number of cement plants")
ax.set_title("Public PLC manufacturer evidence — United States")
ax.set_xlim(0, counts.max() * 1.18)

fig.tight_layout()
save(fig, "plc_evidence_national")

# State-level evidence

state = pd.crosstab(df["state"], df["category"])
state = state.reindex(columns=categories, fill_value=0)
state = state.loc[state.sum(axis=1).sort_values(ascending=False).index]

fig, ax = plt.subplots(
    figsize=(10, max(7, len(state) * 0.32))
)

left = pd.Series(0, index=state.index)

for category in categories:
    ax.barh(
        state.index,
        state[category],
        left=left,
        label=category,
        color=colors[category]
    )
    left += state[category]

ax.invert_yaxis()
ax.set_xlabel("Number of cement plants")
ax.set_title("Public PLC manufacturer evidence by state")

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, -0.05),
    ncol=1,
    frameon=False
)

fig.tight_layout()
save(fig, "plc_evidence_by_state")

print("\nNational evidence summary:")
print(counts.to_string())

print("\nStates represented:", len(state))
print("Manufacturers:", len(df))
print("\nFigures saved in:", OUTPUT)
