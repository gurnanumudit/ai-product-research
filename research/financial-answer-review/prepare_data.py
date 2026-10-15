"""Pinned training-only FinQA intake. Does not execute reference programs.

Creates a fresh data/ directory, preserving source bytes and separate inputs/gold.
No model call, dev/test request or outcome-dependent sampling is implemented.
"""
from pathlib import Path
import argparse, collections, datetime as dt, decimal, gzip, hashlib, json, math, re, subprocess, tempfile, time

COMMIT = '0f16e2867befa6840783e58be38c9efb9229d742'
BASE_URL = 'https://raw.githubusercontent.com/czyssrs/FinQA/' + COMMIT + '/'
TRAIN_SHA = '49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6'
FILES = ('README.md', 'LICENSE', 'dataset/train.json')
SEED = 'finqa-stage-a-20261012-v1'
QUOTAS = {'table_only|single': 13, 'table_only|multi': 13,
          'text_involved|single': 12, 'text_involved|multi': 12}
MAX_TRANSFER = 100_000_000
MAX_RETAINED = 200_000_000

def sha_bytes(x): return hashlib.sha256(x).hexdigest()
def write_json(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')

def numeric(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        result = decimal.Decimal(str(value))
        return str(result) if result.is_finite() else None
    except decimal.InvalidOperation:
        return None

def stratum(record):
    qa = record.get('qa', {})
    if numeric(qa.get('exe_ans')) is None:
        return None, 'nonfinite_or_nonnumeric_execution_answer'
    if not isinstance(record.get('id'), str) or not isinstance(qa.get('question'), str):
        return None, 'invalid_id_or_question'
    if not qa['question'].strip(): return None, 'empty_question'
    program = qa.get('program')
    if not isinstance(program, str): return None, 'missing_reference_program'
    ops = re.findall(r'\b[a-zA-Z_]+\s*\(', program)
    if not ops: return None, 'missing_reference_operations'
    inds = qa.get('gold_inds')
    if not isinstance(inds, dict) or not inds: return None, 'missing_support_metadata'
    keys = list(inds)
    if any(not isinstance(k, str) or not k.startswith(('text_', 'table_')) for k in keys):
        return None, 'unsupported_support_key'
    evidence = 'text_involved' if any(k.startswith('text_') for k in keys) else 'table_only'
    return evidence + '|' + ('single' if len(ops) == 1 else 'multi'), None

def locations(record):
    """Full neutral context; never consumes QA/reference/support annotations."""
    out = {}
    for field, prefix in [('pre_text', 'pre'), ('post_text', 'post')]:
        values = record.get(field)
        if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
            raise ValueError('Source text schema')
        for i, text in enumerate(values): out[f'{prefix}:{i}'] = text
    table = record.get('table')
    if not isinstance(table, list) or not all(isinstance(r, list) and all(isinstance(v, str) for v in r) for r in table):
        raise ValueError('Source table schema')
    # Full rows preserve headers, order and units without gold-driven retrieval.
    for i, row in enumerate(table): out[f'table:row:{i}'] = ' | '.join(row)
    return out

def select(records):
    ids = [r.get('id') for r in records]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate source IDs')
    pools = {k: [] for k in QUOTAS}; excluded = []
    for r in records:
        key, reason = stratum(r)
        if reason: excluded.append({'id': r.get('id'), 'reason': reason}); continue
        # Source-shape validation is outcome-blind and part of eligibility.
        try: locations(r)
        except ValueError:
            excluded.append({'id': r['id'], 'reason': 'unsupported_source_schema'}); continue
        pools[key].append(r)
    rank = lambda r: (sha_bytes((SEED + '\0' + r['id']).encode()), r['id'])
    for pool in pools.values(): pool.sort(key=rank)
    chosen = []
    for key, quota in QUOTAS.items():
        if len(pools[key]) < quota: raise ValueError('Insufficient frozen stratum: ' + key)
        chosen.extend(pools[key][:quota])
    chosen.sort(key=rank)
    return chosen, pools, excluded

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--out', type=Path, default=Path(__file__).parent / 'data')
    args = parser.parse_args(); out = args.out
    if out.exists() or out.is_symlink(): raise SystemExit('Refuse existing destination')
    out.mkdir(parents=True); source = out / 'source'; source.mkdir(); start = time.monotonic()
    resources = {'external_spend_usd': 0, 'model_calls': 0, 'transfer_bytes': 0, 'attempts': [], 'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
    failure = None
    try:
        # This contract is saved before downloading or inspecting task outcomes.
        write_json(out / 'SELECTION-RULE.json', {'commit': COMMIT, 'split': 'train', 'seed': SEED, 'hash': 'sha256(seed + NUL + id)', 'quotas': QUOTAS, 'numeric_eligibility': 'finite numeric exe_ans, nonempty question/program, supported gold key and complete neutral source shape', 'gold_metadata_use': 'sampling strata and evaluator only; not inputs or verifier', 'no_replacement': True, 'input_fields': ['id', 'question', 'locations']})
        for remote in FILES:
            with tempfile.TemporaryDirectory(prefix='finqa-transfer-') as tmp:
                headers = Path(tmp) / 'headers.txt'
                cmd = ['curl', '--fail', '--silent', '--show-error', '--max-time', '90', '--max-filesize', str(MAX_TRANSFER-resources['transfer_bytes']), '-H', 'Accept-Encoding: gzip', '-D', str(headers), BASE_URL + remote]
                completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                wire = completed.stdout; resources['transfer_bytes'] += len(wire)
                header_text = headers.read_text() if headers.exists() else ''
                attempt = {'url': BASE_URL + remote, 'curl_returncode': completed.returncode, 'wire_bytes': len(wire), 'wire_sha256': sha_bytes(wire), 'headers': header_text}
                resources['attempts'].append(attempt)
                if completed.returncode: raise RuntimeError('Download failed: '+remote+': '+completed.stderr.decode()[:300])
                if resources['transfer_bytes'] > MAX_TRANSFER: raise RuntimeError('Transfer ceiling')
                body = gzip.decompress(wire) if re.search(r'^content-encoding:\s*gzip\s*$', header_text, re.I | re.M) else wire
                if len(body)>100_000_000: raise RuntimeError('Source expansion ceiling')
                name = 'train.json' if remote == 'dataset/train.json' else remote
                if name == 'train.json' and sha_bytes(body) != TRAIN_SHA: raise RuntimeError('Pinned train hash mismatch')
                with (source / name).open('xb') as f: f.write(body)
                attempt.update({'decoded_bytes': len(body), 'sha256': sha_bytes(body), 'retained_path': 'source/'+name})
        records = json.loads((source / 'train.json').read_text())
        if not isinstance(records, list) or len(records)!=6251: raise ValueError('Unexpected train frame')
        chosen, pools, excluded = select(records)
        manifest = {'commit': COMMIT, 'source_train_sha256': TRAIN_SHA, 'source_n': len(records), 'eligible_n': sum(map(len,pools.values())), 'stratum_counts': {k:len(v) for k,v in pools.items()}, 'quotas': QUOTAS, 'seed': SEED, 'selected': [{'id':r['id'], 'stratum':stratum(r)[0], 'rank_hash':sha_bytes((SEED+'\0'+r['id']).encode())} for r in chosen], 'excluded': excluded}
        write_json(out / 'selection.json', manifest)
        inputs = [{'id': r['id'], 'question': r['qa']['question'], 'locations': locations(r)} for r in chosen]
        gold = [{'id': r['id'], 'exe_ans': r['qa']['exe_ans'], 'exe_ans_decimal': numeric(r['qa']['exe_ans']), 'answer': r['qa'].get('answer'), 'program': r['qa']['program'], 'program_re': r['qa'].get('program_re'), 'gold_inds': r['qa']['gold_inds'], 'source_split': 'train', 'scoring_annotation_status': 'pending_unit_scale_audit'} for r in chosen]
        write_json(out / 'inputs.json', inputs); write_json(out / 'gold.json', gold)
        resources['selected_n'] = len(chosen); resources['source_records'] = len(records)
    except Exception as exc:
        failure = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        resources['failure'] = failure; resources['elapsed_seconds'] = round(time.monotonic()-start,3)
        resources['files'] = {str(p.relative_to(out)): {'bytes':p.stat().st_size, 'sha256':sha_bytes(p.read_bytes())} for p in out.rglob('*') if p.is_file()}
        resources['retained_bytes_before_manifest'] = sum(x['bytes'] for x in resources['files'].values())
        write_json(out / 'manifest.json', resources)
        print(json.dumps({k:resources.get(k) for k in ['transfer_bytes','retained_bytes_before_manifest','selected_n','source_records','failure','elapsed_seconds']}, indent=2))
    if failure: raise SystemExit(1)
    if resources['retained_bytes_before_manifest'] > MAX_RETAINED: raise SystemExit('Retained-byte ceiling exceeded')

if __name__ == '__main__': main()
