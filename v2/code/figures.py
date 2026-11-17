"""Figures for docs/preliminary_results.md (written to docs/figures).

  fig1_dot_acceptance.png        state DOT acceptance windows and the demand share in accepting states
  fig2_firm_starts.png           record start month of each parent firm (leaders vs followers)
  fig3_calibration_validation.png national adoption and firm starts: model (predictive) vs record
  fig4_mechanisms_sensitivity.png selected mechanism tests and one-at-a-time sensitivity
Usage: python figures.py [fig1 fig2 fig3 fig4]   (fig3 needs validate.py, fig4 needs scenarios.py output)
"""
from __future__ import annotations
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import ROOT, RESULTS, DERIVED, MONTHS, T_OBS, midx, GCCA_DATE, ROADMAP_DATE
from data import ModelData
from targets import usgs_targets

FIG = ROOT / "docs/figures"; FIG.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, AQUA, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#6b6a66", "#e6e5e1"
plt.rcParams.update({"axes.axisbelow": True, "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200})
X = MONTHS.year + (MONTHS.month - 1) / 12
xm = lambda ym: int(ym[:4]) + (int(ym[5:7]) - 1) / 12


def fig1(d):
    dot = pd.read_csv(DERIVED / "dot_ranges.csv")
    dot["lo"] = dot["not_before"].fillna("2012-01").map(xm); dot["hi"] = dot["accepted_by"].map(xm)
    dot = dot.sort_values(["hi", "lo"]).reset_index(drop=True)
    fig, ax = plt.subplots(1, 2, figsize=(11, 6.2), gridspec_kw=dict(width_ratios=[1.25, 1]))
    a = ax[0]
    for i, r in dot.iterrows():
        exact = r["hi"] - r["lo"] < 0.09
        if r["hi"] < 2012:                                                # accepted before the 2012 standard
            a.plot(2012, i, "<", color=BLUE, ms=4); a.text(2012.15, i, "before 2012", va="center", fontsize=6, color=MUTED)
        elif exact:
            a.plot(r["hi"], i, "o", color=BLUE, ms=4)
        else:
            a.plot([r["lo"], r["hi"]], [i, i], color=BLUE, lw=2.2, alpha=.55, solid_capstyle="round")
            a.plot(r["hi"], i, "|", color=BLUE, ms=6)
    a.set_yticks(range(len(dot))); a.set_yticklabels(dot["state"], fontsize=6)
    a.set_xlim(2011.5, 2025.5); a.invert_yaxis(); a.grid(axis="x", color=GRID, lw=.6)
    a.set_xlabel("Year"); a.set_title("(a) DOT acceptance of Type IL by state", loc="left")
    a.plot([], [], "o", color=BLUE, ms=4, label="Documented acceptance month")
    a.plot([], [], color=BLUE, lw=2.2, alpha=.55, label="Window: not before .. accepted by")
    a.legend(frameon=False, loc="lower left", fontsize=7.5)
    # (b) demand share in accepting states, lower and upper bound, vs national PLC share
    b = ax[1]
    w = np.asarray(d.Sm @ d.D[:T_OBS].sum(0)).ravel(); w = w / w.sum()
    t = np.arange(T_OBS)
    early = (t[None, :] >= np.maximum(d.dot_lo, -1)[:, None]).T @ w
    late = (t[None, :] >= np.maximum(d.dot_hi, d.dot_lo)[:, None]).T @ w
    b.fill_between(X[:T_OBS], late, early, color=BLUE, alpha=.18, lw=0, label="Demand in accepting states (range)")
    b.plot(X[:T_OBS], late, color=BLUE, lw=1.4, label="Latest documented acceptance")
    y = usgs_targets()["nat_net"][:T_OBS]
    b.plot(X[:T_OBS], y, color=INK, lw=1.2, label="National PLC share (USGS, net of 2016-19)")
    for dt, lab in ((GCCA_DATE, "GCCA"), (ROADMAP_DATE, "Roadmap")):
        b.axvline(xm(dt), color=MUTED, lw=.7, ls=":"); b.text(xm(dt) + .05, 1.02, lab, fontsize=7, color=MUTED)
    b.set_xlim(2012, 2026); b.set_ylim(0, 1.05); b.grid(axis="y", color=GRID, lw=.6)
    b.set_xlabel("Year"); b.set_ylabel("Share"); b.set_title("(b) Acceptance came well before adoption", loc="left")
    b.legend(frameon=False, loc="center left", fontsize=7.5)
    plt.tight_layout(); plt.savefig(FIG / "fig1_dot_acceptance.png"); plt.close()


def fig2(d):
    Fm = pd.read_csv(DERIVED / "firms.csv")
    Fm["cap_share"] = d.fcap_share
    Fm["x"] = Fm["observed_first"].map(lambda v: xm(v) if isinstance(v, str) else np.nan)
    Fm = Fm.sort_values(["x", "cap_share"], ascending=[True, False], na_position="last").reset_index(drop=True)
    fig, a = plt.subplots(figsize=(8.6, 5.6))
    for i, r in Fm.iterrows():
        col = BLUE if r["gcca_member"] else ORANGE
        lab = f"{r['parent_2020_22']}  ({100 * r['cap_share']:.1f}%)"
        if np.isnan(r["x"]):
            a.plot(2026.1, i, ">", color=col, ms=5, mfc="white")
        else:
            bound = r["record_basis"].startswith("started by")
            a.plot(r["x"], i, "o", color=col, ms=6, mfc=("white" if bound else col), mew=1.4)
        a.text(2019.05, i, lab, va="center", fontsize=7, color=INK)
    for dt, lab in ((GCCA_DATE, "GCCA statement"), (ROADMAP_DATE, "PCA roadmap")):
        a.axvline(xm(dt), color=MUTED, lw=.8, ls=":"); a.text(xm(dt) + .04, -1.3, lab, fontsize=7, color=MUTED)
    a.set_xlim(2019, 2026.4); a.set_ylim(len(Fm) - .3, -1.8); a.set_yticks([])
    a.spines["left"].set_visible(False); a.grid(axis="x", color=GRID, lw=.6)
    a.set_xlabel("Month of first PLC introduction from 2020 onward (record)")
    a.set_title("Parent firms: start of PLC, leaders (GCCA members) and followers", loc="left")
    for c, l in ((BLUE, "GCCA member (leader)"), (ORANGE, "Not a member (follower)")):
        a.plot([], [], "o", color=c, ms=6, label=l)
    a.plot([], [], "o", color=MUTED, ms=6, label="Dated start"); a.plot([], [], "o", color=MUTED, mfc="white", ms=6, label="'Started by' (document date)")
    a.plot([], [], ">", color=MUTED, mfc="white", ms=5, label="Not started by Dec 2025")
    a.legend(frameon=False, loc="upper right", fontsize=7.5)
    plt.tight_layout(); plt.savefig(FIG / "fig2_firm_starts.png"); plt.close()


def fig3(d):
    CC, NC = np.load(RESULTS / "curves_validation.npy")
    y = usgs_targets()["nat_net"][:T_OBS]
    obs_c = np.array([(d.f_obs <= t).sum() for t in range(T_OBS)])
    bound = (d.firms["record_basis"] == "started by (document date)").to_numpy()
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))
    for i, (a, Y, ob, ylab, ttl) in enumerate(((ax[0], NC, y, "PLC share of US cement", "(a) National adoption"),
                                               (ax[1], CC, obs_c, "Parent firms that have started (of 22)", "(b) Parent firms starting PLC"))):
        Y = Y[:, :T_OBS]
        m, lo, hi = np.median(Y, 0), np.quantile(Y, .1, 0), np.quantile(Y, .9, 0)
        a.axvspan(2023, 2026, color="#eeeeec", zorder=0)
        a.text(2025.9, (0.02 if i == 0 else 0.4), "validation 2023-25\n(not fitted)", ha="right", fontsize=7.5, color=MUTED)
        a.text(2016.1, (0.74 if i == 0 else 20.8), "calibration 2010-22", fontsize=7.5, color=MUTED)
        a.fill_between(X[:T_OBS], lo, hi, color=BLUE, alpha=.16, lw=0, step=("post" if i else None))
        a.plot(X[:T_OBS], m, color=BLUE, lw=1.8, label="Model: median, 10-90% of 100 runs", drawstyle=("steps-post" if i else "default"))
        if i == 0:
            a.plot(X[:T_OBS], ob, color=INK, lw=.7); a.plot(X[:T_OBS], ob, "o", color=INK, ms=1.6, label="USGS record (net of 2016-19 baseline)")
            a.set_ylim(0, 0.8)
        else:
            a.step(X[:T_OBS], ob, color=INK, where="post", lw=1.3, label="Record (firm start)")
            for b_, lab in ((False, "Dated start"), (True, "'Started by' (document date)")):
                ts = sorted(d.f_obs[f] for f in range(d.F) if d.f_obs[f] < T_OBS and bound[f] == b_)
                a.plot(X[ts], obs_c[ts], "o", ms=4, mec=INK, mfc=("white" if b_ else INK), ls="none", label=lab)
            a.set_ylim(0, 22); a.set_yticks(range(0, 23, 2))
        a.set_xlim(2016, 2026); a.set_xlabel("Year"); a.set_ylabel(ylab); a.set_title(ttl, loc="left")
        a.grid(axis="y", color=GRID, lw=.6); a.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0, .93))
    plt.tight_layout(); plt.savefig(FIG / "fig3_calibration_validation.png"); plt.close()


def fig4():
    M = pd.read_csv(RESULTS / "scenarios_mechanisms_summary.csv").set_index("scenario")
    S = pd.read_csv(RESULTS / "scenarios_sensitivity_summary.csv").set_index("scenario")
    mech = [("no_industry_signals", "No industry signals"), ("no_GCCA_effect", "No GCCA effect"),
            ("no_plant_withdraws_OPC", "No plant withdraws OPC"), ("followers_convert_fully", "Followers convert fully"),
            ("no_import_dilution", "No import dilution"), ("no_TypeIIV_rules", "No Type II/V rules"),
            ("no_procurement_response", "No procurement response"), ("no_DOT_gate", "No DOT gate")]
    sens = [("aG_-1SE", "aG_+1SE", "GCCA effect +/-1 SE"), ("aP_-1SE", "aP_+1SE", "Roadmap effect +/-1 SE"),
            ("size_-1SE", "size_+1SE", "Size effect +/-1 SE"), ("aF_-1SE", "aF_+1SE", "Follower pull +/-1 SE"),
            ("sigR_x0.5", "sigR_x1.5", "Ready-mix switching x0.5 / x1.5"), ("imports_x1.5", "imports_x0.5", "Imports x1.5 / x0.5"),
            ("dot_windows_latest", "dot_windows_earliest", "DOT dates latest / earliest"),
            ("default_ramp_18", "default_ramp_6", "Default conversion 18 / 6 months")]
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    a = ax[0]
    v = [M.loc[k, "d_s2030"] * 100 for k, _ in mech]
    a.barh(range(len(mech)), v, color=[BLUE if x >= 0 else ORANGE for x in v], height=.55)
    for i, x in enumerate(v):
        a.text(x + (1 if x >= 0 else -1), i, f"{x:+.0f}", va="center", ha=("left" if x >= 0 else "right"), fontsize=7.5)
    a.set_yticks(range(len(mech))); a.set_yticklabels([l for _, l in mech]); a.invert_yaxis()
    a.axvline(0, color=MUTED, lw=.8); a.set_xlim(-70, 25); a.grid(axis="x", color=GRID, lw=.6)
    a.set_xlabel("Change in 2030 PLC share (percentage points)"); a.set_title("(a) Mechanism tests (one mechanism removed)", loc="left")
    a = ax[1]
    for i, (lo_k, hi_k, lab) in enumerate(sens):
        l, h = S.loc[lo_k, "d_y50"], S.loc[hi_k, "d_y50"]
        a.plot([l, h], [i, i], color=MUTED, lw=1)
        a.plot(l, i, "o", color=ORANGE, ms=5); a.plot(h, i, "o", color=BLUE, ms=5)
    a.set_yticks(range(len(sens))); a.set_yticklabels([s[2] for s in sens]); a.invert_yaxis()
    a.axvline(0, color=MUTED, lw=.8); a.set_xlim(-2, 2); a.grid(axis="x", color=GRID, lw=.6)
    a.plot([], [], "o", color=ORANGE, label="first setting"); a.plot([], [], "o", color=BLUE, label="second setting")
    a.legend(frameon=False, fontsize=7.5, loc="lower right")
    a.set_xlabel("Years earlier (+) or later (-) that national PLC share reaches 50%")
    a.set_title("(b) One-at-a-time sensitivity", loc="left")
    plt.tight_layout(); plt.savefig(FIG / "fig4_mechanisms_sensitivity.png"); plt.close()


if __name__ == "__main__":
    which = sys.argv[1:] or ["fig1", "fig2", "fig3", "fig4"]
    d = ModelData() if set(which) & {"fig1", "fig2", "fig3"} else None
    for w in which:
        (fig4 if w == "fig4" else globals()[w])(*(() if w == "fig4" else (d,)))
        print("wrote", w)
