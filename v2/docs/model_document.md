# PLC adoption model: model document

This document defines every agent, decision, equation, variable, parameter and assumption of the model, and links each one to the evidence in `evidence_ledger.md` (item IDs in brackets, for example [S1]) and to the code in `code/`. Results are in `preliminary_results.md`.

---

## 1. Scope

The model reproduces the US transition from ordinary portland cement (OPC, ASTM C150 Type I/II) to portland-limestone cement (PLC, ASTM C595 Type IL) from January 2010 to December 2025, monthly, at the level of 22 parent firms, 100 cement plants, 3,667 ready-mix plants in 47 states with demand in the network (DOT windows cover all 50 states). It is designed so that the same decision structure can be applied to limestone calcined clay cement (LC3) by changing product attributes and a few rules (section 9).

Outcome: the PLC share of cement purchased in each state and nationally, after imports, compared with the USGS share of blended cement net of its 2016-19 level [E5, V1, V2]; and the month in which each parent firm starts its PLC transition [V3]. A firm's start is its first PLC introduction from 2020 onward; niche PLC lines that predate 2020 (Devil's Slide since 2006, Lyons since about 2007 [E3]) are treated as existing products offered beside OPC, not as starts.

## 2. Agents, states and time

| Agent | Number | State variables | Decision |
|---|---|---|---|
| Parent firm f | 22 | started (yes/no), start month | When to start offering PLC (Eq. 1-3) |
| Cement plant j | 100 (98 eligible) | offers OPC, offers PLC, OPC withdrawal month, conversion progress | When PLC is introduced (Eq. 4); whether and when OPC is withdrawn (Eq. 5-7) |
| Ready-mix plant r | 3,667 | PLC share of purchases, first month facing PLC-only supply | Which product to buy from each linked plant (Eq. 8-10) |
| State DOT s | 47 in the network (50 documented) | acceptance month | Accepts Type IL at a month within its documented window (Eq. 11) |
| Imports | by state | import share m_s | Imported cement is OPC (Eq. 12) |

Time step: one month. Calibration window 2010-01 to 2022-12; validation window 2023-01 to 2025-12; scenario horizon to 2035-12.

Network: a ready-mix plant r is linked to the cement plants that can supply it (matrix A, from `original_data/mfr_rmx_pairs.csv`). Monthly ready-mix demand D_r(t) comes from `original_data/rmx_month_demand_exposure.csv.gz` for 2010-2024; for 2025, the 2024 profile of each ready-mix plant is scaled by its state's USGS shipment ratio for the same month (`data.py`).

## 3. Inputs

| File | Origin | Content |
|---|---|---|
| `original_data/mfr_capacity_for_model.csv` | cement-diffusion-abm repository | Plants, capacity, operating period, type |
| `original_data/mfr_rmx_pairs.csv` | cement-diffusion-abm repository | Supply links between cement and ready-mix plants |
| `original_data/rmx_month_demand_exposure.csv.gz` | cement-diffusion-abm repository (gzip of the original csv) | Monthly ready-mix demand, 2010-2024 |
| `original_data/usgs_all_state_type_month.csv` | cement-diffusion-abm repository | USGS shipments by state, type and month, 2002-2024 |
| `original_data/dots.csv` | cement-diffusion-abm repository | State names and codes |
| `original_data/readymix_final_for_network.csv` | cement-diffusion-abm repository | Ready-mix facility list |
| `new_data/evidence/plant_plc_evidence.csv` | compiled for this model | Plant-level PLC evidence: first date, type of document, confidence, source, full-conversion notes |
| `new_data/evidence/dot_acceptance_evidence.csv` | compiled for this model | State DOT acceptance window, status, evidence, source |
| `new_data/plant_conversion_evidence.csv` | compiled for this model | Conversion speed by firm and Type II/V product line by plant, with sources |
| `new_data/firm_attributes.csv` | compiled for this model | GCCA membership; whether the record start is a dated start or a document date |
| `new_data/imports_by_customs_district.csv` | compiled from USGS Minerals Yearbook | Imports by customs district, 2022-2023, destination states |
| `new_data/readymix_owner_assignment.csv` | compiled for this model | Cement firm owning each ready-mix plant (facility-name match to subsidiary brands) |
| `new_data/usgs_2025/` | transcribed from USGS MIS Dec 2025 | 2025 monthly shipments by destination, portland and blended |
| `new_data/derived/` | built by `code/build_inputs.py` | Model-ready tables (plants, firms, DOT windows, rollout lags, USGS 2002-2025, import shares, owners) |

## 4. Equations

Notation: 1[.] is an indicator; logistic(u) = 1 / (1 + e^(-u)); all quantities are monthly.

### 4.1 Parent firm: start of PLC

**Eq. 1. Start hazard (leaders and followers).** For a firm f that has not started, at month t from January 2012:

    logit h_f(t) = a0
                 + M_f [ aG g1(t) + aP g2(t) + aS g1(t) z_f ]
                 + (1 - M_f) aF P_f(t)

| Symbol | Meaning | Code |
|---|---|---|
| M_f | 1 if f is a GCCA member (leader), 0 otherwise (follower) [S3] | `ModelData.member` |
| g1(t) | 1[t >= Sep 2020], GCCA 2050 Climate Ambition in force [S1] | `g1` in `simulate` |
| g2(t) | 1[t >= Oct 2021], PCA Roadmap in force [S2] | `g2` |
| z_f | standardised log capacity share of firm f [S8, S9] | `ModelData.size_z` |
| P_f(t) | follower pull: PLC share bought in the firm's customers' states, after imports, mean of months t-1 .. t-3 [H4] | `pull` |
| a0 | intercept, pinned (Eq. 2) | `lf_a0` |
| aG, aP, aS, aF | coefficients, estimated (Eq. 3) | `lf` |

    P_f(t) = sum_s W_fs * (1/3) sum_{k=1..3} x_s(t-k) (1 - m_s)

W_fs is the capacity-weighted share of firm f's customers' demand located in state s (`ModelData.firm_customer_weights`), x_s the state's domestic PLC share (Eq. 10), m_s its import share (Eq. 12).

Before January 2012 (the Type IL standard [E2]) the hazard is zero. Each month a firm starts with probability h_f(t). Once started it stays started.

**Eq. 2. Intercept.** No firm started alone between January 2012 and August 2020 [S7]. The intercept is pinned so that the expected number of solo starts over that period is S0:

    logistic(a0) = S0 / N_pre,   S0 = 0.5 (main), 0.15 and 1.5 (sensitivity)

N_pre is the number of firm-months at risk before September 2020 (`firm_hazard.fit`).

**Eq. 3. Estimation.** aG, aP, aS and aF are estimated by maximum likelihood on the firm-month panel, January 2012 to December 2022 (22 firms, 2,733 firm-months, 15 starts). The panel's follower pull uses the observed USGS state shares (net of the 2016-19 baseline), not model output. In each model run the four coefficients are drawn once from their estimated covariance (`firm_hazard.py`, `results/firm_hazard.json`).

**Replay mode.** For calibrating the market layer only, firm start months are set to the record (`firm_form = "observed"`). They are never set to the record in validation or scenario runs.

### 4.2 Cement plant: introduction, withdrawal and conversion

**Eq. 4. Introduction.** When firm f starts at month t_f, its eligible plants are put in random order. The first introduces PLC at t_f. Each other plant introduces PLC at t_f + l, with l drawn from the 27 observed within-firm lags of the 2020-22 wave [P5, S11]. Plants with documented PLC before 2020 offer PLC beside OPC from their documented date [E3]. White-cement plants never offer PLC [P7].

**Eq. 5. Withdrawal candidates.** In month t, plant j is a candidate to withdraw OPC if all of the following hold:
- it is eligible, operating, and offers both OPC and PLC;
- its parent has started (t >= t_f);
- its DOT gate is open: G_j(t) >= 0.95, where G_j(t) is the demand-weighted share of j's customers located in states whose DOT has accepted PLC (Eq. 11) [G1, G2];
- its parent is a GCCA member: followers keep OPC beside PLC [H1, H2];
- it is not a Type II/V product-line plant: those plants keep OPC [W1, W2, W6].

**Eq. 6. Withdrawal condition.** A candidate withdraws if the share of its customers' demand that could still buy OPC elsewhere, scaled by the expected loss per such customer, is within its parent's tolerance:

    L_j(t) = sigma * sum_r A_rj dbar_r alt_r(t) / sum_r A_rj dbar_r  <=  lC

alt_r(t) = 1 if r has at least two OPC sources, m_s(r) if exactly one, 0 if r is owned by a cement firm. With sigma = 1 and lC = 1 (section 5) the condition always holds, so in the reported calibration a leader's plant withdraws as soon as Eq. 5 holds. The withdrawal starts 0 to 6 months (uniform) after the decision, or immediately if the decision month is the introduction month.

**Eq. 7. Conversion ramp.** After withdrawal at month w_j, the PLC share of plant j's output rises linearly:

    phi_j(t) = min(1, max(0, (t - w_j + 1) / rho_j))

rho_j is the documented conversion period of j's parent [P4] (1 month for Buzzi, Summit, GCC; 6 for Holcim, Heidelberg; 12 for Argos, Titan; 24 for Cemex; 12 where no firm-level evidence exists).

### 4.3 Ready-mix plant: purchases

A ready-mix plant buys equal amounts from each linked operating cement plant (a plant owned by a cement firm buys only from its parent's plants) [B3]. From each linked plant it buys PLC with the following probabilities.

**Eq. 8. Purchases from a plant that has withdrawn OPC.** The PLC share phi_j(t) is bought as PLC, except that while the buyer can still reach OPC it moves a share of those purchases to OPC (transitional switching) [B1, B2]:

    kappa_r(t) = sigR * 1[n_r(t) >= 1] * max(0, 1 - (t - t0_r) / H)

n_r(t) is the number of r's linked plants still offering OPC (white-cement plants excluded), t0_r the first month r faced PLC-only supply, H the qualification period after which switching stops.

**Eq. 9. Purchases from a plant offering both.**

    pi_r(t) = min(1, pi0 + piL * x_s(r)(t-1) + piD * 1[t >= t_proc])

pi0 is a base rate, piL a state-norm effect, piD the effect of the procurement shift [M1-M5]; t_proc is drawn uniformly per run between December 2021 and September 2022 [M2]. A cement-owned ready-mix plant buys PLC from its parent's plants as soon as they offer it.

**Eq. 10. Product-class constraint.** Buyers supplied by Type II/V-line plants take PLC less [W1-W6]. With exposure e_r = share of r's links to Type II/V-line plants:

    k_r = kiiv * e_r
    kappa'_r(t) = 1 - (1 - kappa_r(t)) (1 - k_r)   if n_r(t) >= 1
    purchases from plants offering both are multiplied by (1 - k_r)

Ready-mix PLC share and state domestic share:

    y_r(t) = [ sum_j Anon_rj phi_j (1 - kappa'_r) + sum_j Aown_rj phi_j
               + (1 - k_r) ( pi_r sum_j Anon_rj b_j + sum_j Aown_rj b_j ) ] / N_r(t)
    x_s(t) = sum_{r in s} D_r(t) y_r(t) / sum_{r in s} D_r(t)

Anon and Aown are the links of independent and cement-owned ready-mix plants, b_j = 1 if j offers both, N_r(t) the number of linked operating plants.

### 4.4 DOT acceptance

**Eq. 11.** State s accepts Type IL at a month drawn uniformly within its documented window [lo_s, hi_s] [G1]; lo_s is the 2012 standard where no "not before" date exists. Draws use their own random stream so that scenarios share DOT months.

### 4.5 Imports and national share

**Eq. 12.** Imported cement is treated as OPC [I1, I2, I4]. The state share after imports and the national share are

    X_s(t) = x_s(t) (1 - m_s)
    X(t) = sum_s D_s(t) X_s(t) / sum_s D_s(t)

m_s is the 2022 import share of state s: imports by customs district [I1], times 0.75 (cement share of cement and clinker imports), allocated to the district's destination states by 2022 consumption, capped at 0.6; Canadian-border districts are excluded [I5]. Only 2022 volumes are used, so no validation-window data enter.

## 5. Parameters

| Symbol | Code | Value | How set | Evidence |
|---|---|---|---|---|
| a0 | `lf_a0` | -8.43 (S0 = 0.5); -9.63 / -7.33 for S0 = 0.15 / 1.5 | Pinned (Eq. 2) | S7 |
| aG | `mem_g` | 3.86 (s.e. 0.74) | Estimated, firm panel 2012-22 | S1, S3, S4 |
| aP | `mem_p` | 2.76 (0.74) | Estimated | S2, S5, S6 |
| aS | `mem_size` | 1.03 (0.47) | Estimated | S8, S9 |
| aF | `non_pull` | 23.7 (2.3) | Estimated | H4 |
| GCCA date, roadmap date | `GCCA_DATE`, `ROADMAP_DATE` | 2020-09, 2021-10 | Evidence | S1, S2 |
| Earliest start | `STANDARD_DATE` | 2012-01 | Evidence | E2 |
| Rollout lags | `rollout_lags.csv` | 27 lags, median about 6 months | Evidence | P5 |
| DOT gate threshold | `g_star` | 0.95 | Fixed | G1, G2 |
| sigma, lC | `sigma`, `lC` | 1, 1 | Fixed (withdrawal follows Eq. 5) | P1, P2 |
| Withdrawal delay | in `simulate` | 0-6 months, uniform | Fixed | P1 |
| rho_j | `ramp_months` | 1 / 6 / 12 / 24; default 12 | Evidence | P4 |
| sigR | `sigR` | 0.63 (20 sets: 0.61-0.66) | Calibrated | B1 |
| H | `H` | 18 months | Fixed | B2 |
| pi0 | `pi0` | 0.001 (0.000-0.003) | Calibrated | B4 |
| piL | `piL` | 0.001 (0.000-0.004) | Calibrated | B4 |
| piD | `piD` | 0.10 (0.09-0.13); near-equal fits 0.00-0.25 | Calibrated, weakly identified | M1-M5 |
| t_proc | `PROC_LO`, `PROC_HI` | uniform Dec 2021 - Sep 2022 | Evidence | M2 |
| kiiv | `kiiv` | 0.999 (0.97-1.00) | Calibrated | W1-W6 |
| m_s | `import_share_2022.csv` | 0-0.6 by state | Evidence and assumption | I1-I5 |
| Cement share of imports | `CEMENT_SHARE` | 0.75 | Assumption | I1 |

## 6. Assumptions

| ID | Assumption | Evidence | Where |
|---|---|---|---|
| A1 | The decision to offer PLC is made by the parent firm, and plants follow within the firm | S11, P1, S6 | Eq. 1, 4 |
| A2 | GCCA members (leaders) respond to two dated industry signals; non-members (followers) respond to the market in their customers' states | S1-S6, H1, H4 | Eq. 1 |
| A3 | Larger leaders respond sooner to the GCCA statement | S8, S9 | Eq. 1 |
| A4 | Solo starts without signals or market pull are rare: 0.5 expected in 2012-20 (0.15 and 1.5 tested) | S7 | Eq. 2 |
| A5 | No firm starts before the 2012 Type IL standard | E2 | Eq. 1 |
| A6 | Within-firm rollout lags follow the 2020-22 wave | P5, S11 | Eq. 4 |
| A7 | Leaders' plants withdraw OPC once the DOT gate is open; followers' plants keep OPC beside PLC | P1, P2, H1, H2 | Eq. 5-6 |
| A8 | Type II/V product-line plants keep OPC; buyers supplied by them take PLC much less | W1-W6 | Eq. 5, 10 |
| A9 | Conversion periods follow documented firm statements; 12 months where none exist | P4 | Eq. 7 |
| A10 | Ready-mix plants split purchases equally across linked operating plants; cement-owned ready-mix buy from the parent | B3 | Eq. 8-10 |
| A11 | Ready-mix plants move PLC-only purchases to OPC while OPC is reachable, for up to H = 18 months | B1, B2 | Eq. 8 |
| A12 | Procurement raises PLC purchases from plants offering both, from a month drawn in Dec 2021 to Sep 2022 | M1-M5 | Eq. 9 |
| A13 | A DOT accepts at a month uniformly distributed within its documented window | G1 | Eq. 11 |
| A14 | Imported cement is OPC; 2022 import shares hold through the horizon; Canadian imports excluded | I1-I5 | Eq. 12 |
| A15 | 2025 ready-mix demand follows the 2024 profile scaled by state shipments | V2 | `data.py` |
| A16 | Record firm start dates that are document dates are upper bounds | V3, V4 | `validate.firm_scores` |

## 7. Calibration and validation

**Two layers, identified separately.**
1. Firm layer (Eq. 1-3): estimated directly from the firm-month record 2012-2022 (`firm_hazard.py`). No adoption-curve fitting.
2. Market layer (Eq. 4-12): calibrated on 2010-2022 with firm starts replayed from the record, so the market parameters are not distorted by firm-timing error (`calibrate.py`).

**Calibration (market layer).** Free parameters sigR, piL, piD, pi0, kiiv. Loss:

    L = mean_t (X(t) - X_obs(t))^2                                   t = 2010-01 .. 2022-12
      + 0.01 * sum_s w_s mean_y (X_s,y - X_s,y,obs)^2                y = 2020, 2021, 2022

w_s is the state's share of 2010-22 demand; X_s,y annual state shares after imports. The state term has a small weight so that the national curve leads. Each trial averages 8 simulations with seeds 0-7 (common random numbers); search by Optuna TPE (multivariate, seed 20261107), 1,500 trials. The 20 trials within 10% of the best loss form the parameter sets.

**Validation (predictive model).** Firm starts predicted by Eq. 1 (coefficients drawn per run), market layer from the 20 parameter sets, 5 seeds each (100 runs). Compared with the record:
- national share: RMSE over 2010-2022 (fit) and over 2023-2025 (forecast, never used in fitting);
- 2025 level, state shares in 2022 and 2025 (demand-weighted RMSE);
- firm starts: number of firms by 2025; timing error per firm, where for document-dated record starts only a model start later than the record counts as an error [V3]; expected number of firms that start in the model but not in the record.

## 8. Mapping: evidence to mechanism to equation

| Mechanism | Evidence | Equation | Parameter or rule | Assumption |
|---|---|---|---|---|
| Industry coordination signals trigger leaders | S1, S2, S5, S6 | 1 | aG, aP, signal dates | A2 |
| Club membership separates leaders and followers | S3, S4 | 1 | M_f | A2 |
| Size shapes which leaders move first | S8, S9 | 1 | aS | A3 |
| Followers respond to their customers' market | H1, H4 | 1 | aF, P_f | A2 |
| No solo starts before the signals | S7 | 2 | a0 | A4 |
| Standard as a precondition | E2 | 1 | 2012-01 | A5 |
| Fleet decision with within-firm rollout | S11, P1, P5 | 4 | rollout lags | A1, A6 |
| OPC withdrawal by leaders forces adoption | P1, P2, P3 | 5, 6 | lC, sigma | A7 |
| Followers add PLC beside OPC | H1, H2 | 5 | `follower_keep_opc` | A7 |
| Product class: Type II/V markets | W1-W6 | 5, 10 | `iiv_keep`, kiiv | A8 |
| Documented conversion speed | P4 | 7 | rho_j | A9 |
| Buyer friction during the switch | B1, B2 | 8 | sigR, H | A11 |
| Procurement as a reinforcer | M1-M5 | 9 | piD, t_proc | A12 |
| DOT acceptance as a permissive gate | G1, G2 | 5, 11 | g_star, windows | A13 |
| Imports as an OPC channel | I1-I5 | 12 | m_s | A14 |

Factors examined and not included, with the evidence: parent climate-commitment dates as firm-specific triggers (they read back the start dates and do not order them [S5]); experience abroad and earlier group targets [S10]; follower size [S10]; local supply tightness (not supported; low-tightness plants converted more often); local competitor imitation (weak [S11]); capacity-weighted purchasing (worse forecast); a slower, censored rollout distribution (rejected by the national record); imports carrying the domestic PLC share (2025 share 0.74 vs 0.62).

## 9. Adapting the model to LC3

The decision structure carries over; product attributes and three rules change.

| Element | PLC | LC3 adaptation | Evidence |
|---|---|---|---|
| Product class | Type IL replaces Type I/II one for one | Type IT (C595) for general use; specialty classes need their own qualification (as Type II/V for PLC) | L1, W5 |
| Incumbent withdrawal | Leaders' plants withdraw OPC (Eq. 5-6) | No plant withdraws the incumbent at first: `all_keep_opc = True`; LC3 is offered beside PLC/OPC | L1, L4 |
| Firm decision | Signals and pull, no capital term | Add a capital barrier K to Eq. 1 for a calciner and clay supply; one calciner decision per plant; build time 24-48 months | L2, L3 |
| Buyer choice | pi from plants offering both (Eq. 9) | Becomes the main adoption channel; pi0, piL, piD set by scenario because the PLC record does not identify them | B4, M5 |
| DOT acceptance | Exogenous window (Eq. 11) | Endogenous: acceptance follows local supply decisions with a lag | L3, L5 |
| Imports | OPC | OPC and PLC imports remain an alternative | I1-I5 |
| Calibration | PLC record 2010-25 | Capital barrier K fitted to the observed LC3 decisions (Troutville, Louisville, Summit) | L3 |

Implementation in the code: `all_keep_opc`, `kiiv_release`, `sunset`, `piD`, `piL`, `pi_boost` are already options of `model.simulate`; the capital barrier and endogenous DOT acceptance are additions (see `preliminary_results.md`, section 7).

## 10. Limitations

1. **Leader timing before the roadmap.** All members share one hazard before October 2021 apart from the size term, so the model spreads the first leaders' starts; CalPortland (record Nov 2020) and Holcim (Dec 2020) start in late and mid 2021 in the median run.
2. **Follower holdouts.** The follower hazard rises steeply with the pull; three small firms that never started (Armstrong, the Texas Lehigh joint venture, UNACEM; together 2% of capacity) start in most runs, and Mitsubishi (started Oct 2024) rarely starts. The 2012-22 data contain too few follower starts (4) to estimate firm heterogeneity.
3. **Plant-specific laggards.** Some leader plants (for example Ravena NY) still lack Type IL years after their parent started [P6]; the model's rollout cannot predict which plants lag, so New York and Pennsylvania are too high.
4. **Southwest.** The buyer constraint is close to complete through 2022 and does not erode afterwards; California and Nevada are too low in 2025.
5. **Procurement response (piD) is weakly identified** by 2010-22 data (near-equal fits from 0 to 0.25); results that depend on it are reported as ranges.
6. **Network.** Equal purchasing across links gives small plants large shares in some states; the network routes Minnesota only to one plant (GCC's Rapid City supply is not linked).
7. **Imports** are all OPC; some integrated firms' terminals import Type IL [I4].
8. **Record dates** are document dates for 13 of 18 firms; true starts are earlier or equal.

## 11. Code map

| File | Content |
|---|---|
| `config.py` | Paths, time axis, signal dates, procurement window, calibration constants |
| `build_inputs.py` | Builds `new_data/derived/` from original and new data |
| `data.py` | `ModelData`: loads all inputs; DOT draws; DOT gate |
| `model.py` | `simulate()`: Eq. 1-11; `national_after_imports()`: Eq. 12 |
| `targets.py` | USGS targets; annual state shares |
| `firm_hazard.py` | Firm-month panel and estimation of Eq. 1-3 |
| `calibrate.py` | Market-layer calibration (replay) |
| `validate.py` | Predictive runs, metrics, firm scoring |
| `scenarios.py` | Mechanism tests, sensitivity, example interventions and LC3 regime |
| `figures.py` | Figures for the preliminary results |
