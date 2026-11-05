#!/usr/bin/env python3
"""Rebuild conservative Module 08 Stage 2 synthesis from Stage 1 matrix.
Run from repository root:
 python research/08_evidence_synthesis/scripts/build_mechanism_synthesis.py
No network, no source edits, no figure generation.
"""
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"


def main():
    matrix = pd.read_csv(DATA / "cross_module_evidence_matrix.csv", dtype=str).fillna("")
    spec = pd.read_csv(DATA / "mechanism_synthesis_spec.csv", dtype=str).fillna("")
    by_id = matrix.set_index("finding_id", verify_integrity=True)
    outputs = []
    link_rows = []
    for _, item in spec.iterrows():
        ids = [x.strip() for x in item.supporting_finding_ids.split(";") if x.strip()]
        missing = sorted(set(ids) - set(by_id.index))
        if missing:
            raise ValueError(f"{item.synthesis_id}: missing Stage 1 IDs: {missing}")
        supporting = by_id.loc[ids]
        urls = set(u for u in supporting.source_url_normalized if u)
        modules = sorted(set(supporting.source_module))
        status = sorted(set(s for s in supporting.verification_status if s))
        row = item.to_dict()
        row.update(supporting_record_count=len(ids), supporting_module_count=len(modules),
                   supporting_modules=";".join(modules), distinct_nonempty_source_urls=len(urls),
                   inherited_verification_statuses=";".join(status),
                   evidence_strength="descriptive_only_not_causal")
        outputs.append(row)
        for fid in ids:
            src = by_id.loc[fid]
            link_rows.append(dict(synthesis_id=item.synthesis_id, finding_id=fid,
                                  source_module=src.source_module,
                                  source_record_ids=src.source_record_ids,
                                  source_url=src.source_url,
                                  verification_status=src.verification_status,
                                  interpretation_limit=src.interpretation_limit))
    pd.DataFrame(outputs).to_csv(DATA / "mechanism_evidence_synthesis.csv", index=False)
    pd.DataFrame(link_rows).to_csv(DATA / "synthesis_evidence_links.csv", index=False)
    print(f"Syntheses: {len(outputs)}; source links: {len(link_rows)}")
    print("Verification statuses are inherited; unique URL counts do not prove independent corroboration.")
    print("Outputs:", DATA / "mechanism_evidence_synthesis.csv", "and", DATA / "synthesis_evidence_links.csv")


if __name__ == "__main__":
    main()
