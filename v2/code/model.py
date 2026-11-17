"""PLC adoption model: parent firms, cement plants, ready-mix producers, state DOTs and imports.

One call of simulate() runs the monthly model from January 2010 to the end of config.MONTHS.

Agents and decisions (equation numbers refer to docs/model_document.md)
  Parent firm (F)   decides when to start offering PLC (first Type IL anywhere in the firm).        Eq. 1-3
                    Leaders (GCCA members) respond to two dated industry signals and to firm size;
                    followers respond to the PLC share already bought in their customers' states.
  Cement plant (J)  introduces PLC after a within-firm rollout lag (Eq. 4); a leader's plant then
                    withdraws OPC once its DOT gate is open and its customers' loss is tolerable (Eq. 5-6);
                    followers' plants and Type II/V-line plants keep OPC beside PLC. A withdrawing plant
                    reaches full PLC over its documented conversion period (Eq. 7).
  Ready-mix (R)     buys equally from its linked operating plants. Purchases from a PLC-only plant
                    move to OPC with probability sigR while OPC is reachable, fading over H months (Eq. 8);
                    from a plant offering both it buys PLC with probability pi (Eq. 9). Buyers supplied
                    by Type II/V-line plants take PLC with probability scaled by (1 - kiiv * exposure)
                    (Eq. 10). Cement-owned ready-mix buys from its parent's plants.
  State DOT (S)     accepts PLC at a month drawn within its documented window (Eq. 11).
  Imports           a state's import share is ordinary cement; it dilutes the state PLC share (Eq. 12).

Firm decision modes
  prm["firm_form"] = "observed": firm start months are the record (replay; used to calibrate the market layer)
  prm["firm_form"] = "lf"      : leaders/followers start hazard (predictive; used for validation and scenarios)

Random numbers: one generator per run (seed); DOT acceptance months use their own stream
np.random.default_rng([seed, 1]) so scenarios that do not change DOT draws keep identical DOT months.
"""
from __future__ import annotations
import numpy as np
from scipy import sparse
from config import T, midx, PROC_LO, PROC_HI, STANDARD_DATE
from data import ModelData, draw_dot, gate_share


def draw_proc(prm, rng):
    """Procurement-shift start month: fixed by prm['proc_date'] or uniform in Dec 2021 .. Sep 2022."""
    if "proc_date" in prm:
        return midx(prm["proc_date"])
    return int(rng.integers(midx(PROC_LO), midx(PROC_HI) + 1, size=1)[0])


def simulate(d: ModelData, prm: dict, seed: int = 0, acc=None, g_star: float = 0.95) -> dict:
    """Run the model once.

    Parameters (prm)  -- calibrated or estimated values are set by calibrate.py / validate.py
      firm_form   "observed" | "lf"
      lf, lf_cov, lf_a0   leaders/followers coefficients {mem_g, mem_p, mem_size, non_pull}, their covariance
                          (one draw per run; None = no draw) and the pinned intercept (firm_hazard.json)
      sigR        ready-mix switching away from PLC-only supply while OPC is reachable (calibrated)
      H           months over which that switching fades after a buyer first faces PLC-only supply (fixed 18)
      pi0, piL, piD   PLC purchase probability from a plant offering both: base, state-norm, procurement (calibrated)
      kiiv        strength of the Type II/V product-class constraint on buyers (calibrated)
      lC          leaders' withdrawal tolerance, share of customers with an OPC alternative (fixed 1)
      sigma       expected loss per customer with an alternative (fixed 1; cancels against lC)
      follower_keep_opc, iiv_keep, firm_ramp   structural rules (True in the reported model)
      ramp_default    conversion months for firms without evidence (12)
    Scenario options (all optional, see scenarios.py and docs/preliminary_results.md)
      sig_scale1/2, signal_shift, shift1/2, lead_scale, follow_scale, members_extra, force_conv,
      dot_all, sunset, imports_spec, iiv_release, kiiv_release, all_keep_opc, ramp_all, proc_date,
      proc_end, pi_boost
    acc: optional DOT acceptance months per state (overrides the draw).

    Returns dict: A_st (S x T state PLC share of domestic purchases), A_dom (T national domestic share),
      fconv (F firm start months; T = never), intro (J PLC introduction), wd (J OPC withdrawal), acc, proc_t.
    """
    ramp = prm.get("ramp", 12)
    rng = np.random.default_rng(seed)
    acc_draw = draw_dot(d, np.random.default_rng([seed, 1]))
    if acc is None:
        acc = acc_draw
    proc_t = draw_proc(prm, rng)
    LF = prm.get("firm_form") == "lf"
    J, R = d.J, d.R
    lags = d.lags
    draw_lag = lambda: int(rng.choice(lags))                              # within-firm rollout lag (Eq. 4)

    # ---- firm starts known in advance (replay) and plant introduction months
    fconv = np.full(d.F, T) if LF else np.minimum(d.f_obs, T).copy()
    intro = np.minimum(d.prewave.copy(), 10**6)                           # pre-2020 PLC lines offered beside OPC
    for f in range(d.F):
        if fconv[f] >= T:
            continue
        js = np.where(d.plant_firm == f)[0]
        rng.shuffle(js)
        for k, j in enumerate(js):
            intro[j] = min(intro[j], fconv[f] + (0 if k == 0 else draw_lag()))
    intro[~d.eligible] = 10**6
    if prm.get("dot_all") is not None:                                    # scenario: every DOT accepts by a date
        acc = np.minimum(acc, midx(prm["dot_all"]))
    G = gate_share(d, acc)

    sigma, lC = prm.get("sigma", 1.0), prm.get("lC", 1.0)
    sigR, H = prm.get("sigR", sigma), prm.get("H")
    tol = lC * sigma                                                      # leaders' tolerance (Eq. 6)
    white = ~d.eligible                                                   # white-cement plants are not gray-OPC sources
    first_po = np.full(R, 10**6)                                          # first month a buyer faced PLC-only supply
    has_par = np.asarray(d.Aown.sum(1)).ravel() > 0                       # owned ready-mix linked to its parent
    Anon_eff = sparse.diags((~has_par).astype(float)) @ d.Anon            # owned ready-mix buy only from the parent
    pi0, piL, piD = prm.get("pi0", 0.0), prm.get("piL", 0.0), prm.get("piD", 0.0)
    sunset = midx(prm["sunset"]) if prm.get("sunset") else None           # scenario: every eligible plant must withdraw OPC
    imp_spec = midx(prm["imports_spec"]) if prm.get("imports_spec") else None
    wd = np.full(J, 10**6)                                                # OPC withdrawal month (PLC only from then)
    pending = np.full(J, 10**6)
    A_st = np.zeros((d.S, T))
    A_dom = np.zeros(T)
    prev_st = np.zeros(d.S)

    for t in range(T):
        opm = d.op[:, t]
        if LF:                                                            # ---- parent-firm start decisions (Eq. 1-3)
            notyet = fconv >= T
            if t == 0:
                keys = ("mem_g", "mem_p") + (("mem_size",) if "mem_size" in prm["lf"] else ()) + ("non_pull",)
                mu = np.array([prm["lf"][k] for k in keys])
                LFb = rng.multivariate_normal(mu, np.array(prm["lf_cov"])) if prm.get("lf_cov") is not None else mu
                LFb[:-1] = LFb[:-1] * prm.get("lead_scale", 1.0)
                LFb[-1] = LFb[-1] * prm.get("follow_scale", 1.0)
                sh_hist = []
            sh1 = prm.get("shift1", prm.get("signal_shift", 0))
            sh2 = prm.get("shift2", prm.get("signal_shift", 0))
            g1 = float(t >= d.signals[0] - sh1) * prm.get("sig_scale1", 1.0)     # GCCA statement in force
            g2 = float(t >= d.signals[1] - sh2) * prm.get("sig_scale2", 1.0)     # PCA roadmap in force
            lead_term = LFb[0] * g1 + LFb[1] * g2
            if "mem_size" in prm["lf"]:
                lead_term = lead_term + LFb[2] * g1 * d.size_z                 # larger members respond sooner
            mem = d.member.copy()
            if prm.get("members_extra"):                                      # scenario: more firms in the club
                mem[list(prm["members_extra"])] = True
            s3 = np.mean(sh_hist[-3:], axis=0) if sh_hist else np.zeros(d.S)  # 3-month mean state share, after imports
            pull = d.Wf @ s3                                                  # PLC share bought in the firm's customers' states
            U = prm["lf_a0"] + lead_term * mem + LFb[-1] * (~mem) * pull
            U = np.where(t >= midx(prm.get("std_date", STANDARD_DATE)), U, -50.0)
            new = notyet & (rng.random(d.F) < 1.0 / (1.0 + np.exp(-U)))
            for f, tf in prm.get("force_conv", {}).items():                   # scenario: a firm starts at a set month
                if t == tf and notyet[f]:
                    new[f] = True
            for f in np.where(new)[0]:                                        # plants introduce PLC after rollout lags
                fconv[f] = t
                js = np.where(d.plant_firm == f)[0]
                rng.shuffle(js)
                for k, j in enumerate(js):
                    if d.eligible[j]:
                        intro[j] = min(intro[j], t + (0 if k == 0 else draw_lag()))

        # ---- plants that decided earlier start withdrawing OPC this month
        start = pending == t
        wd[start] = t
        offers_opc = opm & (wd > t)
        offers_plc = opm & (intro <= t)
        m_r = d.m_imp[d.rs] if (imp_spec is None or t < imp_spec) else np.zeros(R)   # imported OPC reachable w.p. m
        n_opc = np.asarray(d.A @ (offers_opc & ~white).astype(float)).ravel()

        # ---- plant OPC withdrawal decisions (Eq. 5-6)
        if sunset is not None and t == sunset:
            intro = np.where(d.eligible, np.minimum(intro, sunset), intro)
            offers_plc = opm & (intro <= t)
        cand = d.eligible & offers_plc & offers_opc & (pending >= 10**6) & (G[:, t] >= g_star)
        sun_on = sunset is not None and t >= sunset
        if prm.get("follower_keep_opc") and not sun_on:                   # followers add PLC beside OPC
            cand &= (d.plant_firm < 0) | d.member[np.maximum(d.plant_firm, 0)]
        if prm.get("all_keep_opc") and not sun_on:                        # LC3-type regime: nobody drops the incumbent
            cand &= False
        if prm.get("iiv_keep") and not (prm.get("iiv_release") and t >= midx(prm["iiv_release"])):
            cand &= ~d.iiv                                                # Type II/V-line plants keep OPC
        if not sun_on:                                                    # withdrawal follows the parent's start
            cand &= (d.plant_firm < 0) | (fconv[np.maximum(d.plant_firm, 0)] <= t)
        if cand.any():
            alt = ((n_opc >= 2) + (n_opc == 1) * m_r) * (~has_par)        # customer has another OPC source
            lossj = sigma * np.asarray(d.AT @ (d.dbar * alt)).ravel() / np.maximum(d.den_cust, 1e-12)
            tol_j = np.full(J, np.inf) if sun_on else np.full(J, tol)
            ok = cand & (lossj <= tol_j)
            for j in np.where(ok)[0]:                                     # withdrawal starts 0-6 months after deciding
                pending[j] = t if t == intro[j] else t + int(rng.integers(0, 7))
                if pending[j] == t:
                    wd[j] = t
        offers_opc = opm & (wd > t)
        both = offers_opc & offers_plc
        n_opc = np.asarray(d.A @ (offers_opc & ~white).astype(float)).ravel()

        # ---- ready-mix purchases (Eq. 7-10)
        rmp = np.where(d.ramp_def, prm.get("ramp_default", 12.0), d.ramp_j) if prm.get("firm_ramp") else max(ramp, 1)
        if prm.get("ramp_all") is not None:
            rmp = float(prm["ramp_all"])
        frac = np.clip((t - wd + 1) / rmp, 0, 1) * opm                    # PLC share of a withdrawing plant's output
        nsrc = np.where(has_par, np.asarray(d.Aown @ opm.astype(float)).ravel(), np.asarray(d.A @ opm.astype(float)).ravel())
        proc_on = (t >= proc_t) and (t < midx(prm["proc_end"]) if prm.get("proc_end") else True)
        pi = np.clip(pi0 + piL * prev_st[d.rs] + piD * proc_on, 0, 1)
        if prm.get("pi_boost") is not None:                              # scenario: information / demonstration push
            b, tb = prm["pi_boost"]
            pi = np.clip(pi + b * (t >= midx(tb)), 0, 1)
        keep_out = sigR * (n_opc >= 1)
        if H is not None:                                                 # switching fades as buyers qualify PLC mixes
            po = np.asarray(Anon_eff @ frac).ravel() > 0
            first_po = np.where(po & (first_po >= 10**6), t, first_po)
            keep_out = keep_out * np.clip(1 - (t - first_po) / max(H, 1e-9), 0, 1)
        kv = 0.0 if (prm.get("kiiv_release") and t >= midx(prm["kiiv_release"])) else prm.get("kiiv", 0.0)
        kap = kv * d.iiv_r                                                # product-class constraint (Eq. 10)
        if kv > 0:
            keep_out = np.where(n_opc >= 1, 1 - (1 - keep_out) * (1 - kap), keep_out)
        plc_P = np.asarray(Anon_eff @ frac).ravel() * (1 - keep_out) + np.asarray(d.Aown @ frac).ravel()
        plc_B = (1 - kap) * (pi * np.asarray(Anon_eff @ both.astype(float)).ravel()
                             + np.asarray(d.Aown @ both.astype(float)).ravel())
        share = np.clip(np.where(nsrc > 0, (plc_P + plc_B) / np.maximum(nsrc, 1), 0.0), 0, 1)
        Dt = d.D[t]
        st = np.asarray(d.Sm @ (Dt * share)).ravel() / np.maximum(np.asarray(d.Sm @ Dt).ravel(), 1e-12)
        A_st[:, t] = st
        prev_st = st
        if LF:
            sh_hist.append(st * (1 - d.m_imp))                            # state share after imports (follower pull)
        A_dom[t] = (Dt * share).sum() / Dt.sum()
    return dict(A_st=A_st, A_dom=A_dom, fconv=fconv, intro=intro, wd=wd, acc=acc, proc_t=proc_t)


def national_after_imports(d: ModelData, A_st, m_imp=None, imp_spec_t=None):
    """Eq. 12: state shares diluted by imported OPC (imports meet the PLC spec from imp_spec_t if given).
    Returns the national demand-weighted share (T) and the state shares after imports (S x T)."""
    m = (d.m_imp if m_imp is None else m_imp)[:, None]
    if imp_spec_t is not None:
        tt = np.arange(A_st.shape[1])[None, :]
        A = np.where(tt >= imp_spec_t, A_st * (1 - m) + m, A_st * (1 - m))
    else:
        A = A_st * (1 - m)
    Dst = d.Sm @ d.D.T
    return (A * Dst).sum(0) / Dst.sum(0), A
