"""Offline extraction and AST metadata only. Never imports or executes task code.

Run with the cached Python 3.12 and PYTHONPATH=/tmp/idea19-parquet-reader.
Creates owned outputs exclusively; refuses to replace an existing data pack.
"""
import ast
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import warnings

import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'eval-budget-allocation-pilot-20261017'
PILOT = HERE.parent / 'eval-harness-prompt-pilot-20261026/corrected-20261026'
SOURCE = OLD / 'task_selection/raw-v1/bigcodebench-v0.1.4.parquet'
OFFICIAL = OLD / 'readiness-review-20261021/dependencies/metadata-01/official-requirements.txt'
LOCK = OLD / 'readiness-review-20261021/dependencies/attempt-03/requirements.lock'
SOURCE_SHA = 'd9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267'
OFFICIAL_SHA = 'a4d01fb12cbce5223b51f982265cb7975bea770b758cd85cc91b803d3293e39f'
WORKER_SHA = '2cf0dbefaa0e656458a71192dea12a86dab74e8c3e3c27a202e38cdd26b2b298'
FIELDS = ['task_id', 'code_prompt', 'canonical_solution', 'test', 'entry_point']
ALIASES = {'PIL': 'Pillow', 'bs4': 'beautifulsoup4', 'cv2': 'opencv-python-headless',
           'dateutil': 'python-dateutil', 'docx': 'python-docx', 'sklearn': 'scikit-learn',
           'mpl_toolkits': 'matplotlib'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def write_json(path, value, private=False):
    data = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if private else 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
    return hashlib.sha256(data).hexdigest()


def main():
    assert sha(SOURCE) == SOURCE_SHA and sha(OFFICIAL) == OFFICIAL_SHA
    assert sha(HERE / 'worker.py') == sha(PILOT / 'worker.py') == WORKER_SHA
    selected = json.loads((HERE / 'TASKS.json').read_text())
    assert selected['source_sha256'] == SOURCE_SHA
    ids = [r['task_id'] for r in selected['selected_rows']]
    assert len(ids) == len(set(ids)) == 240
    assert not set(ids).intersection(selected['excluded_task_ids'])
    all_rows = pq.read_table(SOURCE, columns=FIELDS + ['instruct_prompt']).to_pylist()
    assert len(all_rows) == len({r['task_id'] for r in all_rows}) == 1140
    by_id = {r['task_id']: r for r in all_rows if r['task_id'] in set(ids)}
    assert len(by_id) == 240
    for selected_row in selected['selected_rows']:
        assert by_id[selected_row['task_id']]['instruct_prompt'] == selected_row['instruct_prompt']
    official = {}
    for line in OFFICIAL.read_text().splitlines():
        if '==' in line:
            name, version = line.split('==')
            key = normalize(name)
            assert key not in official or official[key].split('==')[1] == version
            official[key] = line
    warnings.filterwarnings('ignore', category=SyntaxWarning)
    counts = collections.Counter()
    component_counts = {k: collections.Counter() for k in ['code_prompt', 'canonical_solution', 'test']}
    inventory = []
    for task_id in ids:
        row = by_id[task_id]
        roots = {k: set() for k in component_counts}
        dynamic = 0
        dynamic_literal_modules = set()
        dynamic_nonliteral = 0
        prompt_lines = len(row['code_prompt'].splitlines())
        for field, source in [('reference', row['code_prompt'] + row['canonical_solution']), ('test', row['test'])]:
            # Both trees must parse; exceptions suppress source text in diagnostics.
            try:
                tree = ast.parse(source)
            except SyntaxError:
                raise ValueError('AST parse failed: ' + task_id + ' ' + field) from None
            for node in ast.walk(tree):
                component = field if field == 'test' else ('code_prompt' if node.lineno <= prompt_lines else 'canonical_solution') if hasattr(node, 'lineno') else 'code_prompt'
                if isinstance(node, ast.Import):
                    roots[component].update(a.name.split('.')[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    assert node.level == 0, 'relative import requires review'
                    roots[component].add(node.module.split('.')[0])
                elif isinstance(node, ast.Call) and ast.unparse(node.func) in ('__import__', 'importlib.import_module'):
                    dynamic += 1
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        module = node.args[0].value.split('.')[0]
                        roots[component].add(module)
                        dynamic_literal_modules.add(module)
                    else:
                        dynamic_nonliteral += 1
        union = set().union(*roots.values())
        counts.update(union)
        for field in roots:
            component_counts[field].update(roots[field])
        inventory.append({'task_id': task_id, 'imports': {k: sorted(v) for k, v in roots.items()}, 'dynamic_import_call_count': dynamic, 'dynamic_literal_modules': sorted(dynamic_literal_modules), 'dynamic_nonliteral_import_count': dynamic_nonliteral})
    # This interpreter's stdlib classification is checked against this selected
    # union; cgi remains stdlib in the target Python 3.9 (removed in Python 3.13).
    stdlib = set(sys.stdlib_module_names) | {'cgi'}
    external = sorted(set(counts) - stdlib)
    requirements = {}
    for line in (PILOT / 'requirements.txt').read_text().splitlines():
        if line and not line.startswith('#'):
            name, version = line.split('==')
            assert official[normalize(name)].split('==')[1] == version
            requirements[normalize(name)] = line
    mappings = {}
    for module in external:
        package = normalize(ALIASES.get(module, module))
        if package == 'regex':
            # No direct official regex pin: retain the cached official-input
            # Python 3.9 resolver projection's transitive NLTK dependency pin.
            assert re.search(r'^regex==2026\.1\.15\s', LOCK.read_text(), re.M)
            line = 'regex==2026.1.15'
        else:
            assert package in official, 'unmapped dependency: ' + module
            line = official[package]
        requirements[package] = line
        mappings[module] = line
    # Dynamic imports are retained as dependency uncertainty, never a task-selection gate.
    print(json.dumps({'dynamic_import_metadata':[{k:v for k,v in r.items() if k != 'imports'} for r in inventory if r['dynamic_import_call_count']]}))
    for name in ['private', 'DATA-PINS.json', 'IMPORT-INVENTORY.json', 'requirements.direct.txt']:
        assert not (HERE / name).exists(), 'refusing overwrite: ' + name
    private = HERE / 'private'
    private.mkdir(mode=0o700)
    pins = {}
    for task_id in ids:
        filename = task_id.split('/')[1] + '.json'
        pins[filename] = write_json(private / filename, {k: by_id[task_id][k] for k in FIELDS}, private=True)
    write_json(HERE / 'DATA-PINS.json', {
        'source': 'https://huggingface.co/datasets/bigcode/bigcodebench/resolve/b74c0d0bf70d2c0bc459be537895cca163007f1a/data/v0.1.4-00000-of-00001.parquet',
        'sha256': SOURCE_SHA, 'tasks_sha256': sha(HERE / 'TASKS.json'),
        'task_count': 240, 'ordered_task_ids': ids, 'private_record_fields': FIELDS,
        'private_task_hashes': pins, 'worker_sha256': WORKER_SHA,
        'private_directory_mode': '0700', 'private_file_mode': '0600',
        'task_execution': False, 'extraction_script_sha256': sha(Path(__file__))})
    with (HERE / 'requirements.direct.txt').open('x') as f:
        f.write('\n'.join(requirements[k] for k in sorted(requirements)) + '\n')
    write_json(HERE / 'IMPORT-INVENTORY.json', {
        'tasks_sha256': sha(HERE / 'TASKS.json'), 'source_sha256': SOURCE_SHA,
        'task_count': 240, 'reference_and_test_AST_trees_parsed': 480, 'parse_errors': 0,
        'method': 'AST walk of code_prompt + canonical_solution and test; source text never executed or emitted. Reference imports attributed by original prompt line boundary.',
        'task_counts_by_import_root': dict(sorted(counts.items())),
        'component_task_counts': {k: dict(sorted(v.items())) for k, v in component_counts.items()},
        'third_party_import_mapping': mappings, 'per_task': inventory,
        'official_requirements': {'path': str(OFFICIAL.relative_to(HERE.parent.parent)), 'sha256': OFFICIAL_SHA, 'url': 'https://raw.githubusercontent.com/bigcode-project/bigcodebench/09dd993f46c3fbf3a799465bb96d524edcb0b199/Requirements/requirements-eval.txt'},
        'supplemental_pin': {'requirement': 'regex==2026.1.15', 'reason': 'Imported by three selected tasks; not directly pinned in official requirements; cached Python3.9 resolver projection via official nltk==3.8.', 'path': str(LOCK.relative_to(HERE.parent.parent)), 'sha256': sha(LOCK)},
        'requirements_sha256': sha(HERE / 'requirements.direct.txt'),
        'limitations': ['AST import inventory is not runtime validation or a complete dynamic dependency detector.', 'Direct requirements are pinned; transitive dependency resolution/builds must be captured remotely.', 'TensorFlow resource fit, wikipedia source build, turtle/Tk/headless display and network-dependent behavior remain remote validation gates.', 'NLTK stopwords was the only statically identified requested corpus; retained pilot assets cover it.'],
        'benchmark_execution': False, 'network_calls': 0})
    print(json.dumps({'private_records': len(pins), 'AST_trees': 480, 'third_party_import_roots': len(external), 'requirement_pins': len(requirements), 'private_source_emitted': False}))


if __name__ == '__main__':
    main()
