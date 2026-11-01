"""Read-only audit of POPIN; write reproducible analytical outputs only."""
from pathlib import Path
import json
import hashlib
import itertools
from collections import Counter
import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data' / 'release_v4' / 'analysis' / 'source_inputs'
OUT = ROOT / 'data' / 'release_v4' / 'analysis' / 'source_audit'
DIMS = ['people_centrism','anti_elitism','moral_dichotomy','popular_sovereignty','exclusionary_rhetoric','crisis_rhetoric']
RUNS = {
    'Qwen chunked':['qwen_v4_legacy'],
    'DeepSeek full':['deepseek_v4_full_nonchunked_v4'],
    'DeepSeek chunked':['deepseek_deepseek-v4-flash-0731__v4__decart__dfa2b4e42e','deepseek_deepseek-v4-flash-0731__v4__decart__62a8eacb02'],
    'Luna full':['luna__all_noninvalid__openai__v4','luna__sample_900__openai__v4'],
    'Luna chunked':['luna_chunked_all_noninvalid_v4','luna_chunked_sample1000_v4'],
}

def metrics(x,y):
    x=pd.Series(np.asarray(x,dtype=float));y=pd.Series(np.asarray(y,dtype=float))
    ok=x.notna() & y.notna();x=x[ok];y=y[ok];d=x-y
    return dict(n=len(x),pearson=x.corr(y) if len(x)>=3 else np.nan,spearman=x.rank().corr(y.rank()) if len(x)>=3 else np.nan,mae=d.abs().mean(),rmse=np.sqrt((d*d).mean()),bias=d.mean())

def save(name,rows):
    pd.DataFrame(rows).to_csv(OUT / (name+'.csv'),index=False)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c=duckdb.connect(str(ROOT/'popin.duckdb'),read_only=True)
    s=c.sql('SELECT discourse_id,model_id,run_id,prompt_id,provider,final_score,n_chunks,'+','.join(DIMS)+' FROM scores').df()
    m=c.sql('SELECT id AS discourse_id,iso3,leader_name,discourse_year,discourse_date,dtype,word_count FROM discourses').df()
    l=c.sql('SELECT iso3,TRY_CAST(year AS INTEGER) AS year,TRY_CAST(pop_r AS DOUBLE) AS pop_r,TRY_CAST(pop AS DOUBLE) AS pop FROM raw_lallpi_index').df()
    raw_checks=[]
    for run in RUNS['Luna full']+RUNS['Luna chunked']:
        count=Counter()
        cur=c.execute('SELECT n_chunks,raw_json FROM scores WHERE run_id=?',[run])
        while rows:=cur.fetchmany(500):
            for chunks,raw in rows:
                count['rows']+=1
                if not raw:count['raw_missing']+=1;continue
                obj=json.loads(raw)
                if 'n_valid_chunks' in obj:
                    count['validity_recorded']+=1;count['partial']+=int(obj['n_valid_chunks']!=chunks)
                if 'raw_content' in obj:
                    content=(obj['raw_content'] or '').strip()
                    try:
                        if content.startswith('```'):content=content.split('```')[1].strip().removeprefix('json').strip()
                        parsed=json.loads(content);count['raw_parsed']+=1
                        count['raw_missing_axes']+=int(any(k not in parsed or parsed[k] is None for k in DIMS))
                        count['raw_bounds']+=int(any(not 0<=float(parsed[k])<=100 for k in DIMS if k in parsed and parsed[k] is not None))
                    except Exception:count['raw_parse_error']+=1
        raw_checks.append(dict(run_id=run,**dict(count)))
    save('luna_raw_integrity',raw_checks)
    c.close()
    coverage=[]; frames={}; desc=[]; integrity=[]
    for label,runs in RUNS.items():
        f=s[s.run_id.isin(runs)].copy();assert not f.discourse_id.duplicated().any(),label
        f=f.merge(m,on='discourse_id',validate='one_to_one');frames[label]=f
        coverage.append(dict(model=label,rows=len(f),ids=f.discourse_id.nunique(),speech=int(f.dtype.eq('SPEECH').sum()),parts=json.dumps(f.run_id.value_counts().to_dict())))
        integrity.append(dict(model=label,null_score=int(f.final_score.isna().sum()),null_dimensions=int(f[DIMS].isna().sum().sum()),out_of_bounds=int(((f[DIMS]<0)|(f[DIMS]>100)).sum().sum()),max_mean_residual=float((f.final_score-f[DIMS].mean(axis=1)).abs().max())))
        for scope,sub in [('ALL',f),('SPEECH',f[f.dtype.eq('SPEECH')])]:
            x=sub.final_score
            desc.append(dict(model=label,scope=scope,n=len(x),mean=x.mean(),median=x.median(),sd=x.std(),zero_pct=100*x.eq(0).mean(),ge60_pct=100*x.ge(60).mean()))
    ids=set(frames['Qwen chunked'].discourse_id)
    for f in frames.values():assert set(f.discourse_id)==ids
    save('coverage',coverage);save('score_integrity',integrity);save('descriptive',desc)
    pair=[]
    for a,b in itertools.combinations(frames,2):
        x=frames[a].set_index('discourse_id').final_score;y=frames[b].set_index('discourse_id').final_score.reindex(x.index)
        pair.append(dict(left=a,right=b,**metrics(x,y)))
    save('paired_models',pair)
    t=pd.read_csv(BASE/'gpd_popin_leader_term_matches.csv')
    t=t[t.decision.eq('C_leader_term_unique')].copy()
    t['key']=t.gpd_country+'|'+t.gpd_leader+'|'+t.gpd_term.astype(int).astype(str)
    t['end']=pd.to_numeric(t.gpd_yearend,errors='coerce')
    assert t.end.notna().all()
    points=[]
    for label,f in frames.items():
        for row in t.itertuples():
            sub=f[f.iso3.eq(row.gpd_iso3)&f.leader_name.eq(row.popin_leader_name)&f.discourse_year.between(row.gpd_yearbegin,row.end)]
            for scope,q in [('ALL',sub),('SPEECH',sub[sub.dtype.eq('SPEECH')])]:
                if len(q):points.append(dict(model=label,scope=scope,key=row.key,iso3=row.gpd_iso3,leader=row.popin_leader_name,n_docs=len(q),gpd=50*row.gpd_totalaverage,mean=q.final_score.mean()))
    p=pd.DataFrame(points);save('gpd_term_points',p)
    results=[]
    for scope in ['ALL','SPEECH']:
        for min_n in [1,5,20]:
            z=p[p.scope.eq(scope)&p.n_docs.ge(min_n)]
            common=set.intersection(*[set(z[z.model.eq(a)].key) for a in frames])
            for a in frames:
                q=z[z.model.eq(a)&z.key.isin(common)]
                results.append(dict(model=a,scope=scope,min_docs=min_n,**metrics(q['mean'],q.gpd)))
    save('gpd_term_metrics',results)
    cutoffs=[]
    for threshold in [0,100,200,300,500,1000]:
        temp=[]
        for label,f in frames.items():
            f=f[f.dtype.eq('SPEECH') & f.word_count.gt(threshold)]
            for row in t.itertuples():
                q=f[f.iso3.eq(row.gpd_iso3)&f.leader_name.eq(row.popin_leader_name)&f.discourse_year.between(row.gpd_yearbegin,row.end)]
                if len(q):temp.append(dict(model=label,key=row.key,gpd=50*row.gpd_totalaverage,mean=q.final_score.mean(),n_docs=len(q)))
        zz=pd.DataFrame(temp);common=set.intersection(*[set(zz[zz.model.eq(a)].key) for a in frames])
        for a in frames:
            q=zz[zz.model.eq(a)&zz.key.isin(common)];cutoffs.append(dict(model=a,words_gt=threshold,n_docs_summed=int(q.n_docs.sum()),**metrics(q['mean'],q.gpd)))
    save('word_cutoffs_gpd',cutoffs)
    # Paired cluster bootstrap: resample leaders and retain all their mandates.
    z=p[p.scope.eq('SPEECH')];wide=z.pivot(index=['key','iso3','leader','gpd'],columns='model',values='mean').dropna().reset_index()
    groups=wide.groupby(['iso3','leader']).indices;keys=list(groups);rng=np.random.default_rng(20260906);draws=[]
    for i in range(2000):
        ix=np.concatenate([groups[keys[j]] for j in rng.integers(len(keys),size=len(keys))]);q=wide.iloc[ix]
        a=metrics(q['Luna full'],q.gpd);b=metrics(q['DeepSeek full'],q.gpd)
        draws.append({k:a[k]-b[k] for k in ['pearson','spearman','mae','rmse','bias']})
    boot=pd.DataFrame(draws)
    save('luna_minus_deepseek_full_bootstrap',[dict(metric=k,lo=boot[k].quantile(.025),hi=boot[k].quantile(.975),replicates=2000,leader_clusters=len(keys)) for k in boot])
    # Exact-text candidates are kept distinct from verified matches.
    matches=pd.read_csv(BASE/'gpd_popin_match_review.csv');match_results=[]
    for decisions in [['A_exact_text'],['A_exact_text','B_candidate_high_similarity']]:
        q=matches[matches.decision.isin(decisions)]
        for a,f in frames.items():
            j=q.merge(f,left_on='top_popin_id',right_on='discourse_id',validate='many_to_one')
            match_results.append(dict(model=a,match_level='+'.join(decisions),distinct_docs=j.discourse_id.nunique(),**metrics(j.final_score,50*j.gpd_averagerubric)))
    save('gpd_text_candidate_metrics',match_results)
    # Country-year alignment; no error metric across inequivalent LALLPI scales.
    lall=[]
    assert not l.duplicated(['iso3','year']).any()
    for a,f in frames.items():
        q=f[f.dtype.eq('SPEECH')].groupby(['iso3','discourse_year']).final_score.agg(['mean','size']).reset_index().merge(l,left_on=['iso3','discourse_year'],right_on=['iso3','year'])
        for indicator in ['pop_r','pop']:
            for n in [1,20]:
                j=q[q['size'].ge(n)].dropna(subset=[indicator]);st=metrics(j['mean'],j[indicator])
                lall.append(dict(model=a,indicator=indicator,min_docs=n,n=st['n'],pearson=st['pearson'],spearman=st['spearman']))
    save('lallpi_country_year',lall)
    dimensions=[]
    for a,f in frames.items():
        q=f[f.dtype.eq('SPEECH')]
        for d in DIMS:dimensions.append(dict(model=a,dimension=d,mean=q[d].mean(),zero_pct=100*q[d].eq(0).mean()))
        print('anti_moral',a,q.anti_elitism.corr(q.moral_dichotomy))
    save('dimensions',dimensions)
    sample=pd.read_csv(BASE/'sensitivity_test_sample.csv');sens=[];sr={}
    for file in (BASE/'sensitivity_runs').glob('*.jsonl'):
        rows=[json.loads(line) for line in file.open() if line.strip()];valid=[r for r in rows if r.get('scores')]
        sens.append(dict(file=file.name,rows=len(rows),valid_scores=len(valid),unique_ids=len(set(r['discourse_id'] for r in valid)),partial=sum(r.get('valid_chunks',0)!=r.get('n_chunks',0) for r in valid),sample_missing=len(set(sample.discourse_id)-set(r['discourse_id'] for r in valid))))
        sr[file.stem]=pd.DataFrame([dict(discourse_id=r['discourse_id'],score=r['scores']['final_score']) for r in valid])
    save('prompt_inventory',sens)
    comparisons=[]
    for a,prefix in [('DeepSeek','deepseek_deepseek-v4-flash-0731'),('Qwen','qwen_qwen3-30b-a3b-instruct-2507')]:
        neutral=sr[prefix+'__neutral'];base=sr[prefix+'__v4'] if a=='DeepSeek' else frames['Qwen chunked'][['discourse_id','final_score']].rename(columns={'final_score':'score'})
        q=neutral.merge(base,on='discourse_id',suffixes=('_neutral','_v4'),validate='one_to_one');comparisons.append(dict(model=a,**metrics(q.score_neutral,q.score_v4)))
    save('prompt_comparison',comparisons)
    # Recoverability evidence only; no mutation or merge into the active DB.
    backup_path=ROOT/'popin.duckdb.before_vps_import_20260823.bak'
    if backup_path.exists():
        b=duckdb.connect(str(backup_path),read_only=True)
        backup=b.sql('SELECT model_id,prompt_id,scope,count(*) n FROM scores GROUP BY ALL').df();b.close();save('backup_inventory',backup)
    else:
        save('backup_inventory',pd.DataFrame(columns=['model_id','prompt_id','scope','n']))
    notes=dict(database='popin.duckdb',db_bytes=(ROOT/'popin.duckdb').stat().st_size,raw_documents=len(m),retained=len(ids),speech=len(frames['Luna full'].query("dtype=='SPEECH'")),countries=frames['Luna full'].iso3.nunique(),leaders=frames['Luna full'].leader_name.nunique(),gpd_term_rows=len(t),term_mapping_rule='existing C_leader_term_unique mapping, inclusive year bounds; exact within-year term dates remain to audit',sample_rows=len(sample),sample_ids=sample.discourse_id.nunique(),sample_countries=sample.iso3.nunique(),sample_selection=sample.selection_source.value_counts().to_dict(),gpd_match_decisions=matches.decision.value_counts().to_dict(),backup_inventory_included=backup_path.exists(),analysis_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'audit_metadata.json').write_text(json.dumps(notes,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(notes,ensure_ascii=False));print(pd.DataFrame(results).query("scope=='SPEECH' and min_docs==1").to_string(index=False));print(boot.quantile([.025,.975]).to_string())

if __name__=='__main__':main()
