"""One-use, offline amended audit. Never import a collector or execute candidates.

Only JSON metadata is decoded; private packages and generated Python are hashed.
The original report/audit are historical evidence and are never rewritten.
"""
import argparse
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / 'econ-tool-error-recovery-20261027-main-v1'
NODE = '/Users/muditgurnani/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
PILOT, OLD_INFRA, OLD_API, NEW_INFRA = 4091279770, 24000000000, 469631345, 6000000000
CARRY = PILOT + OLD_INFRA + OLD_API + NEW_INFRA
CAP, RESERVE, MAX_CALLS = 50000000000, 50000000, 572
FORECAST_CAPACITY = 1233  # 2880 - 1647; completed-arm unused slots are not credited.
INITIAL_FORECAST, INITIAL_LARGEST = 3248270, 1624135
RECOVERY = ('BigCodeBench/131', 'B')
RECOVERY_LABEL = 'recovery-task-131-B-final'
LABEL = 'post-HOLD amended completion'
EVALUATOR_COMMIT = 'fd584be94e606dcc605a5b37c108e0a70a93ea20'
VENDOR_FILES = ('bigcodebench/eval/__init__.py', 'bigcodebench/eval/utils.py', 'bigcodebench/eval/_special_oracle.py')
OUTPUTS = ('REPORT-CLAIM.json', 'REPORT-HOLD.json', 'ACTUAL-AUDIT.json', 'ANALYSIS.json', 'REPORT.md')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def integer(value):
    return type(value) is int and 0 <= value <= 2**53 - 1


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def key(row):
    return row['task_id'], row['arm']


def write_once(path, value):
    with Path(path).open('x') as handle:
        handle.write(value if isinstance(value, str) else json.dumps(value, indent=2, allow_nan=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


class Evidence:
    def __init__(self, original, continuation):
        self.original, self.continuation = Path(original).resolve(), Path(continuation).resolve()
        require(self.original != self.continuation, 'original and continuation must be separate')
        self.pins = {}

    def path(self, root, name):
        path = (Path(root) / name).resolve()
        require(path.is_relative_to(Path(root).resolve()), 'evidence path escapes selected root')
        return path

    def pin(self, path):
        path = Path(path).resolve()
        value = digest(path)
        require(str(path) not in self.pins or self.pins[str(path)] == value, 'evidence changed during audit')
        self.pins[str(path)] = value
        return value

    def read(self, root, name):
        path = self.path(root, name)
        require(path.suffix in ('.json', '.jsonl') and 'private' not in path.relative_to(Path(root).resolve()).parts,
                'only non-private JSON metadata may be decoded')
        self.pin(path)
        text = path.read_text()
        return [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == '.jsonl' else json.loads(text)

    def verify_pins(self, root, pins):
        require(isinstance(pins, dict) and pins, 'nonempty pin map required')
        for name, expected in pins.items():
            # Historical release maps contain legitimate sibling projection/source pins.
            path = (Path(root) / name).resolve()
            require(path.is_relative_to(self.original.parent), 'release pin outside workstreams')
            require(self.pin(path) == expected, 'release/evidence pin changed: ' + name)


def load_original_functions(original):
    """Import only offline analysis/report functions, with no bytecode side effects."""
    saved = sys.modules.get('analyze')
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        modules = []
        for name in ('analyze', 'actual_report'):
            spec = importlib.util.spec_from_file_location(name, Path(original) / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            if name == 'analyze':
                sys.modules[name] = module
            spec.loader.exec_module(module)
            modules.append(module)
        return modules
    finally:
        sys.dont_write_bytecode = old_bytecode
        if saved is None:
            sys.modules.pop('analyze', None)
        else:
            sys.modules['analyze'] = saved


def partition_rows(original_rows, rows, todo):
    require(len(original_rows) == len(rows) == 720, 'all 720 assigned rows required')
    old, new = {key(r): r for r in original_rows}, {key(r): r for r in rows}
    require(len(old) == len(new) == 720 and old.keys() == new.keys(), 'duplicate or replaced assigned rows')
    require([key(r) for r in original_rows] == [key(r) for r in rows], 'original row order changed')
    observed = {k for k, r in old.items() if r['observation'] == 'observed'}
    untouched = {k for k, r in old.items() if r['completion'] == 'not_started'}
    require(len(observed) == 576 and len(untouched) == 143 and set(old) - observed - untouched == {RECOVERY},
            'original 576/143/1 coverage binding')
    require(len(todo) == 144 and {key(r) for r in todo} == untouched | {RECOVERY}, 'amendment todo mismatch')
    for item in todo:
        require(all(old[key(item)].get(k) == v for k, v in item.items()), 'amendment original row mismatch')
    for k in observed:
        require(new[k] == old[k], 'original observed outcome replaced')
    for k in untouched:
        require(old[k]['calls'] == 0 and not old[k]['actions'] and not old[k]['evaluations'], 'untouched arm has prior activity')
        require(set(new[k]) == set(old[k]), 'new row must retain original schema')
    for k in new:
        for field in ('schema', 'task_id', 'arm', 'condition', 'block'):
            require(new[k][field] == old[k][field], 'assigned identity changed')
    return old, new, observed, untouched


def validate_recovery(old, row, provenance, evidence):
    allowed = {'observation', 'completion', 'passed', 'final_grade_path', 'final_grade_reason',
               'final_code_syntactically_valid', 'evaluator_count', 'evaluator_seconds', 'evaluations',
               'stop_reason', 'recovery_original_stop_reason', 'recovery_policy',
               'recovery_prior_command_status', 'recovery_disagrees_with_command'}
    added = {'recovery_original_stop_reason', 'recovery_policy'}
    if row['observation'] == 'observed':
        added |= {'recovery_prior_command_status', 'recovery_disagrees_with_command'}
    require(set(row) == set(old) | added, 'recovery schema')
    require(all(row[k] == v for k, v in old.items() if k not in allowed), 'recovery changed prior evidence')
    require(row['recovery_original_stop_reason'] == old['stop_reason'] == 'operational_hold', 'recovery original stop reason')
    require(isinstance(row['recovery_policy'], str) and row['recovery_policy'], 'recovery policy absent')
    require(old['evaluator_count'] == 2 and old['evaluations'][1]['status'] == 'intent', 'old ambiguous intent absent')
    require(row['evaluations'][:2] == old['evaluations'] and len(row['evaluations']) == row['evaluator_count'] == 3,
            'old ambiguous intent must remain distinct')
    last = row['evaluations'][2]
    require(last['index'] == 3 and last['kind'] == 'final_recovery' and last['round'] == old['calls'], 'recovery evaluation identity')
    require(last['candidate_path'] == old['final_candidate_path'] and last['grade_path'] == RECOVERY_LABEL + '.grade.json'
            and last['report_path'] == RECOVERY_LABEL + '.report.json', 'recovery candidate/grade paths')
    if row['observation'] == 'observed':
        require(row['final_grade_path'] == last['grade_path'] and row['completion'] == 'complete' and row['stop_reason'] == 'finish', 'recovery final grade selection')
        require(finite(last['elapsed_seconds']) and math.isclose(row['evaluator_seconds'], old['evaluator_seconds'] + last['elapsed_seconds'], abs_tol=1e-9), 'recovery observed timing')
    else:
        require(last['status'] == 'intent' and last['elapsed_seconds'] is None and row['evaluator_seconds'] == old['evaluator_seconds']
                and row['final_grade_path'] is None and row['passed'] is None, 'unknown recovery grade remains missing')
    # Provenance values are bound by digest, not by inference from command stdout.
    expected = {
        'candidate_sha256': evidence.pin(evidence.path(evidence.original, old['final_candidate_path'])),
        'original_final_command_sha256': evidence.pin(evidence.path(evidence.original, 'task-131-B-eval-2-final.command.json')),
        'finish_action_sha256': evidence.pin(evidence.path(evidence.original, 'task-131-B-call-2.action.json')),
    }
    for name, value in expected.items():
        require(provenance.get(name) == value, 'recovery provenance binding: ' + name)
    command = evidence.read(evidence.original, 'task-131-B-eval-2-final.command.json')
    require(command['exitCode'] == 0, 'original saved final command exit evidence')
    require(provenance['source_task'] == old['task_id'] and provenance['arm'] == old['arm'] and provenance['candidate_path'] == old['final_candidate_path']
            and provenance['old_ambiguous_grade_intent_retained'] is True and provenance['policy'] == row['recovery_policy'], 'recovery provenance identity/policy')
    if row['observation'] == 'observed':
        status = json.loads(command['stdout'])['status']
        require(status == row['recovery_prior_command_status'] and row['recovery_disagrees_with_command'] is (status != last['status']), 'saved command discrepancy disclosure')
    return expected


def validate_grade(g, row, candidate_hash, evidence):
    require(g['task_id'] == row['task_id'] and g['solution_sha256'] == candidate_hash, 'grade/candidate identity binding')
    require(g['status'] in ('pass', 'fail') and type(g['passed']) is bool and g['passed'] == (g['status'] == 'pass'), 'grade verdict')
    require(integer(g['execution_uid']) and g['execution_uid'] != 0 and g['execution_uid_cleanup_verified'] is True and not g.get('local_synthetic_only'), 'grade isolation')
    require(finite(g['elapsed_seconds']), 'grade elapsed time')
    require(g['is_reference'] is False and g['evaluator_commit'] == EVALUATOR_COMMIT
            and g['timeout_seconds'] == 60 and g['hard_timeout_seconds'] == 90, 'frozen grader configuration')
    require(g['task_sha256'] == evidence.pin(evidence.original/'private'/(row['task_id'].split('/')[1]+'.json')), 'private package hash binding')
    require(g['worker_sha256'] == evidence.pin(evidence.original/'worker.py'), 'worker source hash binding')
    require(g['vendor_sha256'] == {name: evidence.pin(evidence.original/'vendor'/name) for name in VENDOR_FILES}, 'vendor source hash binding')
    if g['passed']:
        require(g['test_run_valid'] is True and integer(g['tests_expected']) and g['tests_expected'] > 0 and g['tests_run'] == g['tests_expected'], 'invalid all-tests pass')


def sanitized(g):
    # Exact frozen sanitizer, applied only to recorded feedback metadata.
    return {'status': g['status'], 'feedback': '\n'.join(line for line in g['feedback'].split('\n')
            if line and (not line[0].isspace() or line.lstrip().startswith('File "')))[:4000]}


def parsed_action(model, has_candidate):
    """Mechanical frozen output parsing; never evaluate or display generated code."""
    if model.get('output_status') != 'ok' or not isinstance(model.get('text'), str):
        return {'action': 'invalid', 'reason': model.get('output_status') or 'malformed'}
    text = model['text'].strip()
    if not has_candidate:
        fence = re.fullmatch(r'```(?:python|py)?\s*\n([\s\S]*?)\n```', text)
        code = (fence.group(1) if fence else text).strip()
        return {'action': 'submit', 'code': code+'\n'} if code and '```' not in code else {'action': 'invalid', 'reason': 'malformed'}
    try:
        action = json.loads(text)
        if isinstance(action, dict):
            if action.get('action') in ('finish', 'rerun') and set(action) == {'action'}:
                return action
            if action.get('action') == 'revise' and set(action) == {'action', 'code'} and isinstance(action['code'], str) and action['code'].strip() and '```' not in action['code']:
                return action
    except (ValueError, TypeError):
        pass
    return {'action': 'invalid', 'reason': 'malformed'}


def extract_output(response):
    """Mechanical copy of frozen model-client.extract, without importing client."""
    if response.get('status') == 'incomplete':
        return '', 'incomplete'
    output = response.get('output')
    if response.get('status') != 'completed' or not isinstance(output, list):
        return '', 'malformed'
    messages = [x for x in output if x.get('type') == 'message']
    if len(messages) != 1 or any(x.get('type') not in ('message', 'reasoning') for x in output):
        return '', 'malformed'
    message = messages[0]
    content = message.get('content')
    if message.get('role') != 'assistant' or message.get('status') != 'completed' or not isinstance(content, list) or not content or any(x.get('type') != 'output_text' or not isinstance(x.get('text'), str) for x in content):
        return '', 'malformed'
    text = ''.join(x['text'] for x in content)
    trimmed = text.strip()
    fence = re.fullmatch(r'```(?:python|py)?\s*\n([\s\S]*?)\n```', trimmed)
    code = (fence.group(1) if fence else trimmed).strip()
    return text, 'ok' if code and '```' not in code else 'malformed'


def audit_row(row, root, evidence, recovery=False):
    """Bind all persisted actions/evaluations without executing or viewing code."""
    tid, arm = key(row)
    prefix = 'task-' + tid.split('/')[1] + '-' + arm
    original = evidence.original
    require(row['observation'] in ('observed', 'missing'), 'observation schema')
    require(integer(row['calls']) and row['calls'] <= 4, 'four-call ceiling')
    require(row['completion'] in ('complete', 'incomplete', 'not_started'), 'terminal row completion')
    if row['observation'] == 'observed':
        require(type(row['passed']) is bool and row['completion'] == 'complete', 'observed outcome schema')
    else:
        require(row['passed'] is None and row['completion'] != 'complete', 'unknown outcome cannot become failure')
    actions = row['actions']
    consumed = [a for a in actions if a.get('call_consumed', True) and a['action'] != 'input_limit']
    require(len(consumed) == row['calls'], 'action/call count')
    candidate = None
    for index, action in enumerate(actions, 1):
        cid = f'{prefix}-call-{index}'
        require(action['call_id'] == cid and action['round'] == index and action['action_path'] == cid + '.action.json'
                and action['model_path'] == 'calls/' + cid + '/result.json', 'action identity/path')
        if action['action'] == 'pending':
            require(row['observation'] == 'missing' and index == len(actions), 'pending action on observed row')
            continue
        saved = evidence.read(root, action['action_path'])
        require(all(saved.get(k) == v for k, v in action.items()), 'saved action binding')
        if action['action'] != 'input_limit':
            model = evidence.read(root, action['model_path'])
            require(model['call_id'] == cid and model['output_status'] == action['output_status'], 'action/model identity')
            parsed = parsed_action(model, candidate is not None)
            require(all(saved.get(k) == v for k, v in parsed.items()), 'model/action parse binding')
            response = evidence.read(root, 'calls/' + cid + '/response.json')
            require((model['text'], model['output_status']) == extract_output(response), 'model/raw response binding')
            charge = evidence.read(root, 'calls/' + cid + '/charge.json')
            require(model['cost_nano_usd'] == charge['cost_nano_usd'] and model['usage'] == charge['usage'], 'model/charge binding')
        if action['action'] in ('submit', 'revise'):
            candidate = cid + '.candidate.py'
            require(isinstance(saved.get('code'), str), 'candidate action code absent')
            require(hashlib.sha256(saved['code'].encode()).hexdigest() == evidence.pin(evidence.path(root, candidate)), 'action/candidate hash binding')
        require(action['action'] in ('submit', 'revise', 'finish', 'rerun', 'invalid', 'input_limit'), 'unknown action')
        if action['action'] in ('finish', 'input_limit'):
            require(index == len(actions), 'actions after finish')
    require(row['final_candidate_path'] == candidate and row['final_code_present'] is (candidate is not None), 'final candidate sequence')
    require(row['revisions'] == sum(a['action'] == 'revise' for a in actions)
            and row['explicit_reruns'] == sum(a['action'] == 'rerun' for a in actions)
            and row['invalid_outputs'] == sum(a['action'] == 'invalid' for a in actions)
            and row['candidate_count'] == sum(a['action'] in ('submit', 'revise') for a in actions), 'action counters')
    require(row['evaluator_count'] == len(row['evaluations']), 'evaluation count')
    seconds, completed_evaluations, ambiguous = 0, 0, 0
    for index, evaluation in enumerate(row['evaluations'], 1):
        require(evaluation['index'] == index and 1 <= evaluation['round'] <= row['calls'], 'evaluation index/round')
        eroot = evidence.continuation if recovery and index == 3 else root
        candidate_root = original if recovery else root
        label = RECOVERY_LABEL if recovery and index == 3 else f'{prefix}-eval-{index}-{evaluation["kind"]}'
        require(evaluation['grade_path'] == label + '.grade.json' and evaluation['report_path'] == label + '.report.json', 'evaluation artifact paths')
        prior = [a for a in actions if a['round'] <= evaluation['round'] and a['action'] in ('submit', 'revise')]
        require(prior and evaluation['candidate_path'] == prior[-1]['call_id'] + '.candidate.py', 'evaluation candidate sequence')
        if evaluation['status'] == 'intent':
            require(evaluation['elapsed_seconds'] is None and (row['observation'] == 'missing' or recovery and index == 2), 'ambiguous evaluation retention')
            ambiguous += 1
            for suffix in ('.grade.json', '.report.json', '.command.json'):
                p = evidence.path(eroot, label + suffix)
                if p.exists():
                    evidence.pin(p)
            continue
        g = evidence.read(eroot, evaluation['grade_path'])
        validate_grade(g, row, evidence.pin(evidence.path(candidate_root, evaluation['candidate_path'])), evidence)
        require(evaluation['status'] == g['status'] and evaluation['elapsed_seconds'] == g['elapsed_seconds'], 'evaluation grade metadata')
        require(evidence.read(eroot, evaluation['report_path']) == sanitized(g), 'sanitized report binding')
        require(evidence.read(eroot, label + '.command.json')['exitCode'] == 0, 'grader command status')
        if eroot == evidence.continuation:
            retrieval = evidence.read(eroot, label + '.retrieval.json')
            require(retrieval['method'] == 'SDK readFileToBuffer' and retrieval['path'] == '/opt/idea19/'+label+'.result.json'
                    and integer(retrieval['bytes']) and retrieval['bytes'] > 0 and retrieval['no_grader_reexecution'] is True, 'grader retrieval binding')
        seconds += g['elapsed_seconds']
        completed_evaluations += 1
    require(finite(row['evaluator_seconds']) and math.isclose(seconds, row['evaluator_seconds'], abs_tol=1e-8), 'observed evaluation time sum')
    require(row['automatic_verifications'] == sum(e['kind'] == 'automatic_verification' for e in row['evaluations']), 'automatic verification count')
    expected_evaluations = []
    first_candidate = True
    for action in actions:
        if action['action'] in ('submit', 'revise', 'rerun'):
            expected_evaluations.append(('rerun' if action['action'] == 'rerun' else 'candidate', action['round']))
            if first_candidate and arm == 'C':
                expected_evaluations.append(('automatic_verification', action['round']))
            first_candidate = False
    if candidate:
        expected_evaluations.append(('final', row['calls']))
    if recovery:
        expected_evaluations.append(('final_recovery', 2))
    observed_evaluations = [(e['kind'], e['round']) for e in row['evaluations']]
    require(observed_evaluations == expected_evaluations[:len(observed_evaluations)] and len(observed_evaluations) <= len(expected_evaluations), 'evaluation/action sequence')
    if row['observation'] == 'observed':
        require(observed_evaluations == expected_evaluations and (row['calls'] >= 1 or row['stop_reason'] == 'input_limit'), 'completed evaluation coverage')
    if row['observation'] == 'observed':
        if candidate:
            require(row['final_grade_path'] == row['evaluations'][-1]['grade_path'] and row['evaluations'][-1]['kind'] == ('final_recovery' if recovery else 'final'), 'final grade selection')
            g = evidence.read(evidence.continuation if recovery else root, row['final_grade_path'])
            require(row['passed'] is g['passed'] and row['final_grade_reason'] == g.get('reason'), 'final outcome binding')
            syntax = False if g.get('reason') == 'syntax_error' else True if g['status'] == 'pass' or g.get('reason') in ('test_failure', 'import_error') else None
            require(row['final_code_syntactically_valid'] is syntax, 'syntax binding')
        else:
            require(row['passed'] is False and row['final_grade_path'] is None and row['final_code_syntactically_valid'] is None, 'no-code failure binding')
    if row['first_actual_grade_path']:
        first = row['evaluations'][0]
        require(row['first_actual_grade_path'] == first['grade_path'], 'first grade path')
        g = evidence.read(root, first['grade_path'])
        actual = evidence.read(root, first['report_path'])
        shown = evidence.read(root, row['first_treatment_report_path'])
        require(row['first_actual_passed'] is g['passed'] and row['first_report_differs'] is (actual != shown)
                and row['first_verdict_differs'] is (actual['status'] != shown['status']), 'exposure binding')
        if row['condition'] == 'clean':
            expected_report = actual
        elif row['condition'] == 'misleading success':
            expected_report = {'status': 'pass', 'feedback': ''}
        elif row['condition'] == 'test-tool execution error':
            expected_report = {'status': 'error', 'feedback': 'Test-tool execution error: no usable verdict was returned.'}
        else:
            expected_report = evidence.read(original, 'STALE-CACHE-COMPLETE.json')['reports'][tid]
        require(shown == expected_report, 'frozen first treatment report')
    for path in row['feedback_paths']:
        evidence.read(root, path)
    return {'action_ids': {a['call_id'] for a in consumed}, 'completed_evaluations': completed_evaluations,
            'ambiguous_evaluation_intents': ambiguous, 'observed_evaluator_seconds': seconds}


def audit_messages(row, root, evidence, task, prompts):
    """Rebuild saved request/feedback objects mechanically; no source semantics."""
    messages = [{'role': 'system', 'content': prompts['baseline'] + ('\n\n'+prompts['warning'] if row['arm'] == 'B' else '')},
                {'role': 'user', 'content': task['instruct_prompt']}]
    candidate, first, instruction_added = False, True, False
    feedback_paths = []
    for i, action in enumerate(row['actions']):
        cid, round_number = action['call_id'], action['round']
        request_path = 'calls/'+cid+'/request.json'
        if evidence.path(root, request_path).exists():
            request = evidence.read(root, request_path)
            require(request['body']['input'] == messages, 'exact request history binding')
            require(action['action'] != 'input_limit', 'input limit has dispatched request')
        else:
            require(action['action'] in ('pending', 'input_limit'), 'missing saved request history')
        if action['action'] in ('pending', 'finish', 'input_limit'):
            require(i == len(row['actions'])-1, 'request after terminal action')
            continue
        model = evidence.read(root, action['model_path'])
        if action['action'] == 'invalid':
            if round_number < 4:
                messages += [{'role': 'assistant', 'content': model['text'] or '[No complete usable response]'},
                             {'role': 'user', 'content': prompts['format_error']+'\n'+(prompts['action'] if candidate else prompts['baseline'])}]
            continue
        if action['action'] in ('submit', 'revise'):
            candidate = True
        evaluations = [e for e in row['evaluations'] if e['round'] == round_number and e['kind'] not in ('final', 'final_recovery')]
        path = cid + '.feedback.json'
        if not evidence.path(root, path).exists():
            require(row['observation'] == 'missing' and i == len(row['actions'])-1, 'completed evaluation feedback missing')
            continue
        require(evaluations and all(e['status'] in ('pass', 'fail') for e in evaluations), 'feedback before completed evaluations')
        actual = evidence.read(root, evaluations[0]['report_path'])
        reports = [actual]
        if first:
            first = False
            treated = evidence.read(root, row['first_treatment_report_path'])
            reports = [treated]
            if row['arm'] == 'C':
                require(len(evaluations) == 2 and evaluations[1]['kind'] == 'automatic_verification', 'automatic verification feedback absent')
                verification = evidence.read(root, evaluations[1]['report_path'])
                if treated != verification:
                    reports.append(verification)
        else:
            require(len(evaluations) == 1, 'repeated first-only treatment/verification')
        content = json.dumps({'reports': reports}, ensure_ascii=False, separators=(',', ':'))+'\n'+prompts['action']
        expected = {'reports': reports, 'content': content, 'delivered_to_model': round_number < 4}
        require(evidence.read(root, path) == expected, 'exact feedback content/delivery binding')
        feedback_paths.append(path)
        if round_number < 4:
            messages.append({'role': 'assistant', 'content': model['text']})
            if not instruction_added:
                messages.append({'role': 'system', 'content': prompts['action']})
                instruction_added = True
            messages.append({'role': 'user', 'content': content})
    require(row['feedback_paths'] == feedback_paths, 'feedback path sequence')


def snapshot(calls=0, settled=0, pending=0, forecast=INITIAL_FORECAST, largest=INITIAL_LARGEST):
    return dict(calls=calls, settled_nano_usd=settled, pending_nano_usd=pending,
                retained_carry_nano_usd=CARRY, forecast_per_call_nano_usd=forecast,
                largest_observed_main_call_nano_usd=largest, remaining_call_capacity=FORECAST_CAPACITY-calls,
                whole_completion_projection_nano_usd=CARRY+settled+pending+(FORECAST_CAPACITY-calls)*forecast,
                next_physical_reserve_total_nano_usd=CARRY+settled+pending+RESERVE)


def audit_pre_dispatch_holds(events, rows, allowed_keys, old_call_ids, account, evidence, complete):
    """Prove the narrow pre-reservation exception; never infer it from absence."""
    holds = [e for e in events if e['kind'] == 'model_pre_dispatch_hold']
    require(len(holds) <= 1 and (not holds or not complete), 'pre-dispatch hold requires terminal HOLD')
    paths = {e['artifact_path'] for e in holds}
    require({p.name for p in evidence.continuation.glob('*.predispatch.json')} == paths, 'orphan or missing pre-dispatch artifact')
    by_key = {key(r): r for r in rows}
    financial_ids = {c['call_id'] for c in account['calls']} | {
        e['call_id'] for e in events if e['kind'] in ('model_intent', 'model_settled', 'model_hold')}
    accepted = set()
    for event in holds:
        cid = event['call_id']
        require(key(event) in allowed_keys and key(event) in by_key, 'pre-dispatch outside originally untouched arms')
        row = by_key[key(event)]
        require(event['block'] == row['block'] and event['condition'] == row['condition'], 'pre-dispatch event identity')
        require(cid not in old_call_ids | financial_ids, 'pre-dispatch conflicts with reserved/original call')
        require(row['observation'] == 'missing' and row['passed'] is None and row['completion'] == 'incomplete'
                and row['stop_reason'] == 'operational_hold' and row['actions'], 'pre-dispatch terminal missing row required')
        action = row['actions'][-1]
        require(action['action'] == 'pending' and action['call_id'] == cid and action['round'] == row['calls']
                and action.get('call_consumed', True) is True, 'pre-dispatch terminal pending action binding')
        require(event['artifact_path'] == cid+'.predispatch.json', 'pre-dispatch artifact path binding')
        artifact = evidence.read(evidence.continuation, event['artifact_path'])
        require(set(artifact) == {'call_id', 'request_dispatched', 'financial_reserved', 'stage', 'error_name'}
                and artifact['call_id'] == cid and artifact['request_dispatched'] is False
                and artifact['financial_reserved'] is False and artifact['stage'] == 'pre_reserve'
                and isinstance(artifact['error_name'], str) and artifact['error_name'], 'pre-dispatch artifact binding')
        for root in (evidence.original, evidence.continuation):
            call_dir = evidence.path(root, 'calls/'+cid)
            require(not call_dir.exists() and not call_dir.is_symlink(), 'pre-dispatch has client call directory/receipt')
        require(not evidence.path(evidence.continuation, action['action_path']).exists(), 'pre-dispatch has completed action artifact')
        require(not any(e.get('call_id') == cid and e['kind'] == 'action' for e in events), 'pre-dispatch has completed action event')
        accepted.add(cid)
    return accepted


def reconcile_call_attempts(rows, account, pre_dispatch_ids):
    """Keep interaction attempts separate from reserved/physical billing states."""
    actions = [a for r in rows for a in r['actions'] if a.get('call_consumed', True) and a['action'] != 'input_limit']
    ids = {a['call_id'] for a in actions}
    require(len(ids) == len(actions) and pre_dispatch_ids <= ids, 'duplicate/unbound attempted action')
    require({c['call_id'] for c in account['calls']} == ids - pre_dispatch_ids, 'action/accounting call reconciliation')
    attempted = sum(r['calls'] for r in rows)
    require(attempted == len(actions) == account['reserved_attempts'] + len(pre_dispatch_ids), 'row/accounting call reconciliation')

    def counts(subrows, calls, reserved):
        subids = {a['call_id'] for r in subrows for a in r['actions']}
        return dict(attempted_calls=sum(r['calls'] for r in subrows), reserved_calls=reserved,
                    pre_dispatch_unreserved=len(subids & pre_dispatch_ids),
                    physical_post_intents=sum(c.get('dispatched') is True for c in calls),
                    known_undispatched_reserved=sum(c.get('dispatch_status') == 'known_undispatched' for c in calls),
                    uncertain_dispatch=sum(c.get('dispatch_status') == 'uncertain_dispatch' for c in calls),
                    unresolved_charge_calls=sum(c['pending_nano_usd'] > 0 for c in calls),
                    pending_api_nano_usd=sum(c['pending_nano_usd'] for c in calls))

    result = counts(rows, account['calls'], account['reserved_attempts'])
    require(result['physical_post_intents'] + result['known_undispatched_reserved'] + result['uncertain_dispatch'] == result['reserved_calls'], 'reserved dispatch coverage')
    result['by_arm'] = {arm: counts([r for r in rows if r['arm'] == arm], [c for c in account['calls'] if c['arm'] == arm],
                                   sum(c['arm'] == arm for c in account['calls'])) for arm in 'ABC'}
    return result


def financial_history(events, account, allowed_keys, old_call_ids, pre_dispatch_ids=frozenset()):
    require(events and events[0]['kind'] == 'claim' and events[-1]['kind'] in ('hold', 'collection_complete'), 'terminal financial envelope')
    records = {c['call_id']: c for c in account['calls']}
    require(len(records) == len(account['calls']) and not records.keys() & old_call_ids, 'duplicate original/new call IDs')
    require(all(key(c) in allowed_keys for c in records.values()), 'new call outside 143 untouched arms')
    calls = settled = pending = 0
    forecast, largest = INITIAL_FORECAST, INITIAL_LARGEST
    active, resolved, checks = set(), set(), []
    stopped = False
    seen_pre_dispatch = set()
    for sequence, event in enumerate(events, 1):
        kind = event['kind']
        require(event['sequence'] == sequence, 'event sequence')
        require(kind not in ('hold', 'collection_complete') or sequence == len(events), 'events after terminal marker')
        require(kind != 'claim' or sequence == 1, 'duplicate claim event')
        if kind == 'model_intent':
            cid = event['call_id']
            require(not stopped and calls < MAX_CALLS and cid in records and cid not in active | resolved, 'financial intent identity/limit')
            require(key(event) == key(records[cid]), 'financial intent task-arm')
            before = snapshot(calls, settled, pending, forecast, largest)
            require(before['whole_completion_projection_nano_usd'] <= CAP and before['next_physical_reserve_total_nano_usd'] <= CAP, 'inadmissible dispatch')
            checks.append({'call_id': cid, 'sequence': sequence, 'before': before})
            active.add(cid)
            calls += 1
            pending += RESERVE
        elif kind == 'model_pre_dispatch_hold':
            cid = event['call_id']
            require(not stopped and not active and cid in pre_dispatch_ids and cid not in records and cid not in old_call_ids
                    and cid not in seen_pre_dispatch and key(event) in allowed_keys, 'unaudited/conflicting pre-dispatch hold')
            seen_pre_dispatch.add(cid)
            stopped = True
        elif kind in ('model_settled', 'model_hold'):
            cid = event['call_id']
            require(cid in active and cid not in resolved, 'settlement without unique intent')
            record = records[cid]
            if record.get('usage') is not None:
                cost = record['settled_nano_usd']
                require(integer(cost), 'unknown settled cost')
                settled += cost
                pending -= RESERVE
                largest = max(largest, cost)
                forecast = max(forecast, 2*largest)
            elif record.get('dispatch_status') == 'known_undispatched':
                pending -= RESERVE
                require(kind == 'model_hold', 'undispatched cannot settle')
            else:
                require(kind == 'model_hold' and record['pending_nano_usd'] == RESERVE, 'unknown charge must retain reserve')
            active.remove(cid)
            resolved.add(cid)
            if kind == 'model_settled':
                require(record['settled_nano_usd'] <= RESERVE and snapshot(calls, settled, pending, forecast, largest)['whole_completion_projection_nano_usd'] <= CAP, 'settlement should hold')
            else:
                stopped = True
        elif kind == 'hold':
            stopped = True
        if kind in ('claim', 'model_intent', 'model_settled', 'model_hold', 'model_pre_dispatch_hold', 'hold', 'collection_complete'):
            for field, value in snapshot(calls, settled, pending, forecast, largest).items():
                require(type(event.get(field)) is int and event[field] == value, 'financial snapshot mismatch: ' + field)
    require(seen_pre_dispatch == pre_dispatch_ids, 'pre-dispatch event coverage')
    require(set(records) == active | resolved and calls == account['reserved_attempts'] and settled == account['settled_nano_usd']
            and pending == account['pending_nano_usd'], 'receipt/event reconciliation')
    if events[-1]['kind'] == 'collection_complete':
        require(not stopped and not active and pending == 0, 'unresolved complete accounting')
    terminal = snapshot(calls, settled, pending, forecast, largest)
    return dict(terminal=terminal, dispatch_checks=checks, combined_committed_nano_usd=CARRY+settled+pending,
                actual_plus_pending_cap_satisfied=CARRY+settled+pending <= CAP,
                remaining_forecast_cap_satisfied=terminal['whole_completion_projection_nano_usd'] <= CAP,
                stopped=stopped, active_unresolved_intents=sorted(active), combined_cap_nano_usd=CAP,
                initial_combined_forecast_nano_usd=snapshot()['whole_completion_projection_nano_usd'])


def inspect_costs(original, continuation, node=NODE):
    """Use frozen receipt reconciliation; no collector/client imports or network."""
    script = r"""
import fs from 'node:fs'; import path from 'node:path'; import {pathToFileURL} from 'node:url';
const [oldRoot,newRoot]=process.argv.slice(1);
const {inspectCosts,inspectFinancialHistory}=await import(pathToFileURL(path.join(oldRoot,'audit-costs.mjs')));
const {generationId}=await import(pathToFileURL(path.join(oldRoot,'billing-scoped.mjs')));
const old=inspectCosts(oldRoot), fresh=inspectCosts(newRoot);
const generations=[];
for(const [root,costs] of [[oldRoot,old],[newRoot,fresh]]) for(const call of costs.totals.calls){
 const f=path.join(root,'calls',call.call_id,'response.json');
 if(fs.existsSync(f))generations.push(generationId(JSON.parse(fs.readFileSync(f,'utf8'))));
}
if(new Set(generations).size!==generations.length)throw Error('duplicate physical generation across phases');
console.log(JSON.stringify({old,fresh,oldFinancial:inspectFinancialHistory(oldRoot,old.totals)}));
"""
    return json.loads(subprocess.check_output([node, '--input-type=module', '-e', script, str(original), str(continuation)], text=True, stderr=subprocess.PIPE))


def combine_accounts(old, fresh):
    """Sum disjoint physical attempts and coverage, preserving unknown totals."""
    counts = ('reserved_attempts', 'known_undispatched', 'uncertain_dispatch', 'physical_post_intents',
              'settled_calls', 'settled_nano_usd', 'pending_nano_usd', 'receipt_gets')
    result = {k: old[k] + fresh[k] for k in counts}
    result['calls'] = old['calls'] + fresh['calls']
    require(len({c['call_id'] for c in result['calls']}) == len(result['calls']), 'duplicate combined calls')
    result['by_arm'] = {}
    usage_keys = ('input_tokens', 'output_tokens', 'reasoning_tokens', 'cached_tokens', 'cache_write_tokens', 'provider_latency_ms')
    coverage = ('usage_known_calls', 'usage_unknown_calls', 'cache_write_unknown_calls', 'latency_known_calls', 'latency_unknown_calls')
    for arm in 'ABC':
        parts = [a['by_arm'].get(arm) for a in (old, fresh)]
        parts = [p for p in parts if p is not None]
        require(parts, 'arm accounting absent')
        out = {k: sum(p[k] for p in parts) for k in (*counts[:-1], *coverage, *('known_' + k for k in usage_keys))}
        for k in usage_keys:
            out[k] = None if any(p[k] is None for p in parts) else sum(p[k] for p in parts)
        result['by_arm'][arm] = out
    return result


def resource_audit(data, evidence, complete):
    closures = data['resource_closures']
    require([c['block'] for c in closures] == [10, 11, 12][:len(closures)] and len(closures) <= 3, 'continuation block sequence')
    recorded = {c['block'] for c in closures}
    for suffix in ('DISPATCH', 'HOST', 'RESOURCE-CLOSURE'):
        require(all(int(p.name.split('-')[1]) in recorded for p in evidence.continuation.glob('block-*-'+suffix+'.json')), 'unreported continuation resource')
    unresolved, unknown_usage = [], []
    for c in closures:
        n = c['block']
        require(evidence.read(evidence.continuation, f'block-{n}-RESOURCE-CLOSURE.json') == c, 'resource closure binding')
        name = f'econ-tool-recovery-completion-v1-20261029-{n}'
        require(c.get('name', name) == name and c['infrastructure_reserve_usd'] == 2, 'resource identity/reserve')
        if c.get('creation_dispatched'):
            d = evidence.read(evidence.continuation, f'block-{n}-DISPATCH.json')
            require(d['name'] == name and d['timeout_ms'] == 14400000 and d['infrastructure_reserve_usd'] == 2, 'resource dispatch bounds')
        if c.get('creation_confirmed'):
            h = evidence.read(evidence.continuation, f'block-{n}-HOST.json')
            require(h['name'] == name and h['vcpus'] == 2 and h['memory'] == 4096, 'resource host bounds')
        if complete:
            require(c.get('creation_dispatched') is True and c.get('creation_confirmed') is True, 'complete resource creation evidence')
        verification = c.get('verification')
        closed = c.get('stopped') is True and c.get('deleted') is True and isinstance(verification, dict) and verification.get('empty') is True
        if not closed:
            unresolved.append(n)
        if not (finite(c.get('billable_egress_bytes')) and c['billable_egress_bytes'] <= 2e9 and finite(c.get('observed_resource_cost_upper_usd')) and c['observed_resource_cost_upper_usd'] <= 2):
            unknown_usage.append(n)
    if complete:
        require(len(closures) == 3 and not unresolved and not unknown_usage, 'complete continuation resource bounds/closure')
    cleanup = evidence.read(evidence.original, 'APPROVED-CLEANUP-RESULT-v1.json')
    require(cleanup.get('closure_verified') is True and cleanup.get('deleted') is True and isinstance(cleanup.get('verification'), dict) and cleanup['verification'].get('empty') is True
            and cleanup['name'] == 'econ-tool-recovery-main-v1-20261027-10', 'old host10 additive cleanup evidence')
    return dict(recorded=len(closures), verified_closed=len(closures)-len(unresolved), unresolved_blocks=unresolved,
                unknown_usage_blocks=unknown_usage, planned_hosts=3, original_host10_cleanup_verified=True,
                original_host10_usage=cleanup.get('usage'), original_resource_history_unchanged=True)


def render_amended(summary, original_report_module):
    # Reuse the frozen tables; replace the entire historical financial/resource
    # paragraph, rather than silently inheriting its fixed $24/12-host labels.
    lines = original_report_module.render_report(summary).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith('Main settled API:'))
    end = next(i for i, line in enumerate(lines) if line.startswith('Resource closures verified:'))
    f, r = summary['financial_audit'], summary['resource_audit']
    lines[start:end+1] = [
        f"Original main API: ${OLD_API/1e9:.9f}; new API: ${f['terminal']['settled_nano_usd']/1e9:.9f}; new pending reserve: ${f['terminal']['pending_nano_usd']/1e9:.9f}.",
        f"Retained pilot carry: ${PILOT/1e9:.9f}; old infrastructure reserve: $24; new infrastructure reserve: $6. Combined committed plus reserves: ${f['combined_committed_nano_usd']/1e9:.9f} / $50. Infrastructure invoices and human/Codex costs remain unknown/unmeasured.",
        f"Initial continuation forecast: $38.566028025; terminal remaining-capacity forecast: ${f['terminal']['whole_completion_projection_nano_usd']/1e9:.9f}. The forecast retains all 1,233 original unused call slots minus new calls; completed-arm unused slots are not credited. Actual new calls remain limited to 572. Forecasts are not worst-case bounds. Old API is included once in carry; original plus new model calls and API are combined only for main analysis.",
        f"New resource closures verified: {r['verified_closed']}/{r['recorded']} (3 planned; original blocks 10/11/12). Unresolved: {r['unresolved_blocks']}; unknown new usage: {r['unknown_usage_blocks']}. Old host10 has additive cleanup confirmation; its original unresolved usage remains unknown and all old reserves remain retained.",
    ]
    lines[0] = '# Tool-error recovery — ' + LABEL
    lines = [line.replace('| Arm | Calls |', '| Arm | Attempted calls |') for line in lines]
    lines[4] = lines[4].replace('This final main report', 'This amended report')
    recovery = summary['recovery_status']
    lines[1:1] = ['', 'The original main-v1 report remains the primary historical report. This additive completion changed recovery policy after results were known; it is not a pristine preregistered complete run. Original 576 observed outcomes are unchanged; only originally missing outcomes may be filled.',
                  '', 'B/131 retains the exact original final candidate and both old evaluations. The saved original final command exited 0 with a test-failure indication, but full-grade retrieval failed; that command is not used to infer or replace the original missing outcome. The prespecified single final_recovery evaluation determines the amended outcome regardless of agreement. The old ambiguous intent remains distinct. '
                  + f"Recovery status: {recovery['observation']}; command/recovery disagreement: {recovery['disagrees_with_command']}.",
                  '', f"Evaluator counts in the inherited tables are recorded intents, including the old ambiguous intent. Confirmed saved evaluations: {summary['evaluation_audit']['completed_evaluations']}; ambiguous intents: {summary['evaluation_audit']['ambiguous_evaluation_intents']}. Tool seconds are an observed subtotal; the old ambiguous execution duration is unknown."]
    attempts = summary['call_attempt_audit']
    lines += ['', 'Interaction attempts include proven pre-dispatch failures before any financial reservation. Reserved calls, physical POST intents, reserved-but-known-undispatched calls, uncertain dispatch and unresolved charges are separate. A pending interaction action does not by itself establish a pending charge. Client failures retain their original billing classification and unknown reserves.', '',
              '| Arm | Attempted calls | Reserved calls | Proven pre-dispatch / unreserved | Physical POST intents | Reserved / known undispatched | Uncertain dispatch | Unresolved charges | Pending API reserve USD |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm, c in attempts['by_arm'].items():
        lines.append('| '+' | '.join(map(str, [arm, c['attempted_calls'], c['reserved_calls'], c['pre_dispatch_unreserved'],
                     c['physical_post_intents'], c['known_undispatched_reserved'], c['uncertain_dispatch'],
                     c['unresolved_charge_calls'], f"{c['pending_api_nano_usd']/1e9:.9f}"]))+' |')
    return '\n'.join(lines) + '\n'


def audit_and_report(root=HERE, original=ORIGINAL, node=NODE):
    root, original = Path(root).resolve(), Path(original).resolve()
    require(root != original, 'refusing original report directory')
    require(all(not (root / name).exists() for name in OUTPUTS), 'refusing report overwrite/replay')
    terminal = [name for name in ('COLLECTION-COMPLETE.json', 'HOLD.json') if (root/name).exists()]
    require(len(terminal) == 1, 'exactly one terminal collector marker required')
    write_once(root/'REPORT-CLAIM.json', {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pid': os.getpid(), 'phase': 'continuation', 'label': LABEL, 'no_replay': True})
    try:
        return _report(root, original, node, terminal[0])
    except Exception as error:
        write_once(root/'REPORT-HOLD.json', {'error_type': type(error).__name__, 'reason': str(error), 'no_replay': True})
        raise


def _report(root, original, node, terminal):
    evidence = Evidence(original, root)
    read = evidence.read
    release = read(root, 'RELEASE.json')
    require(release.get('accepted') is True and release.get('phase') == 'continuation' and release.get('independent_review_accepted') is True, 'independent continuation release required')
    require(all(Path(p).is_absolute() for p in release['files']), 'continuation release requires absolute pins')
    required = [root/n for n in ('AMENDMENT.json', 'PROTOCOL.md', 'report_continuation.py', 'test_report_continuation.py', 'REPORTER-NOTES.json')]
    required += [original/n for n in ('RELEASE.json', 'RESULTS.json', 'ACTUAL-AUDIT.json', 'ANALYSIS.json', 'REPORT.md', 'HOLD.json',
                 'analyze.py', 'actual_report.py', 'audit-costs.mjs', 'billing-scoped.mjs', 'APPROVED-CLEANUP-RESULT-v1.json', 'task-131-B-eval-2-final.command.json')]
    required += [p for p in root.iterdir() if p.suffix in ('.py', '.mjs', '.sh')]
    require(all(str(p) in release['files'] for p in required), 'required original/new source pin absent')
    evidence.verify_pins(root, release['files'])
    old_release = read(original, 'RELEASE.json')
    evidence.verify_pins(original, old_release['files'])
    old_audit = read(original, 'ACTUAL-AUDIT.json')
    require(old_audit['accepted'] is True and old_audit['observed_arms'] == 576, 'original historical audit')
    evidence.verify_pins(original, old_audit['files'])
    amendment = read(root, 'AMENDMENT.json')
    provenance = read(root, 'RECOVERY-PROVENANCE.json') if (root/'RECOVERY-PROVENANCE.json').exists() else None
    require(amendment['source_results_sha256'] == evidence.pin(original/'RESULTS.json'), 'original results amendment pin')
    for field, expected in dict(cap_usd=50, old_api_nano_usd=OLD_API, old_pending_nano_usd=0, pilot_carry_nano_usd=PILOT,
                                old_main_infra_nano_usd=OLD_INFRA, new_infra_nano_usd=NEW_INFRA, new_max_calls=MAX_CALLS,
                                forecast_per_call_nano_usd=INITIAL_FORECAST, combined_projection_nano_usd=snapshot()['whole_completion_projection_nano_usd']).items():
        require(amendment[field] == expected, 'amendment finance binding: ' + field)
    claim = read(root, 'CLAIM.json')
    require(claim['phase'] == 'continuation' and claim['release_sha256'] == evidence.pin(root/'RELEASE.json'), 'collector claim/release binding')
    old_data, data, marker = read(original, 'RESULTS.json'), read(root, 'RESULTS.json'), read(root, terminal)
    require(data['phase'] == 'continuation' and Path(data['source_main']).resolve() == original and data['original_calls'] == 1647
            and data['assigned_tasks'] == 240 and data['assigned_arms'] == 720, 'continuation dataset identity')
    complete = terminal == 'COLLECTION-COMPLETE.json'
    require(data['collection_status'] == ('complete' if complete else 'held'), 'terminal collection status')
    old, new, observed, untouched = partition_rows(old_data['results'], data['results'], amendment['todo'])
    recovery_attempted = new[RECOVERY] != old[RECOVERY]
    if recovery_attempted:
        require(provenance is not None, 'recovery provenance required')
        recovery_hashes = validate_recovery(old[RECOVERY], new[RECOVERY], provenance, evidence)
    else:
        require(not complete and provenance is None, 'complete report requires recovery')
        recovery_hashes = None
    tasks = read(original, 'TASKS.json')['selected_rows']
    prompts = read(original, 'PROMPTS.json')
    schedule = read(original, 'SCHEDULE.json')
    bytask, byschedule = {t['task_id']: t for t in tasks}, {t['task_id']: t for t in schedule}
    require(len(bytask) == len(byschedule) == 240 and bytask.keys() == byschedule.keys(), 'original schedule identity')
    require(Counter(r['condition'] for r in schedule) == dict.fromkeys(('clean', 'test-tool execution error', 'misleading success', 'stale test report'), 60), 'condition allocation')
    rows, action_ids, evaluation_audit = [], set(), Counter()
    for row in data['results']:
        k = key(row)
        source = original if k in observed or k == RECOVERY else root
        sched = byschedule[row['task_id']]
        require(row['condition'] == sched['condition'] and row['block'] == sched['block'] and row['arm'] in sched['arms'], 'assigned schedule binding')
        if row['completion'] != 'not_started':
            result_root = root if k == RECOVERY and recovery_attempted else source
            require(read(result_root, 'result-' + row['task_id'].split('/')[1] + '-' + row['arm'] + '.json') == row, 'individual result binding')
        checked = audit_row(row, source, evidence, k == RECOVERY and recovery_attempted)
        audit_messages(row, source, evidence, bytask[row['task_id']], prompts)
        require(not action_ids & checked['action_ids'], 'duplicate action call')
        action_ids |= checked.pop('action_ids')
        evaluation_audit.update(checked)
        rows.append({**row, 'domain': bytask[row['task_id']]['domain'], 'completed': row['completion'] == 'complete'})
    costs = inspect_costs(original, root, node)
    for source, name in ((original, 'old'), (root, 'fresh')):
        evidence.verify_pins(source, costs[name]['pins'])
    prior, fresh = costs['old']['totals'], costs['fresh']['totals']
    require(prior['settled_nano_usd'] == OLD_API and prior['pending_nano_usd'] == 0 and prior['reserved_attempts'] == 1647, 'original API carry mismatch')
    require(prior == old_audit['accounting'], 'original accounting changed')
    account = combine_accounts(prior, fresh)
    events = read(root, 'EVENTS.jsonl')
    old_call_ids = {c['call_id'] for c in prior['calls']}
    pre_dispatch_ids = audit_pre_dispatch_holds(events, rows, untouched, old_call_ids, fresh, evidence, complete)
    attempts = reconcile_call_attempts(rows, account, pre_dispatch_ids)
    new_attempts = reconcile_call_attempts([r for r in rows if key(r) in untouched], fresh, pre_dispatch_ids)
    financial = financial_history(events, fresh, untouched, old_call_ids, pre_dispatch_ids)
    for field, value in financial['terminal'].items():
        require(data[field] == value and marker[field] == value, 'terminal accounting binding: ' + field)
    resource = resource_audit(data, evidence, complete)
    if complete:
        require(all(r['observation'] == 'observed' for r in rows) and financial['actual_plus_pending_cap_satisfied'] and financial['remaining_forecast_cap_satisfied'], 'invalid completed coverage/finance')
    analysis, old_report = load_original_functions(original)
    summary = analysis.summarize(rows, 240, bootstrap=True)
    summary.update(phase='continuation', label=LABEL, original_report_primary_historical=True, pristine_preregistered_complete=False,
                   accounting=account, original_accounting=prior, new_accounting=fresh, financial_audit=financial,
                   resource_audit=resource, resource_closures=data['resource_closures'], evaluation_audit=dict(evaluation_audit),
                   infrastructure_actual_usd=data['actual_infrastructure_usd'], infrastructure_reserve_usd=30,
                   pilot_carry_usd=PILOT/1e9, human_codex_costs='unmeasured', collection_status=data['collection_status'],
                   recovery_provenance=provenance, recovery_hashes=recovery_hashes)
    summary.update(call_attempt_audit=attempts, new_call_attempt_audit=new_attempts,
                   pre_dispatch_unreserved_call_ids=sorted(pre_dispatch_ids))
    summary['recovery_status'] = {'observation': new[RECOVERY]['observation'], 'disagrees_with_command': new[RECOVERY].get('recovery_disagrees_with_command')}
    summary['evidence_locations'] = {'original_observed': {'root': str(original), 'keys': sorted(observed)},
                                     'new_arms': {'root': str(root), 'keys': sorted(untouched)},
                                     'recovery': {'key': list(RECOVERY), 'candidate_actions_old_evaluations_root': str(original), 'new_grade_root': str(root)}}
    summary['secondary'] = {a: old_report.secondary_metrics([r for r in rows if r['arm'] == a], account['by_arm'][a]) for a in 'ABC'}
    exposure = ('assigned', 'first_grade_observed', 'first_actual_failed', 'first_report_differs', 'first_verdict_differs', 'first_report_comparison_unknown', 'first_fail_final_pass')
    summary['descriptive_condition_exposure'] = {c: {a: {k: v for k, v in old_report.secondary_metrics([r for r in rows if r['arm'] == a and r['condition'] == c], {}).items() if k in exposure} for a in 'ABC'} for c in analysis.CONDITIONS}
    summary['descriptive_domains'] = {d: {a: analysis.metrics([r for r in rows if r['domain'] == d and r['arm'] == a]) for a in 'ABC'} for d in sorted({t['domain'] for t in tasks})}
    # Pin remaining call/grade/command/result/code artifacts mechanically, including
    # evidence not decoded above. Never decode hidden packages or generated code.
    for directory in (original, root):
        for p in directory.iterdir():
            if p.is_file() and (p.name.startswith(('task-', 'result-', 'recovery-', 'block-'))):
                evidence.pin(p)
        calls_dir = directory/'calls'
        if calls_dir.exists():
            for p in calls_dir.rglob('*'):
                if p.is_file():
                    evidence.pin(p)
    evidence.pin(root/'REPORT-CLAIM.json')
    # Recheck all pins to detect concurrent collection or evidence modification.
    require(all(digest(p) == value for p, value in evidence.pins.items()), 'evidence changed before report commit')
    audit = dict(accepted=True, phase='continuation', label=LABEL, assigned_arms=720,
                 observed_arms=sum(r['observation'] == 'observed' for r in rows), unchanged_original_observed_arms=576,
                 files=evidence.pins, verified_files=len(evidence.pins), accounting=account, financial_audit=financial,
                 resource_audit=resource, evaluation_audit=dict(evaluation_audit), no_execution_or_provider_calls=True,
                 call_attempt_audit=attempts, new_call_attempt_audit=new_attempts, pre_dispatch_unreserved_call_ids=sorted(pre_dispatch_ids),
                 independent_actual_review_pending=True, further_study_authorized=False)
    report = render_amended(summary, old_report)
    write_once(root/'ACTUAL-AUDIT.json', audit)
    write_once(root/'ANALYSIS.json', summary)
    write_once(root/'REPORT.md', report)
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actual', action='store_true', required=True)
    parser.parse_args()
    result = audit_and_report()
    print(json.dumps({'accepted': True, 'label': LABEL, 'observed_arms': result['observed_arms']}))


if __name__ == '__main__':
    main()
