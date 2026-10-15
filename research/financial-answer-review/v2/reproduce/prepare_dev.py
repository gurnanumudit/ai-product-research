"""Pinned FinQA public-development intake; no model calls or test access.

Run only after SELECTION-PROTOCOL.json is saved and independently reviewed.
Fresh output directory required. Source references are never answering inputs.
"""
import argparse
import collections
import datetime
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import time

BASE = Path(__file__).parent
COMMIT = '0f16e2867befa6840783e58be38c9efb9229d742'
URL = f'https://raw.githubusercontent.com/czyssrs/FinQA/{COMMIT}/dataset/dev.json'
EXPECTED_SHA = 'a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51'

def sha(data): return hashlib.sha256(data).hexdigest()
def save(path, obj):
    with path.open('x') as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')

def numeric(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)): return False
    try: return Decimal(str(value)).is_finite()
    except InvalidOperation: return False

def locations(record):
    out = {}
    for field, prefix in [('pre_text', 'pre'), ('post_text', 'post')]:
        values = record.get(field)
        if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
            raise ValueError('unsupported text schema')
        for i, text in enumerate(values): out[f'{prefix}:{i}'] = text
    table = record.get('table')
    if not isinstance(table, list) or not all(isinstance(row, list) and all(isinstance(x, str) for x in row) for row in table):
        raise ValueError('unsupported table schema')
    for i, row in enumerate(table): out[f'table:row:{i}'] = ' | '.join(row)
    return out

def metadata(record, protocol):
    identifier = record.get('id'); qa = record.get('qa', {})
    if not isinstance(identifier, str) or len(identifier.split('/')) != 3: return None, 'unsupported_id'
    if identifier in protocol['prior_exposed_ids_excluded']: return None, 'documented_prior_manual_exposure'
    if not isinstance(qa.get('question'), str) or not qa['question'].strip(): return None, 'missing_question'
    if not numeric(qa.get('exe_ans')): return None, 'nonnumeric_or_nonfinite_execution_reference'
    program = qa.get('program')
    if not isinstance(program, str): return None, 'missing_program_metadata'
    operations = re.findall(r'\b[a-zA-Z_]+\s*\(', program)
    if not operations: return None, 'missing_operations'
    supports = qa.get('gold_inds')
    if not isinstance(supports, dict) or not supports or any(not isinstance(k, str) or not k.startswith(('text_', 'table_')) for k in supports):
        return None, 'unsupported_support_metadata'
    try: locations(record)
    except ValueError: return None, 'unsupported_neutral_source_schema'
    evidence = 'text_involved' if any(k.startswith('text_') for k in supports) else 'table_only'
    stratum = evidence + '|' + ('single' if len(operations) == 1 else 'multi')
    report = '/'.join(identifier.split('/')[:2])
    return {'id': identifier, 'stratum': stratum, 'report_group': report,
            'page_group': identifier.rsplit('-', 1)[0], 'company': identifier.split('/')[0],
            'rank_hash': sha((protocol['seed'] + '\0' + identifier).encode()),
            'documented_prior_exposed_report': report in protocol['prior_exposed_reports_flagged']}, None

def select(records, protocol):
    if len({r['id'] for r in records}) != len(records): raise ValueError('duplicate IDs')
    pools = {key: [] for key in protocol['quotas']}; excluded = []
    by_id = {r['id']: r for r in records}
    for record in records:
        meta, reason = metadata(record, protocol)
        if reason: excluded.append({'id': record.get('id'), 'reason': reason})
        else: pools[meta['stratum']].append(meta)
    original_counts = {key: len(value) for key, value in pools.items()}
    if any(original_counts[k] < q for k, q in protocol['quotas'].items()):
        raise ValueError('insufficient stratum; no automatic quota redistribution')
    report_count = collections.Counter(); selected = []; selected_count = collections.Counter()
    while len(selected) < sum(protocol['quotas'].values()):
        for key, quota in protocol['quotas'].items():
            if selected_count[key] >= quota: continue
            chosen = min(pools[key], key=lambda m: (report_count[m['report_group']], m['rank_hash'], m['id']))
            pools[key].remove(chosen); selected.append(chosen)
            report_count[chosen['report_group']] += 1; selected_count[key] += 1
    # Freeze final execution order independently of the cyclic sampling order.
    selected.sort(key=lambda m: (m['rank_hash'], m['id']))
    return [by_id[m['id']] for m in selected], selected, excluded, original_counts

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=BASE/'dev-v1')
    parser.add_argument('--protocol', type=Path, default=BASE/'SELECTION-PROTOCOL.json')
    args = parser.parse_args(); protocol = json.loads(args.protocol.read_text())
    if args.out.exists() or args.out.is_symlink(): raise SystemExit('Refuse existing destination')
    if protocol.get('review_state') != 'approved_before_acquisition': raise SystemExit('Protocol review gate not approved')
    if protocol['source_url'] != URL or protocol['source_sha256'] != EXPECTED_SHA: raise SystemExit('Source pin mismatch')
    args.out.mkdir(parents=True); (args.out/'source').mkdir(); start = time.monotonic()
    manifest = {'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'external_spend_usd':0,'model_calls':0,'source_url':URL,'source_commit':COMMIT,
                'protocol_sha256':sha(args.protocol.read_bytes()),'download_attempts':0,'failure':None}
    try:
        with tempfile.TemporaryDirectory(prefix='finqa-dev-transfer-') as tmp:
            header = Path(tmp)/'headers'; manifest['download_attempts'] = 1
            result = subprocess.run(['curl','--fail','--silent','--show-error','--max-time','90',
                                     '--max-filesize','100000000','-H','Accept-Encoding: gzip',
                                     '-D',str(header),URL],capture_output=True)
            manifest.update({'wire_bytes':len(result.stdout),'wire_sha256':sha(result.stdout),
                             'curl_returncode':result.returncode,'headers':header.read_text() if header.exists() else ''})
            if result.returncode: raise RuntimeError('Verified HTTPS acquisition failed: '+result.stderr.decode()[:200])
            body = gzip.decompress(result.stdout) if re.search(r'^content-encoding:\s*gzip\s*$',manifest['headers'],re.I|re.M) else result.stdout
            if len(body)>20000000 or sha(body)!=EXPECTED_SHA: raise ValueError('Source expansion or hash mismatch')
            with (args.out/'source/dev.json').open('xb') as handle: handle.write(body)
        records = json.loads(body)
        if not isinstance(records,list) or len(records)!=883: raise ValueError('Unexpected public dev frame')
        chosen,selected,excluded,pools = select(records,protocol)
        inputs = [{'id':r['id'],'question':r['qa']['question'],'locations':locations(r)} for r in chosen]
        gold = [{'id':r['id'],'source_split':'dev','original_qa':r['qa']} for r in chosen]
        save(args.out/'inputs.json',inputs); save(args.out/'gold.json',gold)
        selection = {'source_n':len(records),'selected_n':len(selected),'eligible_n':sum(pools.values()),
                     'stratum_pools':pools,'quotas':protocol['quotas'],'selected':selected,'excluded':excluded,
                     'report_groups':len({m['report_group'] for m in selected}),
                     'page_groups':len({m['page_group'] for m in selected}),
                     'company_groups':len({m['company'] for m in selected}),
                     'report_group_sizes':dict(collections.Counter(m['report_group'] for m in selected))}
        save(args.out/'selection.json',selection)
        manifest.update({'decoded_bytes':len(body),'source_sha256':sha(body),'source_records':len(records),
                         'selected_n':len(selected),'input_fields':['id','question','locations'],
                         'gold_isolation':'original_qa evaluator-only; source metadata eligibility does not certify labels'})
    except Exception as error:
        manifest['failure']={'type':type(error).__name__,'message':str(error)}
    finally:
        manifest['elapsed_seconds']=round(time.monotonic()-start,3)
        manifest['files']={str(p.relative_to(args.out)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
                           for p in args.out.rglob('*') if p.is_file()}
        manifest['retained_bytes_before_manifest']=sum(m['bytes'] for m in manifest['files'].values())
        save(args.out/'manifest.json',manifest)
        print(json.dumps({k:manifest.get(k) for k in ['wire_bytes','decoded_bytes','selected_n','failure','elapsed_seconds','retained_bytes_before_manifest']}))
    if manifest['failure']: raise SystemExit(1)
    if manifest['retained_bytes_before_manifest']>300000000: raise SystemExit('Retained ceiling exceeded')

if __name__=='__main__': main()
