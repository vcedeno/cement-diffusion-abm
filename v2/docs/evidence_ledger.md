# Evidence ledger: US portland-limestone cement (PLC, ASTM C595 Type IL) transition

This ledger lists the evidence used to design, parameterise and test the PLC adoption model. Each item has an identifier, the claim it supports, its date, its source, and the model element it informs (equations and parameters are defined in `model_document.md`). Plant-level and state-level evidence is tabulated in full in `new_data/evidence/` and summarised here.

Conventions
- "Documented by" dates are the earliest public evidence that a product was available (EPD issue date, DOT approved-list revision, company release). They are upper bounds on the true start.
- Evidence is classified as **D** (dated document: specification, list, filing, press release), **T** (technical or trade press report), **S** (statistics), or **P** (practitioner account).
- "Used for" names the model element: firm decision (F), plant rule (P), ready-mix rule (R), DOT gate (G), imports (I), calibration or validation target (V), scenario lever (X), LC3 adaptation (L).

---

## 1. Product, standard and timeline

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| E1 | PLC sold under ASTM C1157 from 2005; limited sales 2005-2012 because C1157 had no AASHTO equivalent | 2005-2012 | T | FHWA-HRT-23-104 [R1]; CP Tech Center MAP brief, Oct 2018 [R2] | Context; pre-2020 product lines (P) |
| E2 | Type IL added to ASTM C595 and AASHTO M 240 in 2012 | 2012 | D | FHWA-HRT-23-104 [R1]; PCA/Innis NCC presentation, Mar 2014 [R3] | Earliest firm start month, 2012-01 (F) |
| E3 | About 30 US plants had produced some PLC by 2018; Devil's Slide (UT) since 2006; Lyons (CO) for more than 15 years by 2022 | 2006-2018 | T, D | MAP brief Oct 2018 [R2]; Cemex release 5 Apr 2022 [R4] | Pre-2020 PLC lines offered beside OPC (P, `prewave`) |
| E4 | All 50 state DOTs accept Type IL by April 2024 (Connecticut last); 44 states by May 2022 | 2022-2024 | D | PCA, 2 May 2022 [R5]; PCA, 2 Apr 2024 [R6] | DOT windows (G) |
| E5 | USGS reports Type IL directly from 2025: 0.618 of 2025 shipments, matching the blended share net of the 2016-19 baseline (0.623) | 2025 | S | USGS Mineral Industry Surveys, Cement in December 2025 [R7] | Target definition (V) |
| E6 | PLC is cheaper to make (limestone replaces clinker) and adds capacity in a tight market | 2022, 2024 | T | PCA/NRMCA statements, spring 2022 [R8]; Tilt-Up Today 2024 [R9] | Context; no cost term identified for PLC |

## 2. Industry signals and firm commitments (firm decision)

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| S1 | GCCA 2050 Climate Ambition: member companies commit to carbon-neutral concrete by 2050 | 1 Sep 2020 | D | Global Cement, Sep 2020 [R10] | Leaders' first signal, `GCCA_DATE` = 2020-09 (F, Eq. 1) |
| S2 | PCA Roadmap to Carbon Neutrality published (announced Nov 2020) | 12 Oct 2021 | D | Cement Americas, Oct 2021 [R11]; Cement Americas, Nov 2020 [R12] | Leaders' second signal, `ROADMAP_DATE` = 2021-10 (F, Eq. 1) |
| S3 | GCCA membership: 12 of the 22 US parent firms are members (Holcim, Heidelberg, Cemex, CRH, Buzzi, Vicat, Titan, Votorantim, Taiheiyo/CalPortland, Argos, GCC, UNACEM); 11 of the 12 were members by Oct 2018 | 2018-2020 | D | Global Cement, Oct 2018 [R13]; Global Cement, 2019 [R14]; GCCA members page [R15] | Leader/follower split, `gcca_member` (F) |
| S4 | Members started earlier: 11 of 12 members started by end-2022 (median Nov 2021) vs 4 of 10 non-members | 2020-2022 | S | `new_data/evidence/plant_plc_evidence.csv` | Leader/follower structure (F) |
| S5 | Parent climate commitments do not order the starts: Heidelberg committed May 2019 and started Jan 2022, after Holcim (Sep 2020 pledge, Dec 2020 start); the large firms converge on late 2021 to early 2022 regardless of commitment date | 2019-2022 | D | Heidelberg SBTi May 2019 [R16]; Cemex Feb 2020 [R17]; Holcim SBTi pledge Sep 2020 [R18]; Titan SBTi Jul 2021 [R19]; Argos Oct 2021 [R20] | Common dated signal rather than firm-specific commitment dates (F) |
| S6 | Of 14 conversion announcements (10 firms), 12 cite carbon goals, 10 cite customers, 3 cite the PCA roadmap, 4 claim leadership ("instead of waiting for the market to ask"); none cites DOT acceptance or cost | 2021-2022 | D | Announcements listed in [R21]-[R33] | Signals drive leaders; DOT acceptance a precondition only (F, G) |
| S7 | No US parent firm started PLC alone between the 2012 standard and the GCCA statement (record: zero starts 2012-01 to 2020-08) | 2012-2020 | S | `new_data/evidence/plant_plc_evidence.csv` | Intercept pinned to a small number of solo starts (F, `a0`) |
| S8 | Larger GCCA members started sooner after the GCCA statement (Holcim, 19% of capacity, Dec 2020; UNACEM, 0.8%, never); estimated size effect 1.03 (s.e. 0.47), likelihood-ratio p = 0.013; improves leave-one-member-out log-likelihood by 2.0 | 2020-2022 | S | `results/firm_hazard.json`, `code/firm_hazard.py` | Size term for leaders, `mem_size` (F) |
| S9 | Organisational size is positively associated with innovation adoption across studies | 1992 | Lit | Damanpour, Organization Studies 13(3) [R34] | Justification of the size term (F) |
| S10 | Experience with PLC abroad (EU, Canada) and a group climate target before Sep 2020 do not improve the leader or follower fit (p = 0.22, 0.30); follower size does not either (p = 0.67) | 2012-2022 | S | `code/firm_hazard.py` (tested alternatives) | Factors not included (F) |
| S11 | Plants of the same parent convert closer together than plants of different parents (mean gap 7.4 vs 9.2 months, permutation p = 0.014); local competitor clustering is weak (p = 0.07 at 300 miles, null at 150 and 500 miles) | 2020-2023 | S | Plant evidence table, 53 dated plants | Company-level decision with within-firm rollout (F, P, Eq. 4) |

## 3. Followers and holdouts

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| H1 | Non-members that started offered PLC beside OPC: Capitol (TxDOT Apr 2025: I, III, IL; EPD Feb 2023), Monarch (KDOT Nov 2024: I, I/II, III, IL), Giant/Keystone (EPD Aug 2023), Mitsubishi (EPD Oct 2024: II/V and IL), Eagle Central Plains (I, II, IL) | 2023-2025 | D | DOT approved lists and EPDs in `new_data/evidence/plant_plc_evidence.csv` | Followers keep OPC, `follower_keep_opc` (P) |
| H2 | Martin Marietta converted Midlothian and Hunter to Type IL by 31 Dec 2023 (about 90% of Type I/II customers); Summit converted Davenport (Apr 2022) and Hannibal (Aug 2022) fully | 2022-2023 | D | Martin Marietta 2024 proxy [R35]; Summit, Aug 2022 [R32] | Follower behaviour (P, R) |
| H3 | Four firms have no Type IL evidence through 2025: Salt River Materials (AZ), UNACEM/Drake (AZ), Armstrong (PA), Eagle/Heidelberg Texas Lehigh JV | 2025-2026 | D | ADOT lists Oct 2024 and Feb 2026 [R36, R37]; Drake EPD Apr 2025; TxDOT list Apr 2025 | Validation (V); follower holdouts are a stated limitation |
| H4 | Follower pull: a follower's start probability rises with the PLC share already bought in its customers' states (estimated aF = 23.7, s.e. 2.3) | 2012-2022 | S | `results/firm_hazard.json` | Follower term (F, Eq. 1) |

## 4. Plants: rollout, withdrawal and conversion speed

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| P1 | Leaders converted whole fleets and withdrew Type I/II: Holcim Midlothian (intro Mar 2021, full Nov 2021), Ste. Genevieve and Alpena (by Jan 2022), Joppa (Apr 2022); Buzzi/Alamo all 8 plants ("full conversion", I/II production ends) on a dated schedule in 2022; Titan Pennsuco and Roanoke full Nov 2022; GCC whole Minnesota market Jul 2022 | 2021-2022 | D | Holcim Sep 2021 [R21]; ENR Mar 2022 [R8]; Pit & Quarry Apr 2022 [R23]; Buzzi/Alamo Mar 2022 [R27]; Titan Nov 2022 [R31]; GCC Jun 2022 [R30] | Leaders' plants withdraw OPC (P, Eq. 5-6) |
| P2 | Supplier letter (Jul 2022): "all local cement suppliers are ceasing production of Type I and Type II cement"; practitioners (Mar 2023): most major producers switched to IL exclusively | 2022-2023 | P | ASCE Collaborate discussion [R38] | OPC withdrawal forces downstream adoption (P, R) |
| P3 | Agencies reacted to the supply change: WisDOT (Dec 2021, "the cement industry is changing over"), Idaho TD (Dec 2022, "availability of cement is becoming more and more limited"), FHWA (2023, PLC "progressively replacing Type I and Type I/II cements in most plants") | 2021-2023 | D | Idaho TD memo [R39]; FHWA-HRT-23-104 [R1] | Withdrawal as the adoption channel (P) |
| P4 | Documented conversion speeds (introduction to full PLC): Buzzi, Summit, GCC about 1 month; Holcim (Midlothian 8 months), Heidelberg about 6; Argos and Titan about 12; Cemex partial and gradual (Brooksville more than 50%, Demopolis more than 20% in Feb 2022), 24 | 2021-2023 | D | `new_data/plant_conversion_evidence.csv` (ramp_basis); Cemex Feb 2022 [R40] | Conversion ramp `ramp_months` (P, Eq. 7) |
| P5 | Within-firm rollout lags of follow-on plants, 2020-22 wave: 27 observed lags | 2020-2022 | S | `new_data/derived/rollout_lags.csv` (built from the plant evidence) | Rollout lag distribution (P, Eq. 4) |
| P6 | Some leader plants lagged for years: Amrize (Holcim) Ravena NY states it is working toward "the future production of Type IL" (2026); Cemex Knoxville EPD Oct 2023 covers Type I/II only | 2023-2026 | D | Ravena plant page [R41]; plant evidence table | Limitation: plant-specific laggards (NY, PA) |
| P7 | White-cement plants (Waco TX, York PA) make no gray PLC; slag-grinding sites act as distribution points of their parent | n/a | D | Plant evidence table | `eligible`, `role` (P) |
| P8 | Cupertino (CA) closed around 2020 | 2020 | D | CARB facility reporting | Operating period (P) |

## 5. Sulfate-resistant (Type II/V) markets (Southwest)

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| W1 | Arizona's three plants offer no Type IL on the ADOT approved list in Oct 2024 or Feb 2026 (CalPortland Rillito I/II/V; Drake Paulden I/II/V; Salt River Clarkdale I/II/V and IP); Arizona's Type IL comes only from out-of-state or Mexican plants | 2024-2026 | D | ADOT lists [R36, R37] | Type II/V plants keep OPC (P); buyer constraint (R) |
| W2 | Drake produces "100% ASTM Type II-V cement" for Arizona and Las Vegas; Salt River sells Type I/II/V (low alkali) and IP(25), no Type IL | 2022, 2026 | D | Global Cement plant report Jul 2022 [R42]; SRMG products [R43] | Type II/V product-line flag (P) |
| W3 | Arizona's recommended general-use cement is low-alkali Type II; Phoenix's approved mix designs 2025-26 name only Type IP | 2025-2026 | D | Arizona Rock Products Association spec [R44]; City of Phoenix [R45] | Buyer side of the product-class constraint (R) |
| W4 | Caltrans requires Type IL to carry a moderate or high sulfate-resistance designation and alkali of 0.60% or less (notice 6 Aug 2021; spec Oct 2021); every listed California plant now offers Type IL beside Type II/V (19 Type IL products), yet California's PLC share is about 0.10 in 2025 | 2021-2026 | D, S | Caltrans notice [R46]; Caltrans AML [R47]; CP Tech Center Apr 2026 [R48]; USGS [R7] | Buyers in Type II/V markets take PLC much less, `kiiv` (R, Eq. 10) |
| W5 | Sulfate designation of blended cement is by performance test (ASTM C1012), "a more conservative approach" than the C3A limit for Type II/V portland cement; GCC moves to ASTM C452 for PLC sulfate designation from Aug 2026 | 2024, 2026 | D | PCA SN3148 [R49]; GCC customer letter Jul 2026 [R50] | Mechanism behind W1-W4; LC3 transfer (L) |
| W6 | Type II/V product-line plants (11): CA (Victorville, Redding, Tehachapi, Lucerne Valley, Oro Grande, Mojave, Lebec), AZ (Paulden, Clarkdale, Rillito), NV (Fernley), TX (GCC Odessa) with pre-2021 product sources where available | 2016-2026 | D | `new_data/plant_conversion_evidence.csv` (iiv_basis, iiv_pre2021_basis) | `iiv` flag and buyer exposure (P, R) |
| W7 | Remaining OPC in 2025 is concentrated: Southwest (CA, AZ, NV, NM) holds 34% of US OPC shipments at 11% PLC; Texas 26% (South TX 30% PLC, North TX 72%); NY/NJ/PA/New England 13%; rest of US 23% at 85% PLC | 2025 | S | USGS [R7], `new_data/usgs_2025` | Validation by state (V) |

## 6. Ready-mix producers (buyers)

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| B1 | Contractors reported more problems with Type IL than Type I (set time, finishing, bleeding, saw-cut timing): 56% of respondents, 72% of concrete contractors | 2023 | S | ACI 302 / ASCC survey [R51] | Transitional switching away from PLC-only supply, `sigR` (R, Eq. 8) |
| B2 | New mix designs and trial batches are needed; many batch plants swapped cement without additional testing once supply changed | 2022-2024 | T, P | Tilt-Up Today [R9]; ASCE Collaborate [R38] | Switching fades over a qualification period, `H` = 18 months (R, Eq. 8) |
| B3 | Cement firms own ready-mix operations (Cemex, Holcim/Aggregate Industries, Argos, CRH/Oldcastle, Titan/S&W, CalPortland, GCC, Heidelberg/Hanson, Vicat/National, Buzzi/Alamo) | n/a | D | `new_data/readymix_owner_assignment.csv` (facility-name match to subsidiary brands) | Owned ready-mix buys from its parent (R) |
| B4 | Suppliers offering both still sold mostly PLC in some cases (Martin Marietta about 90% of Type I/II customers by 2023; Cemex Brooksville more than 50% in Feb 2022) | 2022-2023 | D | [R35], [R40] | Purchase probability from plants offering both, `pi` (R, Eq. 9) |

## 7. Public procurement

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| M1 | Port Authority of NY and NJ Clean Construction Program and low-carbon concrete specification | Oct 2020 to 2021 | D | Port Authority [R52]; ENR [R53] | Procurement context (R) |
| M2 | Federal Buy Clean: Executive Order 14057 (Dec 2021); Buy Clean Task Force; IRA low-embodied-carbon funds (Aug 2022) | Dec 2021 to Sep 2022 | D | Federal Register 13 Dec 2021 [R54]; Federal Buy Clean Initiative [R55] | Procurement shift, start drawn in Dec 2021 to Sep 2022, `piD` (R, Eq. 9) |
| M3 | GSA interim IRA low-embodied-carbon material requirements (pilot) | 16 May 2023 | D | GSA [R56] | Procurement reinforcer after the conversions |
| M4 | State action: New York Low Embodied Carbon Concrete Leadership Act (Jan 2022), New Jersey low-carbon concrete law | 2022-2023 | D | NRDC overview [R57] | Procurement context |
| M5 | Procurement milestones postdate most conversions (late 2021 to 2023): a reinforcer, not the trigger | 2021-2023 | Inference from M1-M4 and P1 | n/a | `piD` weakly identified by 2010-22 data |
| M6 | July 2025 budget legislation rescinded about $1.8 billion of IRA low-carbon materials funds; GSA/DOT pilots cancelled | 2025 | D | Canary Media [R58] | Context for 2025 |

## 8. State DOT acceptance

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| G1 | Acceptance window for each of the 50 states (not before, accepted by, status, evidence, source); 16 verified or bounded by a dated provision, the rest bounded by the Jul 2018 acceptance map, the May 2022 44-state count and the Apr 2024 50-state announcement | 2008-2024 | D | `new_data/evidence/dot_acceptance_evidence.csv` (state-level sources); MAP brief Oct 2018 [R2]; PCA [R5, R6] | DOT gate (G, Eq. 11) |
| G2 | Early verified acceptances were followed by years without adoption: Iowa by Apr 2013, North Carolina by Feb 2014, South Carolina May 2014, Tennessee and Texas by Mar 2014, Indiana by Sep 2015, Florida 2015-17, Alabama Dec 2019; national take-off 2021-22 | 2013-2022 | D, S | Dated provisions in G1; USGS | DOT acceptance permissive, not binding (G) |
| G3 | Paving use of PLC: more than 200 miles by 2014, about 900 miles by 2018 | 2014-2018 | T | PCA/Innis Mar 2014 [R3]; ENR | Context |

## 9. Imports

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| I1 | Imports of hydraulic cement and clinker by customs district, 2022 (and 2023) | 2022-2023 | S | USGS Minerals Yearbook, Cement, imports by customs district [R59]; `new_data/imports_by_customs_district.csv` | Import share by state, `m_imp` (I, Eq. 12) |
| I2 | USGS shipments by destination include imported cement | 2021 | D | USGS MIS Dec 2021 table notes [R7] | Imports dilute observed state shares (I) |
| I3 | Imports were 21% of US consumption in 2025 (Turkey 32%, Canada 20%, Vietnam 13%, Greece 9%) | 2025 | S | USGS Mineral Commodity Summaries 2026 [R60] | Context |
| I4 | Integrated firms' terminals import Type IL in some cases (Titan from Turkey to Newark, Norfolk, Tampa; SCG ships both I/II and IL to Houston and West Coast ports); independent traders' product type not documented | 2022-2024 | D | Adocim/Titan EPD Apr 2024 [R61]; SCG EPD Dec 2024 [R62]; Global Cement Mar 2022 [R63] | Assumption test: imports carrying the domestic PLC share overshoot 2025 (0.74 vs 0.62), so imports are treated as ordinary cement (I) |
| I5 | Canadian-border imports excluded from dilution (Canadian producers make GUL, the PLC equivalent) | n/a | Assumption | `new_data/imports_by_customs_district.csv` (included = 0) | (I) |

## 10. Observed record (targets)

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| V1 | Monthly shipments of portland and blended cement by destination state, 2002-2024 | 2002-2024 | S | USGS MIS, compiled in `original_data/usgs_all_state_type_month.csv` | Calibration and validation targets (V) |
| V2 | Monthly shipments by destination, 2025 (tables 2a and 2b, incl. Type IL year to date) | 2025 | S | USGS MIS, Cement in December 2025 (released Apr 2026) [R7]; transcription and checks in `new_data/usgs_2025/SOURCE.txt` | Validation 2023-25 (V) |
| V3 | Record of firm starts (first PLC introduction by any plant of the parent from 2020 onward; pre-2020 niche lines, [E3], are not counted as starts): 18 of 22 firms by Dec 2025; 13 of the 18 dates are document dates (EPD, DOT list, data sheet, year-end statement) | 2020-2024 | D | `new_data/evidence/plant_plc_evidence.csv`, `new_data/firm_attributes.csv` | Firm validation, scored as "started by" for document dates (V) |
| V4 | CRH start: Ash Grove Seattle Type IL EPD issued 01.12.2021 (reference year 2019); Utah DOT used only limestone cement by Jul 2022 (suppliers Holcim Devil's Slide and Ash Grove Leamington) | 2021-2022 | D, T | Ash Grove Seattle EPD [R64]; KSL Jul 2022 [R65] | CRH record start 2021-12, upper bound (V) |

## 11. Comparison case: Canada

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| C1 | CSA A3001 allowed 5-15% limestone (GUL) in 2008; National Building Code 2010; the Cement Association of Canada launched a joint industry brand (Contempra) in 2011; British Columbia reached about 50% of shipments by 2013 | 2008-2013 | D | World Cement Oct 2011 [R66]; Concrete Products Sep 2013 [R67]; CAC annual report 2017 [R68] | Coordination device as an intervention (X) |
| C2 | The same multinationals owned plants on both sides of the border | n/a | D | Plant ownership | Coordination, not technology or firm identity, as the US constraint (X) |

## 12. LC3 (limestone calcined clay cement)

| ID | Evidence | Date | Type | Source | Used for |
|---|---|---|---|---|---|
| L1 | LC3 fits ASTM C595 Type IT (up to 40% pozzolan and 15% limestone); calcined clay can also be sold to ready-mix as an SCM (C618 Class N); higher replacement rates exceed current limits | 2024 | T | ACEEE, Hasanbeigi et al., Mar 2024 [R69] | Product class and channel (L) |
| L2 | Conversion needs a calciner and clay supply: $5-110 million per plant in case studies; operating cost 21-33% lower | 2024 | T | RMI, Dec 2024 [R70] | Capital barrier (L) |
| L3 | US projects: Titan Troutville (VA) flash calciner, about 300,000 short tons/yr calcined clay, DOE $61.7 million; Ash Grove Louisville (NE) kiln converted to a calciner, NDOT approval 2025, production early 2026; Summit four calcination sites (up to $215.6 million, negotiation); Vicat Lebec award terminated May 2025 | 2024-2026 | D, T | DOE Industrial Demonstrations [R71]; Global Cement Jun 2025 [R72]; Global Cement Jan 2025 [R73] | Observed LC3 decisions for calibration of the capital barrier (L) |
| L4 | Higher water demand, lower early strength and red colour; admixtures add 1-3% to concrete cost | 2024 | T | ACEEE [R69] | Buyer switching for LC3 (L, R) |
| L5 | Fly-ash shortages in Virginia motivate LC3 evaluation (VTRC 26-R52); no DOT acceptance of LC3 as such found | 2026 | D | VTRC 26-R52 [R74] | DOT acceptance becomes endogenous for LC3 (L, G) |

---

## References

[R1] FHWA (2023). Portland-Limestone Cement. FHWA-HRT-23-104. https://highways.dot.gov/sites/fhwa.dot.gov/files/FHWA-HRT-23-104.pdf
[R2] CP Tech Center (2018). MAP Brief, October 2018: Portland-limestone cement. https://www.intrans.iastate.edu/wp-content/uploads/2019/10/MAPbriefOctober2018.pdf
[R3] Innis, P. (2014). Portland-limestone cement, National Concrete Consortium, March 2014. https://www.intrans.iastate.edu/wp-content/uploads/2018/08/SP14-16-Innis-Limestone-sec.pdf
[R4] Cemex (5 Apr 2022). Cemex increasing production of lower carbon portland limestone cement in Colorado. https://prnewswire.com/news-releases/cemex-increasing-production-of-lower-carbon-portland-limestone-cement-in-colorado-301518153.html
[R5] PCA (2 May 2022). A milestone for sustainable infrastructure: 44 state DOTs now accept use of portland-limestone cement. https://www.cement.org/2022/05/02/a-milestone-for-sustainable-infrastructure-44-state-departments-of-transportation-now-accept-use-of-portland-limestone-cement/
[R6] PCA (2 Apr 2024). All 50 states give environmentally conscious cement the green light. https://cement.org/newsroom/2024/04/02/all-50-states-give-environmentally-conscious-cement-the-green-light
[R7] USGS. Mineral Industry Surveys, Cement (monthly), incl. Cement in December 2025. https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/files/mis-202512-cemen.pdf
[R8] ENR (Mar 2022). Producers shift to make more lower-carbon portland-limestone cement. https://www.enr.com/articles/53850-producers-shift-to-make-more-lower-carbon-portland-limestone-cement
[R9] Tilt-Up Today (2024). Type IL cement and tilt-up. https://tilt-up.org/tilt-uptoday/?p=17475
[R10] Global Cement (Sep 2020). GCCA announces 2050 Climate Ambition. https://globalcement.com/news/item/11287-global-cement-and-concrete-association-announces-2050-climate-ambition
[R11] Cement Americas (12 Oct 2021). PCA releases Roadmap to Carbon Neutrality. https://cementamericas.com/2021/10/12/pca-releases-roadmap-to-carbon-neutrality/
[R12] Cement Americas (17 Nov 2020). PCA to develop carbon neutrality roadmap. https://cementamericas.com/2020/11/17/pca-to-develop-carbon-neutrality-roadmap/
[R13] Global Cement (Oct 2018). GCCA membership grows to 20 companies. https://www.globalcement.com/news/8885-global-cement-and-concrete-association-membership-grows-to-20-companies
[R14] Global Cement (2019). GCCA expands membership to 36 companies and 15 affiliates. https://globalcement.com/news/9802-global-cement-and-concrete-association-expands-membership-to-36-companies-and-15-affiliates
[R15] GCCA. Members and affiliates. https://gccassociation.org/concretefuture/about-us-members-and-affiliates/
[R16] HeidelbergCement (13 May 2019). SBTi approval. https://www.heidelbergmaterials.com/en/pr-13-05-2019
[R17] Global Cement (Feb 2020). Cemex launches Climate Action strategy. https://www.globalcement.com/news/item/10489-cemex-launches-climate-action-strategy
[R18] Holcim (21 Sep 2020). LafargeHolcim signs Net Zero Pledge with Science-Based Targets. https://www.holcim.com/lafargeholcim-net-zero-pledge-science-based-targets
[R19] Global Cement (Jul 2021). SBTi validates Titan Cement's CO2 reduction goals. https://globalcement.com/news/item/12715-science-based-targets-initiative-validates-titan-cement-s-co2-reduction-goals
[R20] Global Cement (Oct 2021). Argos commits to 29% CO2 reduction by 2030. https://globalcement.com/news/13862-argos-commits-to-29-co2-emissions-reduction-by-2030-and-carbon-neutral-concrete-by-2050
[R21] Business Wire (14 Sep 2021). LafargeHolcim Midlothian conversion. https://www.businesswire.com/news/home/20210914005800/en
[R23] Pit & Quarry (19 Apr 2022). Holcim US transitioning another cement plant to PLC. https://www.pitandquarry.com/holcim-us-transitioning-another-cement-plant-to-plc/
[R24] Global Cement (Feb 2022). Lehigh Mason City completes PLC transition. https://www.globalcement.com/news/14324-lehigh-cement-s-mason-city-cement-plant-completes-portland-limestone-cement-transition
[R25] World Cement (27 Jul 2022). Lehigh Union Bridge transitions to EcoCem PLC. https://www.worldcement.com/the-americas/27072022/lehigh-cement-plant-in-union-bridge-maryland-transitions-to-ecocem-plc/amp/
[R26] Global Cement (Feb 2022). Argos USA to convert Roberta to PLC. https://globalcement.com/news/14346-argos-usa-to-convert-roberta-cement-to-portland-limestone-cement-production
[R27] PR Newswire (17 Mar 2022). Buzzi Unicem USA and Alamo Cement announce changes to production of portland cement. https://prnewswire.com/news-releases/buzzi-unicem-usa-and-alamo-cement-company-announce-changes-to-production-of-portland-cement-at-its-us-operations-301505028.html
[R28] World Cement (28 Apr 2022). Argos announces new PLC brand and sustainability timeline. https://www.worldcement.com/the-americas/28042022/argos-announces-new-plc-type-il-brand-and-sustainable-strategy-timeline
[R29] Concrete Products (14 Dec 2021). Titan America Type IL milestone. https://concreteproducts.com/index.php/2021/12/14/titan-america-measures-type-il-milestone-doubles-florida-terminal-storage/
[R30] World Cement (6 Jun 2022). GCC fully converts Minnesota market to PLC. https://www.worldcement.com/the-americas/06062022/gcc-fully-converts-minnesota-market-to-portland-limestone-cement/amp/
[R31] Concrete Products (29 Nov 2022). Titan America fully converts Pennsuco, Roanoke plants to Type IL. https://concreteproducts.com/index.php/2022/11/29/titan-america-fully-converts-pennsuco-roanoke-plants-to-type-il/
[R32] Business Wire (22 Aug 2022). Summit Materials, Hannibal and Davenport PLC. https://www.businesswire.com/news/home/20220822005179/en
[R33] PR Newswire (Apr 2022). CalPortland converts Mojave production to PLC. https://prnewswire.com/news-releases/calportland-converts-mojave-cement-plant-production-to-portland-limestone-cement-301525362.html
[R34] Damanpour, F. (1992). Organizational size and innovation. Organization Studies 13(3), 375-402.
[R35] Martin Marietta (2024). Proxy statement, p. 158. https://mcdn.martinmarietta.com/Investors/Proxy/2024/files/basic-html/page158.html
[R36] Arizona DOT (Oct 2024). Hydraulic cements approved list. https://azdot.gov/sites/default/files/2024-10/hydraulic_cements_approved_list_oct2024.pdf
[R37] Arizona DOT (Feb 2026). Hydraulic cements approved list. https://azdot.gov/sites/default/files/2026-02/hydraulic_cements_approved_list_02192026.pdf
[R38] ASCE Collaborate, discussion "Type 1L cement" (2022-2023). https://collaborate.asce.org/professionaltopics/discussion/type-1l-cement
[R39] Idaho Transportation Department (Dec 2022). Transition to Type IL cement. https://itd.idaho.gov/wp-content/uploads/2023/01/Transition_Type-IL_Cement.pdf
[R40] PR Newswire (24 Feb 2022). Cemex successfully launches lower carbon portland limestone cement in southeastern US. https://prnewswire.com/news-releases/cemex-successfully-launches-lower-carbon-portland-limestone-cement-in-southeastern-us-301489969.html
[R41] Amrize Ravena. Innovation and sustainability. https://ravena.amrize.com/innovation-and-sustainability
[R42] Global Cement (Jul 2022). Plant report: Drake Cement. https://globalcement.com/magazine/articles/1264-plant-report-drake-cement
[R43] Salt River Materials Group. Cement products. https://srmaterials.com/products/cement.html
[R44] Arizona Rock Products Association. Recommended specification with notes. https://www.azrockproducts.org/wp-content/uploads/ARPA-Recommended-Specification-with-notes.pdf
[R45] City of Phoenix (2026). 2025-2026 approved concrete mix designs. https://www.phoenix.gov/content/dam/phoenix/streetssite/documents/materials-lab/2025-2026-ApprovedConcreteMixDesigns-04212026.pdf
[R46] Caltrans (6 Aug 2021). Notice for implementation of portland-limestone cement. https://dot.ca.gov/-/media/dot-media/programs/engineering/documents/mets/notice-for-implementation-of-portland-limestone-cement-a11y.pdf
[R47] Caltrans. Authorized materials list, cementitious materials. https://mets.dot.ca.gov/aml/CementitiousList.php
[R48] CP Tech Center (Apr 2026). Caltrans Type IL presentation. https://www.cptechcenter.org/wp-content/uploads/sites/7/2026/04/15-NC2-Presentation-Syed-Aqib.pdf
[R49] PCA (2024). SN3148.03, Portland-limestone cement. https://cement.org/wp-content/uploads/2024/06/2024-SN3148.03.pdf
[R50] GCC (13 Jul 2026). Customer letter: sulfate designation transition. https://www.gcc.com/wp-content/uploads/2026/07/Customer-Letter-Sulfate-Designation-Transition.pdf
[R51] Concrete Products (28 Aug 2023). ACI 302, ASCC survey stakeholders on portland-limestone cement mixes. https://concreteproducts.com/index.php/2023/08/28/aci-302-ascc-survey-stakeholders-on-portland-limestone-cement-mixes/
[R52] Port Authority of NY and NJ. Low-Carbon Concrete Pilot Program, Task B report. https://www.panynj.gov/content/dam/port-authority/about/environmental-initiatives-/clean-construction/LCCPP-taskB-report.pdf
[R53] ENR. Port Authority of NY and NJ sets new low-carbon concrete mandate. https://enr.com/articles/56627-port-authority-of-ny-and-nj-sets-new-low-carbon-concrete-mandate
[R54] Federal Register (13 Dec 2021). Executive Order 14057. https://www.govinfo.gov/content/pkg/FR-2021-12-13/pdf/2021-27114.pdf
[R55] Federal Buy Clean Initiative (archived). https://sustainability.gov/archive/biden46/buyclean/index.html
[R56] GSA (16 May 2023). GSA pilots Buy Clean IRA requirements for low embodied carbon construction materials. https://www.gsa.gov/about-us/newsroom/news-releases/gsa-pilots-buy-clean-inflation-reduction-act-requirements-for-low-embodied-carbon-construction-materials-05162023
[R57] NRDC. NY and NJ: centers of action on low carbon concrete buying. https://www.nrdc.org/experts/sasha-stashwick/ny-and-nj-centers-action-low-carbon-concrete-buying
[R58] Canary Media (2025). Trump rescinds federal program to boost low-carbon building materials. https://www.canarymedia.com/articles/policy-regulation/trump-rescinds-federal-program-to-boost-low-carbon-building-materials
[R59] USGS. Minerals Yearbook, Cement (2022, 2023), imports of hydraulic cement and clinker by customs district. https://www.usgs.gov/centers/national-minerals-information-center/cement-statistics-and-information
[R60] USGS (2026). Mineral Commodity Summaries 2026, Cement. https://pubs.usgs.gov/periodicals/mcs2026/mcs2026-cement.pdf
[R61] Adocim/Titan (25 Apr 2024). Turkey cement EPD (ASTM). https://www.astm.org/v3/assets/blt5eb0a2cb04534832/blt444a319df6bcf367/697b1d899940131333021681/1131.Adocim_Titan_Turkey_Cement_EPD_2024_04_25.pdf
[R62] SCG (18 Dec 2024). Vietnam cement import EPD. https://pcr-epd.s3.us-east-2.amazonaws.com/1341.SCG_Vietnam_Cement_Import_EPD_2024_12_18.pdf
[R63] Global Cement (Mar 2022). Titan America commences Type IL sales in New Jersey and New York City. https://globalcement.com/news/14437-titan-america-commences-type-il-portland-limestone-cement-sales-in-new-jersey-and-new-york-city
[R64] Ash Grove (2021). EPD, Portland-limestone cement Type IL, Seattle. https://pcr-epd.s3.us-east-2.amazonaws.com/571.EPD_FOR_AshGrove_EPD-Type_IL_Seattle_Athena.pdf
[R65] KSL (17 Jul 2022). UDOT using new limestone cement. https://www.ksl.com/article/50441071/udot-using-new-limestone-cement-with-several-benefits
[R66] World Cement (7 Oct 2011). Cement Association of Canada launches Contempra. https://www.worldcement.com/the-americas/07102011/Cement_Association_of_Canada_launches_Contempra
[R67] Concrete Products (17 Sep 2013). Ground limestone-bearing cement nears 50 percent of British Columbia shipments. https://concreteproducts.com/index.php/2013/09/17/ground-limestone-bearing-cement-nears-50-percent-of-british-columbia-shipments/
[R68] Cement Association of Canada (2017). Annual report. https://annualreports.cement.ca/wp-content/uploads/CAC-AR-2017.pdf
[R69] Hasanbeigi, A. et al. (Mar 2024). LC3 in the US market. ACEEE. https://www.aceee.org/research-report/i2401
[R70] RMI (Dec 2024). The business case for LC3. https://rmi.org/wp-content/uploads/dlm_uploads/2024/12/the_business_case_for_LC3_report.pdf
[R71] DOE. Industrial Demonstrations Program, cement and concrete projects. https://www.energy.gov/cmei/oced/industrial-demonstrations-program-selected-and-awarded-projects-cement-and-concrete
[R72] Global Cement (Jun 2025). Undecarbonising in the US. https://globalcement.com/news/analysis/19470-undecarbonising-in-the-us
[R73] Global Cement (Jan 2025). Update on calcined clay. https://globalcement.com/news/analysis/18987-update-on-calcined-clay-january-2025
[R74] Virginia Transportation Research Council (2026). Report 26-R52. https://vtrc.virginia.gov/reports/all-reports/26-r52/
