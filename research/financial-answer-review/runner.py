"""Bounded Stage A transport. Dry-run by default; never reads evaluation gold."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

MODEL = "openai/gpt-5.4-mini"
ENDPOINT = "https://ai-gateway.vercel.sh/v1/chat/completions"
INPUT_PRICE = 0.75 / 1_000_000
OUTPUT_PRICE = 4.5 / 1_000_000
MAX_OUTPUT = 4096
MAX_ESTIMATED_INPUT = 10000
MAX_REQUEST_BYTES = 80000
STAGE_CAP = 5.0


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs(path):
    rows = json.loads(Path(path).read_text())
    if not isinstance(rows, list):
        raise ValueError("Expected a JSON array of answering inputs")
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
    encoder = tiktoken.get_encoding("o200k_base")
    payloads = [payload_for(row) for row in rows]
    counts = []
    for payload in payloads:
        serialized = json.dumps(payload, ensure_ascii=False)
        # Count entire request, including schema, plus conservative framing reserve.
        estimate = len(encoder.encode(serialized)) + 1000
        if estimate > MAX_ESTIMATED_INPUT or len(serialized.encode()) > MAX_REQUEST_BYTES:
            raise ValueError("Prompt exceeds prospective cap; stop, do not truncate or replace")
        counts.append(estimate)
    return payloads, counts


def save_json(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--out', required=True)
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
    approval = None
    if args.execute:
        if not args.approval:
            raise ValueError('No reviewed approval manifest')
        approval = json.loads(Path(args.approval).read_text())
        if approval.get('approved') is not True or approval.get('model') != MODEL:
            raise ValueError('Approval does not match this run')
        if approval.get('input_sha256') != digest(args.inputs):
            raise ValueError('Frozen inputs changed')
        for name, expected in approval['files'].items():
            if digest(Path(__file__).parent / name) != expected:
                raise ValueError('Reviewed code changed: ' + name)
    out = Path(args.out)
    if out.exists() or out.is_symlink() or any(p.is_symlink() for p in out.parents):
        raise ValueError('Output must be new and not symlinked')
    out.mkdir(parents=True, exist_ok=False)
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
    import requests
    from dotenv import dotenv_values
    key = os.environ.get('AI_GATEWAY_API_KEY')
    if not key and args.env_file:
        key = dotenv_values(args.env_file).get('AI_GATEWAY_API_KEY')
    if not key:
        raise ValueError('AI_GATEWAY_API_KEY unavailable')
    session = requests.Session()  # requests has no automatic retries by default
    attempted, succeeded, cost = 0, 0, 0.0
    stop_reason = 'completed'
    first_model = None
    started = time.monotonic()
    for row, payload, reserve in zip(rows, payloads, reserves):
        if time.monotonic() - started > 1800 or cost + reserve > STAGE_CAP:
            stop_reason = 'wall_time_or_cost_cap'
            break
        attempted += 1
        save_json(out / f'{attempted:02d}-request.json', {'id': row['id'], 'payload': payload})
        call_start = time.monotonic()
        record = {'id': row['id'], 'attempt': attempted, 'reserve_usd': reserve}
        try:
            response = session.post(ENDPOINT, json=payload,
                headers={'Authorization': 'Bearer ' + key}, timeout=120, allow_redirects=False)
            record['http_status'] = response.status_code
            if response.status_code != 200:
                # Never print provider error bodies or credential-bearing request objects.
                record['status'] = 'http_failure_no_retry'
                cost += reserve  # unresolved bill conservatively reserved
                stop_reason = record['status']
            else:
                body = response.json()
                record['response'] = body
                usage = body.get('usage', {})
                inp, output = usage.get('prompt_tokens'), usage.get('completion_tokens')
                if not isinstance(inp, int) or not isinstance(output, int) or min(inp, output) < 0:
                    cost += reserve
                    stop_reason = 'usage_missing_or_invalid'
                else:
                    billed_estimate = inp * INPUT_PRICE + output * OUTPUT_PRICE
                    cost += billed_estimate
                    record['list_price_cost_usd'] = billed_estimate
                    if inp > MAX_ESTIMATED_INPUT or output > MAX_OUTPUT or billed_estimate > reserve:
                        stop_reason = 'observed_usage_exceeds_bound'
                model = body.get('model')
                if first_model is None:
                    first_model = model
                if not model or model != first_model:
                    stop_reason = 'returned_model_missing_or_changed'
                record['status'] = 'received'
                succeeded += 1
        except (requests.RequestException, ValueError):
            record['status'] = 'transport_or_json_failure_no_retry'
            cost += reserve
            stop_reason = record['status']
        record['elapsed_seconds'] = time.monotonic() - call_start
        save_json(out / f'{attempted:02d}-response.json', record)
        print(f'{attempted}/50 attempted, {succeeded} received, USD{cost:.4f} accounted', flush=True)
        if stop_reason != 'completed':
            break
    save_json(out / 'resources.json', {
        'planned': 50, 'attempted': attempted, 'received': succeeded,
        'list_price_plus_unresolved_reserves_usd': cost,
        'billing_status': 'Usage-based list-price estimate, not reconciled invoice; no credit purchases',
        'elapsed_seconds': time.monotonic() - started, 'stop_reason': stop_reason,
        'returned_model': first_model, 'automatic_retries': 0,
    })
    print('Stopped:', stop_reason)


if __name__ == '__main__':
    main()
