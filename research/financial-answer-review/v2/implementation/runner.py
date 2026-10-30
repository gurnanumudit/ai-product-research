"""Version2 bounded phase transport. Dry-run by default; never reads evaluation gold."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from decimal import Decimal, InvalidOperation

MODEL = "openai/gpt-5.4-mini"
ENDPOINT = "https://ai-gateway.vercel.sh/v1/chat/completions"
INPUT_PRICE = 0.75 / 1_000_000
OUTPUT_PRICE = 4.5 / 1_000_000
MAX_OUTPUT = 4096
MAX_ESTIMATED_INPUT = 10000
MAX_REQUEST_BYTES = 80000
STAGE_CAP = 5.0
TOTAL_CAP = Decimal('40')
PRIOR_SPEND = Decimal('0.140064')
PHASE_LIMITS = {'dev': 200, 'test': 1147}
BASE = Path(__file__).resolve().parent
ALLOWED_RETURNED_MODELS = ("gpt-5.4-mini", "gpt-5.4-mini-2026-03-17",
                          "openai/gpt-5.4-mini", "openai/gpt-5.4-mini-2026-03-17")
REQUIRED_FILES = ("runner.py", "summarize_pilot.py", "training_check.py", "test_runner.py", "test_summary.py", "test_v2.py", "tests/test_build.py",
                  "package/__init__.py", "package/numbers.py", "package/schema.py",
                  "package/prompt.py", "package/checker.py", "package/scorer.py",
                  "package/policies.py")
DEPENDENCIES = ("requests", "urllib3", "certifi", "charset-normalizer", "idna",
                "python-dotenv", "tiktoken", "regex")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()


def value_digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def runtime_identity():
    """Lightweight dependency identity, not a hermetic OS/TLS attestation."""
    from importlib.metadata import distribution
    packages = {}
    for name in DEPENDENCIES:
        dist = distribution(name)
        packages[name] = dist.version
    return {'python': sys.version, 'executable_sha256': digest(sys.executable),
            'dependencies': packages}


def load_inputs(path, expected_count=50):
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list):
        raise ValueError("Expected a JSON array of answering inputs")
    from package.prompt import build_messages
    for row in rows:
        build_messages(row)
        if not row['id']:
            raise ValueError('Empty input ID')
    if (type(expected_count) is not int or not 1 <= expected_count <= 1147
            or len(rows) != expected_count or len({r['id'] for r in rows}) != expected_count):
        raise ValueError("Exact frozen input count and unique IDs required")
    for row in rows:
        if set(row) != {"id", "question", "locations"}:
            raise ValueError("Unexpected input fields; possible reference leakage")
        if not isinstance(row['locations'], dict):
            raise ValueError("Expected neutral location map")
    return rows


def payload_for(row):
    from package.prompt import build_messages
    from package.schema import RESPONSE_SCHEMA
    return {
        "model": MODEL, "messages": build_messages(row), "stream": False,
        "reasoning_effort": "low", "max_completion_tokens": MAX_OUTPUT,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "financial_answer", "strict": True, "schema": RESPONSE_SCHEMA}},
        "providerOptions": {"gateway": {"only": ["openai"]}},
    }


def inspect_requests(rows):
    import tiktoken
    import tiktoken.load
    # No cache miss may silently trigger a model-vocabulary download.
    original_read = tiktoken.load.read_file
    def local_only(path):
        if str(path).startswith(('https://', 'http://')):
            raise ValueError('Tokenizer cache unavailable; no download authorized')
        return original_read(path)
    tiktoken.load.read_file = local_only
    try:
        encoder = tiktoken.get_encoding("o200k_base")
    finally:
        tiktoken.load.read_file = original_read
    payloads = [payload_for(row) for row in rows]
    counts = []
    for payload in payloads:
        serialized = json.dumps(payload, ensure_ascii=False)
        # Count entire request, including schema, plus conservative framing reserve.
        estimate = len(encoder.encode(serialized, disallowed_special=())) + 1000
        if estimate > MAX_ESTIMATED_INPUT or len(json.dumps(payload).encode()) > MAX_REQUEST_BYTES:
            raise ValueError("Prompt exceeds prospective cap; stop, do not truncate or replace")
        counts.append(estimate)
    return payloads, counts


def save_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    # Persist the new directory entry before any later irreversible request.
    fd = os.open(str(Path(path).parent), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load_budget(path):
    """Two immutable phase allocations, not an automatically recycled wallet."""
    budget = json.loads(Path(path).read_text())
    try:
        if set(budget) != {'schema_version', 'total_cap_usd', 'prior_spend_usd', 'phases'} or budget['schema_version'] != 1:
            raise ValueError('Unexpected budget schema')
        if set(budget['phases']) != {'dev', 'test'}:
            raise ValueError('Only the two approved phases are allowed')
        cap, prior = Decimal(budget['total_cap_usd']), Decimal(budget['prior_spend_usd'])
        if not cap.is_finite() or not prior.is_finite() or cap != TOTAL_CAP or prior < PRIOR_SPEND:
            raise ValueError('Invalid total/prior budget')
        total = prior
        for phase, limit in PHASE_LIMITS.items():
            entry = budget['phases'][phase]
            reserve = Decimal(entry['reserve_usd'])
            if set(entry) != {'max_attempts', 'reserve_usd'} or type(entry['max_attempts']) is not int or entry['max_attempts'] != limit:
                raise ValueError('Unexpected phase attempt cap')
            if not reserve.is_finite() or reserve < 0:
                raise ValueError('Invalid phase allocation')
            total += reserve
        if total > cap:
            raise ValueError('Prior spend plus phase allocations exceeds USD40')
    except (KeyError, TypeError, InvalidOperation) as exc:
        raise ValueError('Malformed budget manifest') from exc
    return budget


def phase_check(phase, count, verification, reserves, budget):
    if phase not in PHASE_LIMITS or type(count) is not int or not 1 <= count <= PHASE_LIMITS[phase]:
        raise ValueError('Invalid phase or count')
    if (phase == 'dev' and (count != 200 or verification != 'both')
            or phase == 'test' and verification not in ('count', 'priority')):
        raise ValueError('Dev requires 200/both candidates; test requires one frozen candidate')
    if len(reserves) != count or sum(Decimal(str(r)) for r in reserves) > Decimal(budget['phases'][phase]['reserve_usd']):
        raise ValueError('Actual phase reserve exceeds its frozen allocation')


def freeze_contract(inputs, adjudication, rows, payloads, counts, reserves,
                    budget_path, protocol_path, phase, verification, groups_path):
    """A prospective template, never self-authorizes execution."""
    return {
        'model': MODEL, 'endpoint': ENDPOINT, 'planned': len(rows),
        'phase': phase, 'verification_candidate': verification,
        'budget_sha256': digest(budget_path), 'budget': load_budget(budget_path),
        'protocol_sha256': digest(protocol_path),
        'group_metadata_sha256': digest(groups_path),
        'input_sha256': digest(inputs), 'adjudication_sha256': digest(adjudication),
        'ids': [r['id'] for r in rows],
        'request_sha256': [value_digest(p) for p in payloads],
        'estimated_input_tokens': counts, 'reserves_usd': reserves,
        'files': {name: digest(BASE / name) for name in REQUIRED_FILES},
        'runtime': runtime_identity(), 'allowed_returned_models': list(ALLOWED_RETURNED_MODELS),
        'max_output_tokens': MAX_OUTPUT, 'max_input_tokens': MAX_ESTIMATED_INPUT,
        'phase_cap_usd': load_budget(budget_path)['phases'][phase]['reserve_usd'],
        'total_cap_usd': '40', 'price_usd_per_million': {'input': .75, 'output': 4.5},
        'automatic_retries': 0, 'no_outcomes_before_review': True,
    }


def validate_approval(approval, expected):
    if (approval.get('approved') is not True or not isinstance(approval.get('hq_decision'), str)
            or not approval['hq_decision'].strip()):
        raise ValueError('Execution requires an explicit logged HQ decision')
    if set(approval) != set(expected) | {'approved', 'hq_decision'}:
        raise ValueError('Incomplete or unexpected approval fields')
    for key, value in expected.items():
        if approval[key] != value:
            raise ValueError('Approval freeze mismatch: ' + key)


def consume_approval(approval_path, out, phase='dev'):
    """One execution per phase, even with a copied manifest or new output directory.

    Never auto-remove this marker. A crash leaves requests possibly billed and
    requires human reconciliation, not a resume/retry.
    """
    if phase not in PHASE_LIMITS:
        raise ValueError('Unknown phase')
    approval = json.loads(Path(approval_path).read_text())
    budget_hash = approval['budget_sha256']
    lock = BASE.parent / 'BUDGET-LOCK.json'
    if lock.exists():
        if json.loads(lock.read_text())['budget_sha256'] != budget_hash:
            raise ValueError('Phase allocations changed after first execution; stop')
    else:
        save_json(lock, {'budget_sha256': budget_hash, 'no_automatic_reallocation': True})
    save_json(BASE.parent / f'EXECUTION-{phase}-CONSUMED.json', {
        'approval_sha256': digest(approval_path), 'out': str(Path(out).resolve()),
        'consumed_at_unix': time.time(), 'automatic_resume': False, 'phase': phase,
    })


def response_content(body):
    """Expose a final answer only for one complete, non-refused assistant choice."""
    if not isinstance(body, dict) or body.get('error'):
        return None, 'invalid_or_error_body'
    choices = body.get('choices')
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return None, 'invalid_choices'
    choice = choices[0]
    message = choice.get('message')
    if not isinstance(message, dict) or message.get('role') != 'assistant':
        return None, 'invalid_message'
    if message.get('refusal'):
        return None, 'refusal'
    if choice.get('finish_reason') != 'stop':
        return None, 'incomplete_or_unexpected_finish'
    if not isinstance(message.get('content'), str) or not message['content'].strip():
        return None, 'missing_content'
    return message['content'], 'complete'


def assess_body(body, reserve, first_model):
    record = {'status': 'received', 'accounted_usd': reserve, 'accounting': 'unresolved_reserved'}
    stop = None
    if not isinstance(body, dict):
        return {**record, 'status': 'invalid_response_body'}, 'invalid_response_body', first_model
    model = body.get('model')
    if model not in ALLOWED_RETURNED_MODELS or (first_model is not None and model != first_model):
        stop = 'returned_model_unexpected_missing_or_changed'
    elif first_model is None:
        first_model = model
    usage = body.get('usage')
    inp = usage.get('prompt_tokens') if isinstance(usage, dict) else None
    output = usage.get('completion_tokens') if isinstance(usage, dict) else None
    if type(inp) is not int or type(output) is not int or min(inp, output) < 0:
        stop = stop or 'usage_missing_or_invalid'
    else:
        billed = inp * INPUT_PRICE + output * OUTPUT_PRICE
        record.update(list_price_cost_usd=billed, accounting='usage_list_price', accounted_usd=billed)
        if inp > MAX_ESTIMATED_INPUT or output > MAX_OUTPUT or billed > reserve:
            record['accounted_usd'] = max(billed, reserve)
            stop = stop or 'observed_usage_exceeds_bound'
    content, content_status = response_content(body)
    record['content_status'] = content_status
    if content_status == 'invalid_or_error_body':
        stop = stop or content_status
    if stop:
        record['status'] = stop
    return record, stop, first_model


def run_calls(rows, payloads, reserves, out, session, key, phase_cap=STAGE_CAP, wall_seconds=7200):
    """Called only after main validates/consumes HQ approval; injectable for offline tests."""
    import requests
    attempted, received, accounted = 0, 0, 0.0
    planned = len(rows)
    if not (planned == len(payloads) == len(reserves)) or not 1 <= planned <= 1147:
        raise ValueError('Frozen run arrays must align within the maximum count')
    stop_reason, first_model = 'completed', None
    started = time.monotonic()
    for row, payload, reserve in zip(rows, payloads, reserves):
        if attempted >= planned or time.monotonic() - started > wall_seconds or accounted + reserve > phase_cap:
            stop_reason = 'attempt_wall_time_or_cost_cap'
            break
        attempted += 1
        # A durable dispatch INTENT precedes session.post. After a crash it means
        # possibly sent/billed, not proof that the provider processed the request.
        save_json(out / f'{attempted:02d}-request.json', {
            'id': row['id'], 'attempt': attempted, 'payload': payload,
            'request_sha256': value_digest(payload), 'reserve_usd': reserve,
            'dispatch_intent_at_unix': time.time(), 'may_have_been_sent': True,
        })
        call_start = time.monotonic()
        record = {'id': row['id'], 'attempt': attempted, 'reserve_usd': reserve,
                  'accounted_usd': reserve, 'accounting': 'unresolved_reserved'}
        try:
            response = session.post(ENDPOINT, json=payload,
                headers={'Authorization': 'Bearer ' + key}, timeout=120, allow_redirects=False)
            record['http_status'] = response.status_code
            if response.status_code != 200:
                record['status'] = stop_reason = 'http_failure_no_retry'
            else:
                body = response.json()
                record['response'] = body
                assessment, stop, first_model = assess_body(body, reserve, first_model)
                record.update(assessment)
                received += 1
                stop_reason = stop or 'completed'
        except (requests.RequestException, ValueError):
            record['status'] = stop_reason = 'transport_or_json_failure_no_retry'
        record['elapsed_seconds'] = time.monotonic() - call_start
        accounted += record['accounted_usd']
        save_json(out / f'{attempted:02d}-response.json', record)
        print(f'{attempted}/{planned} attempted, {received} received, USD{accounted:.4f} accounted', flush=True)
        if stop_reason != 'completed':
            break
    resources = {'planned': planned, 'attempted': attempted, 'received': received,
        'list_price_plus_unresolved_reserves_usd': accounted,
        'billing_status': 'Usage list-price estimate plus unresolved reserves, not reconciled invoice',
        'elapsed_seconds': time.monotonic() - started, 'stop_reason': stop_reason,
        'returned_model': first_model, 'automatic_retries': 0,
        'unattempted': planned - attempted, 'phase_cap_usd': phase_cap}
    save_json(out / 'resources.json', resources)
    return resources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--adjudication', required=True, help='Outcome-blind evaluator annotation freeze; hash only')
    parser.add_argument('--phase', required=True, choices=('dev', 'test'))
    parser.add_argument('--expected-count', required=True, type=int)
    parser.add_argument('--budget', required=True, help='HQ frozen two-phase allocation JSON')
    parser.add_argument('--protocol', required=True, help='Reviewed phase scientific protocol; hash only')
    parser.add_argument('--groups', required=True, help='Frozen selection/group metadata; hash only')
    parser.add_argument('--verification', required=True, choices=('both', 'count', 'priority'))
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--approval', help='Reviewed freeze manifest; required for execution')
    parser.add_argument('--env-file', help='Load AI_GATEWAY_API_KEY without printing it')
    args = parser.parse_args()
    rows = load_inputs(args.inputs, args.expected_count)
    payloads, counts = inspect_requests(rows)
    forecast = float(PRIOR_SPEND) + 1347 * (MAX_ESTIMATED_INPUT * INPUT_PRICE + MAX_OUTPUT * OUTPUT_PRICE)
    if forecast > 40:
        raise ValueError('Whole proposed study forecast exceeds USD40')
    # Conservative per-request byte-based reserve, not an observed billing amount.
    reserves = [(len(json.dumps(p).encode()) + 4096) * INPUT_PRICE + MAX_OUTPUT * OUTPUT_PRICE
                for p in payloads]
    budget = load_budget(args.budget)
    phase_check(args.phase, len(rows), args.verification, reserves, budget)
    expected = freeze_contract(args.inputs, args.adjudication, rows, payloads, counts, reserves,
                              args.budget, args.protocol, args.phase, args.verification, args.groups)
    approval = None
    if args.execute:
        if not args.approval:
            raise ValueError('No reviewed approval manifest')
        approval = json.loads(Path(args.approval).read_text())
        validate_approval(approval, expected)
        if (BASE.parent / f'EXECUTION-{args.phase}-CONSUMED.json').exists():
            raise ValueError('Phase approval already consumed; no automatic restart')
    out = Path(args.out)
    if out.exists() or out.is_symlink() or any(p.is_symlink() for p in out.parents):
        raise ValueError('Output must be new and not symlinked')
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / 'approval-template.json', {**expected, 'approved': False, 'hq_decision': ''})
    save_json(out / 'preflight.json', {
        'model': MODEL, 'model_identity_limit': 'Gateway alias; returned model retained, not guaranteed immutable snapshot',
        'input_sha256': digest(args.inputs), 'planned': len(rows), 'calls': 0, 'phase': args.phase,
        'estimated_input_tokens': counts, 'phase_conservative_reserve_usd': sum(reserves),
        'whole_proposed_study_forecast_usd': forecast,
        'phase_execution_approval_validated': bool(args.execute), 'later_phase_requires_separate_gate': True,
        'phase_cap_usd': budget['phases'][args.phase]['reserve_usd'], 'max_output_tokens': MAX_OUTPUT,
        'budget': budget, 'budget_sha256': digest(args.budget),
        'price_usd_per_million': {'input': .75, 'output': 4.5},
        'pricing_sources': ['https://ai-gateway.vercel.sh/v1/models',
                            'https://developers.openai.com/api/docs/models/gpt-5.4-mini'],
    })
    if not args.execute:
        print(f'Dry run only: {len(rows)} inputs validated; no provider calls')
        return
    consume_approval(args.approval, out, args.phase)
    import requests
    from dotenv import dotenv_values
    key = os.environ.get('AI_GATEWAY_API_KEY')
    if not key and args.env_file:
        key = dotenv_values(args.env_file).get('AI_GATEWAY_API_KEY')
    if not key:
        raise ValueError('AI_GATEWAY_API_KEY unavailable')
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=0))
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=0))
    run_calls(rows, payloads, reserves, out, session, key,
              phase_cap=float(budget['phases'][args.phase]['reserve_usd']),
              wall_seconds=1800 if args.phase == 'dev' else 7200)
    session.close()


if __name__ == '__main__':
    main()
