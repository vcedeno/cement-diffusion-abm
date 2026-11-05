#!/usr/bin/env python3
"""Reproducible, conservative TITLE-ONLY triage; not abstract screening."""
from pathlib import Path
import argparse, re, json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PLC=[r'portland[\s\-–]*limestone\s+cement',r'limestone[\s\-–]*portland\s+cement',r'\btype\s+i[\s\-]*l\b',r'\bportland\s+cement\s+type\s+il\b',r'\bplc\b(?=.*\bcement\b)',r'\bcem\s*ii\s*/\s*[ab]\s*[\-–]\s*l\b']
LC3=[r'limestone[\s\-–]*calcined[\s\-–]*clay(?:\s+cement)?',r'calcined[\s\-–]*clay[\s\-–]*limestone(?:\s+cement)?',r'\blc\s*[³3]\b',r'\blc3\b',r'\blc\s*[-–]\s*3\b']
BROAD=[r'low[\s\-–]*carbon\s+concrete',r'low[\s\-–]*carbon\s+cement',r'low[\s\-–]*co2\s+concrete',r'low[\s\-–]*clinker\s+cement',r'decarboni[sz].{0,20}(?:cement|concrete)',r'(?:cement|concrete).{0,20}decarboni[sz]']

def matches(t, patterns):
    return any(re.search(p,t,flags=re.I) for p in patterns)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);(out/'figures').mkdir(exist_ok=True)
    df=pd.read_csv(a.input,dtype=str,keep_default_na=False)
    required={'search_group','openalex_id','title','year'}
    if not required.issubset(df):raise ValueError(f'Missing columns: {required-set(df)}')
    df['year_num']=pd.to_numeric(df.year,errors='coerce')
    df['title_plc']=df.title.map(lambda t:matches(t,PLC))
    df['title_lc3']=df.title.map(lambda t:matches(t,LC3))
    df['title_broad']=df.title.map(lambda t:matches(t,BROAD))
    df['title_triage']=df.apply(lambda r:'TITLE_MATCH' if r[['title_plc','title_lc3','title_broad']].any() else 'NEEDS_ABSTRACT_REVIEW',axis=1)
    df['abstract_available_in_input']=False
    df['final_screening_status']='NOT_SCREENED_ABSTRACT'
    df.to_csv(out/'publication_search_memberships_title_triage.csv',index=False)
    works=df.groupby('openalex_id',sort=False).agg(title=('title','first'),year=('year','first'),doi=('doi','first'),work_type=('work_type','first'),source=('source','first'),search_groups=('search_group',lambda s:';'.join(sorted(set(s)))),title_plc=('title_plc','max'),title_lc3=('title_lc3','max'),title_broad=('title_broad','max'),membership_count=('search_group','size')).reset_index()
    works['title_triage']=works.apply(lambda r:'TITLE_MATCH' if r[['title_plc','title_lc3','title_broad']].any() else 'NEEDS_ABSTRACT_REVIEW',axis=1)
    works['final_screening_status']='NOT_SCREENED_ABSTRACT';works['abstract']='';works['abstract_screening_decision']='PENDING'
    works.to_csv(out/'publication_unique_works_title_triage.csv',index=False)
    # Search-membership annual counts, no claim of relevance.
    annual=df.groupby(['year_num','search_group']).size().unstack(fill_value=0).sort_index();annual.index.name='year';annual.to_csv(out/'publication_annual_search_hits.csv')
    # Unique works per year and conservative explicit title signals; overlapping categories permitted.
    unique=works.copy();unique['year_num']=pd.to_numeric(unique.year,errors='coerce')
    rows=[]
    for y,g in unique.groupby('year_num'):
        if pd.isna(y):continue
        rows.append(dict(year=int(y),unique_works=len(g),title_plc=int(g.title_plc.sum()),title_lc3=int(g.title_lc3.sum()),title_broad=int(g.title_broad.sum()),needs_abstract_review=int((g.title_triage=='NEEDS_ABSTRACT_REVIEW').sum())))
    counts=pd.DataFrame(rows).sort_values('year');counts.to_csv(out/'publication_annual_unique_title_signals.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,5));cols=['PLC_strict','PLC_expanded','LC3_strict','low_carbon_concrete']
    for c in cols:
        if c in annual:ax.plot(annual.index,annual[c],label=c.replace('_',' '),lw=1.8)
    ax.set(xlabel='Publication year',ylabel='OpenAlex search hits (not screened)',title='OpenAlex candidate records by search query');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'figures'/'01_raw_search_hits_by_year.png',dpi=200);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5))
    for c,l in [('title_plc','PLC title signal'),('title_lc3','LC3 title signal'),('title_broad','Broad low-carbon title signal')]:ax.plot(counts.year,counts[c],label=l,lw=1.8)
    ax.set(xlabel='Publication year',ylabel='Unique works with explicit title signal',title='Conservative title signals (NOT screened publications)');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'figures'/'02_unique_title_signals_by_year.png',dpi=200);plt.close(fig)
    report={'search_membership_rows':len(df),'unique_openalex_works':len(works),'search_group_counts':df.search_group.value_counts().to_dict(),'title_signal_unique_works':{c:int(works[c].sum()) for c in ['title_plc','title_lc3','title_broad']},'unique_works_needing_abstract_review':int((works.title_triage=='NEEDS_ABSTRACT_REVIEW').sum()),'abstracts_present_in_input':False,'limitations':['Title-only triage, not relevance screening','OpenAlex search retrieval is not an exhaustive bibliometric census','Categories overlap and search strategies differ','2025 indexing may be incomplete']}
    (out/'publication_screening_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
