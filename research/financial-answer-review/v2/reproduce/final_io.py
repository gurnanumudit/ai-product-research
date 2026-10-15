"""Small local-file safety helpers for offline final-test reproduction."""
import hashlib
import json
from pathlib import Path
from safe_output import fresh_output


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def destination(path, input_roots):
    """Refuse existing/symlinked or archive-contained output before input reads."""
    resolved = Path(path).resolve()
    if any(resolved.is_relative_to(Path(root).resolve()) for root in input_roots):
        raise ValueError('Output must be outside every supplied input archive')
    return fresh_output(path)


def bindings(path, required):
    mapping = json.loads(Path(path).read_text())
    if not isinstance(mapping, dict) or set(mapping) != set(required):
        raise ValueError('Exact nonempty input binding key set required')
    for value in mapping.values():
        if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Bindings must contain lowercase SHA256 digests')
    return mapping


def read_bound(path, expected, limit=20000000):
    with Path(path).open('rb') as handle:
        body = handle.read(limit + 1)
    if len(body) > limit:
        raise ValueError('Local input exceeds byte limit')
    if hashlib.sha256(body).hexdigest() != expected:
        raise ValueError('Local input hash mismatch: ' + Path(path).name)
    return body


def save(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')


def receipt(out, input_bindings, historical_source, dependencies):
    save(Path(out) / 'reproduction-manifest.json', {
        'mode': 'offline_local_transformation_not_review_approval',
        'historical_source_sha256': historical_source,
        'input_sha256': input_bindings,
        'code_sha256': {p.name: digest(p) for p in dependencies},
        'files': {p.name: {'sha256': digest(p), 'bytes': p.stat().st_size}
                  for p in sorted(Path(out).iterdir()) if p.is_file()},
        'network_requests': 0, 'model_calls': 0,
        'notice': 'Caller-supplied review judgments are not created or certified by this code.'
    })

