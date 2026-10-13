"""Bounded Stage A transport. Dry-run by default; never reads evaluation gold."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

MODEL = "openai/gpt-5.4-mini"
ENDPOINT = "https://ai-gateway.vercel.sh/v1/chat/completions"
INPUT_PRICE = 0.75 / 1_000_000
OUTPUT_PRICE = 4.5 / 1_000_000
MAX_OUTPUT = 4096
MAX_ESTIMATED_INPUT = 10000
MAX_REQUEST_BYTES = 80000
STAGE_CAP = 5.0
BASE = Path(__file__).resolve().parent
ALLOWED_RETURNED_MODELS = ("gpt-5.4-mini", "gpt-5.4-mini-2026-03-17",
                          "openai/gpt-5.4-mini", "openai/gpt-5.4-mini-2026-03-17")
REQUIRED_FILES = ("runner.py", "summarize_pilot.py", "test_runner.py", "test_summary.py",
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


def load_inputs(path):
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list):
        raise ValueError("Expected a JSON array of answering inputs")
    from package.prompt import build_messages
    for row in rows:
        build_messages(row)
        if not row['id']:
            raise ValueError('Empty input ID')
    if len(rows) != 50 or len({r['id'] for r in rows}) != 50:
        raise ValueError("Exactly 50 unique frozen inputs required")
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
        if estimate > MAX_ESTIMATED_INPUT or len(serialized.encode()) > MAX_REQUEST_BYTES:
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


def freeze_contract(inputs, adjudication, rows, payloads, counts, reserves):
    """A prospective template, never self-authorizes execution."""
    return {
        'model': MODEL, 'endpoint': ENDPOINT, 'planned': 50,
        'input_sha256': digest(inputs), 'adjudication_sha256': digest(adjudication),
        'ids': [r['id'] for r in rows],
        'request_sha256': [value_digest(p) for p in payloads],
        'estimated_input_tokens': counts, 'reserves_usd': reserves,
        'files': {name: digest(BASE / name) for name in REQUIRED_FILES},
        'runtime': runtime_identity(), 'allowed_returned_models': list(ALLOWED_RETURNED_MODELS),
        'max_output_tokens': MAX_OUTPUT, 'max_input_tokens': MAX_ESTIMATED_INPUT,
        'stage_cap_usd': STAGE_CAP, 'price_usd_per_million': {'input': .75, 'output': 4.5},
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


def consume_approval(approval_path, out):
    """One Stage A execution, even with a copied manifest or new output directory.

    Never auto-remove this marker. A crash leaves requests possibly billed and
    requires human reconciliation, not a resume/retry.
    """
    save_json(BASE / 'EXECUTION-CONSUMED.json', {
        'approval_sha256': digest(approval_path), 'out': str(Path(out).resolve()),
        'consumed_at_unix': time.time(), 'automatic_resume': False,
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


def run_calls(rows, payloads, reserves, out, session, key):
    """Called only after main validates/consumes HQ approval; injectable for offline tests."""
    import requests
    attempted, received, accounted = 0, 0, 0.0
    stop_reason, first_model = 'completed', None
    started = time.monotonic()
    for row, payload, reserve in zip(rows, payloads, reserves):
        if attempted >= 50 or time.monotonic() - started > 1800 or accounted + reserve > STAGE_CAP:
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
        print(f'{attempted}/50 attempted, {received} received, USD{accounted:.4f} accounted', flush=True)
        if stop_reason != 'completed':
            break
    resources = {'planned': 50, 'attempted': attempted, 'received': received,
        'list_price_plus_unresolved_reserves_usd': accounted,
        'billing_status': 'Usage list-price estimate plus unresolved reserves, not reconciled invoice',
        'elapsed_seconds': time.monotonic() - started, 'stop_reason': stop_reason,
        'returned_model': first_model, 'automatic_retries': 0,
        'unattempted': 50 - attempted}
    save_json(out / 'resources.json', resources)
    return resources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--adjudication', required=True, help='Outcome-blind evaluator annotation freeze; hash only')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--approval', help='Reviewed freeze manifest; required for execution')
    parser.add_argument('--env-file', help='Load AI_GATEWAY_API_KEY without printing it')
    args = parser.parse_args()
    rows = load_inputs(args.inputs)
    payloads, counts = inspect_requests(rows)
    forecast = 1397 * (MAX_ESTIMATED_INPUT * INPUT_PRICE + MAX_OUTPUT * OUTPUT_PRICE)
    if forecast > 40:
        raise ValueError('Whole proposed study forecast exceeds USD40')
    # Conservative per-request byte-based reserve for pilot, not tokenizer estimate.
    reserves = [(len(json.dumps(p).encode()) + 4096) * INPUT_PRICE + MAX_OUTPUT * OUTPUT_PRICE
                for p in payloads]
    if sum(reserves) > STAGE_CAP:
        raise ValueError('Conservative Stage A reserve exceeds USD5')
    expected = freeze_contract(args.inputs, args.adjudication, rows, payloads, counts, reserves)
    approval = None
    if args.execute:
        if not args.approval:
            raise ValueError('No reviewed approval manifest')
        approval = json.loads(Path(args.approval).read_text())
        validate_approval(approval, expected)
        if (BASE / 'EXECUTION-CONSUMED.json').exists():
            raise ValueError('Stage A approval already consumed; no automatic restart')
    out = Path(args.out)
    if out.exists() or out.is_symlink() or any(p.is_symlink() for p in out.parents):
        raise ValueError('Output must be new and not symlinked')
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / 'approval-template.json', {**expected, 'approved': False, 'hq_decision': ''})
    save_json(out / 'preflight.json', {
        'model': MODEL, 'model_identity_limit': 'Gateway alias; returned model retained, not guaranteed immutable snapshot',
        'input_sha256': digest(args.inputs), 'planned': 50, 'calls': 0,
        'estimated_input_tokens': counts, 'pilot_conservative_reserve_usd': sum(reserves),
        'whole_proposed_study_forecast_usd': forecast, 'whole_study_authorized': False,
        'stage_cap_usd': STAGE_CAP, 'max_output_tokens': MAX_OUTPUT,
        'price_usd_per_million': {'input': .75, 'output': 4.5},
        'pricing_sources': ['https://ai-gateway.vercel.sh/v1/models',
                            'https://developers.openai.com/api/docs/models/gpt-5.4-mini'],
    })
    if not args.execute:
        print('Dry run only: 50 inputs validated; no provider calls')
        return
    consume_approval(args.approval, out)
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
    run_calls(rows, payloads, reserves, out, session, key)
    session.close()


if __name__ == '__main__':
    main()
