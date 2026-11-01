"""Invented metadata only. No real reporting, model, grader, or network calls."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import report_continuation as report


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')))


def events(path, rows):
    path.write_text(''.join(json.dumps(e)+'\n' for e in rows))


def row(tid='BigCodeBench/900001', arm='A', condition='clean', observed=False):
    return dict(schema=1, task_id=tid, arm=arm, condition=condition, block=10,
                observation='observed' if observed else 'missing', completion='complete' if observed else 'not_started',
                passed=False if observed else None, first_actual_passed=None, first_report_differs=None, first_verdict_differs=None,
                final_candidate_path=None, final_grade_path=None, first_actual_grade_path=None, first_treatment_report_path=None,
                final_code_present=False, final_code_syntactically_valid=None, final_grade_reason=None,
                calls=0, revisions=0, explicit_reruns=0, automatic_verifications=0, evaluator_count=0, evaluator_seconds=0,
                candidate_count=0, invalid_outputs=0, actions=[], evaluations=[], feedback_paths=[], stop_reason='input_limit' if observed else None)


def cohort():
    rows = [row('BigCodeBench/'+str(900000+i), a, ('clean', 'test-tool execution error', 'misleading success', 'stale test report')[i//60], i < 192)
            for i in range(240) for a in 'ABC']
    rows[577].update(task_id=report.RECOVERY[0], arm='B', completion='incomplete', calls=2)
    todo = [{k: r[k] for k in ('task_id', 'arm', 'condition', 'block', 'completion', 'calls', 'final_candidate_path')} for r in rows[576:]]
    return rows, todo


def grade_fixture(evidence, row_value, code_path, passed=False):
    source = evidence.original
    for path, text in [(source/'worker.py', '# invented worker bytes'),
                       (source/'private'/(row_value['task_id'].split('/')[1]+'.json'), 'PRIVATE-INVENTED-NOT-DECODED')]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    for name in report.VENDOR_FILES:
        path = source/'vendor'/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# invented vendor bytes')
    return dict(task_id=row_value['task_id'], solution_sha256=report.digest(code_path), status='pass' if passed else 'fail',
                passed=passed, reason='success' if passed else 'test_failure', execution_uid=65534,
                execution_uid_cleanup_verified=True, elapsed_seconds=.25, feedback='' if passed else 'Invented failure',
                test_run_valid=True, tests_expected=2, tests_run=2, is_reference=False,
                evaluator_commit=report.EVALUATOR_COMMIT, timeout_seconds=60, hard_timeout_seconds=90,
                task_sha256=report.digest(source/'private'/(row_value['task_id'].split('/')[1]+'.json')),
                worker_sha256=report.digest(source/'worker.py'), vendor_sha256={n: report.digest(source/'vendor'/n) for n in report.VENDOR_FILES})


def interaction_fixture(parent, arm='B', rounds=2, recovery=False):
    original, fresh = Path(parent)/'original', Path(parent)/'continuation'
    original.mkdir(exist_ok=True); fresh.mkdir(exist_ok=True)
    evidence = report.Evidence(original, fresh)
    value = row('BigCodeBench/131' if recovery else 'BigCodeBench/900001', arm, 'misleading success', True)
    prefix = 'task-'+value['task_id'].split('/')[1]+'-'+arm
    prompts = dict(baseline='Invented baseline.', warning='Invented warning.', action='Invented common action.', format_error='Invented format error.')
    task = {'instruct_prompt': 'Invented public prompt.'}
    messages = [{'role': 'system', 'content': prompts['baseline']+('\n\n'+prompts['warning'] if arm == 'B' else '')}, {'role': 'user', 'content': task['instruct_prompt']}]
    code_path = original/(prefix+'-call-1.candidate.py')
    code_path.write_text('invented = 1\n')
    grade = grade_fixture(evidence, value, code_path)
    value.update(calls=rounds, candidate_count=1, final_code_present=True, final_candidate_path=code_path.name,
                 final_code_syntactically_valid=True, final_grade_reason='test_failure', passed=False,
                 first_actual_passed=False, first_report_differs=True, first_verdict_differs=True,
                 stop_reason='finish' if rounds < 4 else 'four_call_limit')
    for r in range(1, rounds+1):
        cid = prefix+'-call-'+str(r)
        action_name = 'submit' if r == 1 else 'finish' if rounds < 4 else 'rerun'
        text = 'invented = 1\n' if r == 1 else json.dumps({'action': action_name})
        action = dict(round=r, call_id=cid, model_path='calls/'+cid+'/result.json', action_path=cid+'.action.json',
                      action=action_name, call_consumed=True, output_status='ok')
        saved_action = {**action, **({'code': 'invented = 1\n'} if r == 1 else {})}
        save(original/action['action_path'], saved_action)
        save(original/action['model_path'], dict(call_id=cid, text=text, output_status='ok', cost_nano_usd=123, usage={'input': 10}))
        save(original/'calls'/cid/'charge.json', dict(cost_nano_usd=123, usage={'input': 10}))
        save(original/'calls'/cid/'response.json', dict(status='completed', output=[dict(type='message', role='assistant', status='completed', content=[dict(type='output_text', text=text)])]))
        save(original/'calls'/cid/'request.json', {'body': {'input': copy.deepcopy(messages)}})
        value['actions'].append(action)
        if action_name == 'finish':
            break
        if action_name == 'rerun':
            value['explicit_reruns'] += 1
        kinds = ['candidate' if r == 1 else 'rerun'] + (['automatic_verification'] if r == 1 and arm == 'C' else [])
        for kind in kinds:
            index = len(value['evaluations'])+1
            label = f'{prefix}-eval-{index}-{kind}'
            e = dict(index=index, kind=kind, round=r, candidate_path=code_path.name, grade_path=label+'.grade.json', report_path=label+'.report.json', status='fail', elapsed_seconds=.25)
            value['evaluations'].append(e)
            save(original/e['grade_path'], grade); save(original/e['report_path'], report.sanitized(grade))
            save(original/(label+'.command.json'), {'exitCode': 0})
        if r == 1:
            value['first_actual_grade_path'] = value['evaluations'][0]['grade_path']
            value['first_treatment_report_path'] = prefix+'-first-treatment.report.json'
            save(original/value['first_treatment_report_path'], {'status': 'pass', 'feedback': ''})
        shown = [{'status': 'pass', 'feedback': ''}] if r == 1 else [report.sanitized(grade)]
        if r == 1 and arm == 'C':
            shown.append(report.sanitized(grade)); value['automatic_verifications'] = 1
        content = json.dumps({'reports': shown}, separators=(',', ':'))+'\n'+prompts['action']
        feedback = cid+'.feedback.json'
        save(original/feedback, {'reports': shown, 'content': content, 'delivered_to_model': r < 4})
        value['feedback_paths'].append(feedback)
        if r < 4:
            messages.append({'role': 'assistant', 'content': text})
            if r == 1:
                messages.append({'role': 'system', 'content': prompts['action']})
            messages.append({'role': 'user', 'content': content})
    index = len(value['evaluations'])+1
    label = f'{prefix}-eval-{index}-final'
    final = dict(index=index, kind='final', round=rounds, candidate_path=code_path.name,
                 grade_path=label+'.grade.json', report_path=label+'.report.json', status='fail', elapsed_seconds=.25)
    value['evaluations'].append(final)
    save(original/(label+'.command.json'), {'exitCode': 0, 'stdout': json.dumps({'status': 'fail', 'reason': 'test_failure'})})
    if not recovery:
        save(original/final['grade_path'], grade); save(original/final['report_path'], report.sanitized(grade))
        value['final_grade_path'] = final['grade_path']
    else:
        final.update(status='intent', elapsed_seconds=None)
        value.update(observation='missing', completion='incomplete', passed=None, final_grade_reason=None,
                     final_code_syntactically_valid=None, stop_reason='operational_hold')
    value['evaluator_count'] = len(value['evaluations'])
    value['evaluator_seconds'] = sum(e['elapsed_seconds'] or 0 for e in value['evaluations'])
    return evidence, value, prompts, task, grade


def recovered_fixture(parent, passed=True):
    evidence, old, prompts, task, g = interaction_fixture(parent, recovery=True)
    value = copy.deepcopy(old)
    policy = 'Single fresh final grade determines amended outcome regardless of prior command summary; no new model call'
    value.update(observation='observed', completion='complete', passed=passed, final_grade_reason='success' if passed else 'test_failure',
                 final_code_syntactically_valid=True, stop_reason='finish', final_grade_path=report.RECOVERY_LABEL+'.grade.json',
                 evaluator_count=3, evaluator_seconds=.5, recovery_original_stop_reason='operational_hold', recovery_policy=policy,
                 recovery_prior_command_status='fail', recovery_disagrees_with_command=passed)
    e = dict(index=3, kind='final_recovery', round=2, candidate_path=old['final_candidate_path'],
             grade_path=value['final_grade_path'], report_path=report.RECOVERY_LABEL+'.report.json', status='pass' if passed else 'fail', elapsed_seconds=.25)
    value['evaluations'].append(e)
    g.update(passed=passed, status=e['status'], reason=value['final_grade_reason'], feedback='' if passed else 'Invented failure')
    save(evidence.continuation/e['grade_path'], g); save(evidence.continuation/e['report_path'], report.sanitized(g))
    save(evidence.continuation/(report.RECOVERY_LABEL+'.command.json'), {'exitCode': 0})
    save(evidence.continuation/(report.RECOVERY_LABEL+'.retrieval.json'), {'method': 'SDK readFileToBuffer', 'path': '/opt/idea19/'+report.RECOVERY_LABEL+'.result.json', 'bytes': 100, 'no_grader_reexecution': True})
    provenance = dict(source_task=old['task_id'], arm='B', candidate_path=old['final_candidate_path'],
                      candidate_sha256=report.digest(evidence.original/old['final_candidate_path']),
                      original_final_command_sha256=report.digest(evidence.original/'task-131-B-eval-2-final.command.json'),
                      finish_action_sha256=report.digest(evidence.original/'task-131-B-call-2.action.json'),
                      old_ambiguous_grade_intent_retained=True, policy=policy)
    return evidence, old, value, provenance, prompts, task


def financial_fixture(cost=1200000, unknown=False):
    cid = 'task-900001-A-call-1'
    call = dict(call_id=cid, task_id='BigCodeBench/900001', arm='A', settled_nano_usd=0 if unknown else cost,
                pending_nano_usd=report.RESERVE if unknown else 0, usage=None if unknown else {'input': 5})
    account = dict(calls=[call], reserved_attempts=1, settled_nano_usd=call['settled_nano_usd'], pending_nano_usd=call['pending_nano_usd'])
    last = report.snapshot(1, account['settled_nano_usd'], account['pending_nano_usd'], max(report.INITIAL_FORECAST, cost*2) if not unknown else report.INITIAL_FORECAST,
                           max(report.INITIAL_LARGEST, cost) if not unknown else report.INITIAL_LARGEST)
    ev = [dict(sequence=1, kind='claim', **report.snapshot()),
          dict(sequence=2, kind='model_intent', call_id=cid, task_id=call['task_id'], arm='A', **report.snapshot(1, 0, report.RESERVE)),
          dict(sequence=3, kind='model_hold' if unknown else 'model_settled', call_id=cid, **last),
          dict(sequence=4, kind='hold' if unknown else 'collection_complete', **last)]
    return ev, account, {report.key(call)}


class PartitionTests(unittest.TestCase):
    def test_only_missing_can_be_filled(self):
        old, todo = cohort(); new = copy.deepcopy(old)
        for r in new[576:]:
            r.update(observation='observed', completion='complete', passed=False)
        result = report.partition_rows(old, new, todo)
        self.assertEqual((len(result[2]), len(result[3])), (576, 143))
        new[0]['passed'] = True
        with self.assertRaisesRegex(ValueError, 'original observed outcome replaced'):
            report.partition_rows(old, new, todo)

    def test_duplicate_or_changed_assignment_rejected(self):
        old, todo = cohort(); new = copy.deepcopy(old); new[-1] = new[-2]
        with self.assertRaisesRegex(ValueError, 'duplicate or replaced'):
            report.partition_rows(old, new, todo)

    def test_new_rows_cannot_hide_provenance_schema_changes(self):
        old, todo = cohort(); new = copy.deepcopy(old); new[-1]['arbitrary'] = 1
        with self.assertRaisesRegex(ValueError, 'original schema'):
            report.partition_rows(old, new, todo)


class EvidenceTests(unittest.TestCase):
    def test_private_bytes_only_hash_and_paths_contained(self):
        with tempfile.TemporaryDirectory() as parent:
            e = report.Evidence(Path(parent)/'old', Path(parent)/'new')
            p = e.original/'private'/'x.json'; p.parent.mkdir(parents=True); p.write_text('not even valid JSON')
            self.assertEqual(e.pin(p), report.digest(p))
            with self.assertRaisesRegex(ValueError, 'non-private'):
                e.read(e.original, 'private/x.json')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                e.path(e.original, '../new/x.json')

    def test_candidate_tampering_fails_without_code_execution(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, _, _, _ = interaction_fixture(parent)
            (e.original/r['final_candidate_path']).write_text('changed invented bytes')
            with self.assertRaisesRegex(ValueError, 'candidate hash'):
                report.audit_row(r, e.original, e)

    def test_grade_source_and_private_package_pins(self):
        for field in ('task_sha256', 'worker_sha256', 'vendor_sha256'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as parent:
                e, r, _, _, g = interaction_fixture(parent)
                g[field] = {} if field == 'vendor_sha256' else '0'*64
                save(e.original/r['final_grade_path'], g)
                with self.assertRaisesRegex(ValueError, 'hash binding'):
                    report.audit_row(r, e.original, e)

    def test_model_action_binding(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, _, _, _ = interaction_fixture(parent)
            path = e.original/r['actions'][1]['model_path']
            m = json.loads(path.read_text()); m['text'] = '{"action":"rerun"}'; save(path, m)
            with self.assertRaisesRegex(ValueError, 'model/action'):
                report.audit_row(r, e.original, e)

    def test_recovery_can_disagree_without_replacing_old_intent(self):
        with tempfile.TemporaryDirectory() as parent:
            e, old, r, p, prompts, task = recovered_fixture(parent, True)
            report.validate_recovery(old, r, p, e)
            counts = report.audit_row(r, e.original, e, recovery=True)
            report.audit_messages(r, e.original, e, task, prompts)
            self.assertEqual(counts['ambiguous_evaluation_intents'], 1)
            self.assertEqual(counts['completed_evaluations'], 2)
            self.assertEqual(r['evaluations'][1], old['evaluations'][1])
            self.assertTrue(r['recovery_disagrees_with_command'])

    def test_recovery_prior_outcome_or_call_mutation_rejected(self):
        for field, changed in [('calls', 3), ('first_actual_passed', True), ('final_candidate_path', 'replacement.py')]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as parent:
                e, old, r, p, _, _ = recovered_fixture(parent)
                r[field] = changed
                with self.assertRaisesRegex(ValueError, 'changed prior evidence'):
                    report.validate_recovery(old, r, p, e)

    def test_recovery_command_disagreement_must_be_reported(self):
        with tempfile.TemporaryDirectory() as parent:
            e, old, r, p, _, _ = recovered_fixture(parent)
            r['recovery_disagrees_with_command'] = False
            with self.assertRaisesRegex(ValueError, 'discrepancy'):
                report.validate_recovery(old, r, p, e)


class MessageTests(unittest.TestCase):
    def test_warning_system_action_priority_firstonly_and_round4(self):
        for arm in ('B', 'C'):
            with self.subTest(arm=arm), tempfile.TemporaryDirectory() as parent:
                e, r, prompts, task, _ = interaction_fixture(parent, arm, rounds=4)
                report.audit_row(r, e.original, e)
                report.audit_messages(r, e.original, e, task, prompts)
                feedback = json.loads((e.original/r['feedback_paths'][-1]).read_text())
                self.assertFalse(feedback['delivered_to_model'])

    def test_missing_system_priority_or_prompt_warning_rejected(self):
        for mode in ('warning', 'system'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as parent:
                e, r, prompts, task, _ = interaction_fixture(parent)
                cid = r['actions'][0 if mode == 'warning' else 1]['call_id']
                path = e.original/'calls'/cid/'request.json'
                request = json.loads(path.read_text())
                if mode == 'warning': request['body']['input'][0]['content'] = prompts['baseline']
                else: request['body']['input'][-2]['role'] = 'user'
                save(path, request)
                with self.assertRaisesRegex(ValueError, 'request history'):
                    report.audit_messages(r, e.original, e, task, prompts)

    def test_automatic_verification_not_silently_omitted(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, prompts, task, _ = interaction_fixture(parent, 'C')
            path = e.original/r['feedback_paths'][0]
            f = json.loads(path.read_text()); f['reports'].pop(); save(path, f)
            with self.assertRaisesRegex(ValueError, 'feedback content'):
                report.audit_messages(r, e.original, e, task, prompts)

    def test_round4_must_not_claim_delivery(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, prompts, task, _ = interaction_fixture(parent, rounds=4)
            path = e.original/r['feedback_paths'][-1]
            f = json.loads(path.read_text()); f['delivered_to_model'] = True; save(path, f)
            with self.assertRaisesRegex(ValueError, 'feedback content/delivery'):
                report.audit_messages(r, e.original, e, task, prompts)


class FinancialTests(unittest.TestCase):
    def test_precise_carry_and_projection(self):
        self.assertEqual(report.CARRY, 34560911115)
        self.assertEqual(report.snapshot()['whole_completion_projection_nano_usd'], 38566028025)
        self.assertEqual(report.snapshot()['remaining_call_capacity'], 1233)
        self.assertEqual(report.snapshot(calls=572)['remaining_call_capacity'], 661)
        self.assertEqual(report.MAX_CALLS, 572)
        ev, a, allowed = financial_fixture()
        result = report.financial_history(ev, a, allowed, set())
        self.assertEqual(result['combined_committed_nano_usd'], report.CARRY+1200000)

    def test_unknown_charge_remains_reserved(self):
        ev, a, allowed = financial_fixture(unknown=True)
        result = report.financial_history(ev, a, allowed, set())
        self.assertEqual(result['terminal']['pending_nano_usd'], 50000000)
        self.assertTrue(result['stopped'])
        ev[-1]['kind'] = 'collection_complete'
        with self.assertRaisesRegex(ValueError, 'unresolved complete'):
            report.financial_history(ev, a, allowed, set())

    def test_duplicate_original_calls_and_wrong_arms_rejected(self):
        ev, a, allowed = financial_fixture()
        with self.assertRaisesRegex(ValueError, 'duplicate original/new'):
            report.financial_history(ev, a, allowed, {a['calls'][0]['call_id']})
        with self.assertRaisesRegex(ValueError, 'outside 143'):
            report.financial_history(ev, a, {report.RECOVERY}, set())

    def test_carry_forecast_pending_and_sequence_tampering(self):
        for field in ('retained_carry_nano_usd', 'forecast_per_call_nano_usd', 'pending_nano_usd', 'remaining_call_capacity', 'sequence'):
            with self.subTest(field=field):
                ev, a, allowed = financial_fixture(); ev[1][field] += 1
                with self.assertRaises(ValueError):
                    report.financial_history(ev, a, allowed, set())

    def test_largest_call_increases_forecast_monotonically(self):
        ev, a, allowed = financial_fixture(2400000)
        result = report.financial_history(ev, a, allowed, set())
        self.assertEqual(result['terminal']['forecast_per_call_nano_usd'], 4800000)
        ev[2]['forecast_per_call_nano_usd'] = report.INITIAL_FORECAST
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            report.financial_history(ev, a, allowed, set())

    def test_duplicate_settlement_and_events_after_terminal(self):
        ev, a, allowed = financial_fixture(); ev.insert(3, copy.deepcopy(ev[2]))
        for i, e in enumerate(ev, 1): e['sequence'] = i
        with self.assertRaisesRegex(ValueError, 'unique intent'):
            report.financial_history(ev, a, allowed, set())
        ev, a, allowed = financial_fixture(); ev.append(dict(sequence=5, kind='noise'))
        with self.assertRaisesRegex(ValueError, 'envelope'):
            report.financial_history(ev, a, allowed, set())


def saved_call(root, cid, gen='gen_invented', cost=1000000):
    directory = root/'calls'/cid
    body = dict(model='openai/gpt-6-luna', input='Invented prompt', reasoning={'effort': 'medium'}, max_output_tokens=8192,
                providerOptions={'gateway': {'only': ['openai']}}, service_tier='default', tools=[], stream=False, store=False)
    body_hash = hashlib.sha256(json.dumps(body, separators=(',', ':')).encode()).hexdigest()
    save(directory/'request.json', dict(call_id=cid, body=body, request_sha256=body_hash, reserve_nano_usd=50000000))
    save(directory/'DISPATCH.json', dict(call_id=cid, model_request_attempts=1))
    response = dict(id=gen, model='openai/gpt-6-luna', status='incomplete', usage=dict(input_tokens=10, output_tokens=5, total_tokens=15,
                    input_tokens_details={'cached_tokens': 0}, output_tokens_details={'reasoning_tokens': 2}))
    receipt = {'data': dict(id=gen, total_cost=str(cost/1e9), is_byok=False, provider_name='openai', model='openai/gpt-6-luna', tokens_prompt=10, tokens_completion=5)}
    usage = dict(input=10, output=5, total=15, cached=0, reasoning=2, cache_write=None)
    save(directory/'response.json', response); save(directory/'response.http.json', dict(status=200, body=json.dumps(response)))
    save(directory/'receipt.json', receipt); save(directory/'receipt-0.http.json', dict(status=200, body=json.dumps(receipt)))
    save(directory/'charge.json', dict(cost_nano_usd=cost, usage=usage))
    return directory


def empty_main_snapshot():
    return dict(calls=0, settled_nano_usd=0, pending_nano_usd=0, pilot_carry_nano_usd=report.PILOT,
                infrastructure_reserve_nano_usd=report.OLD_INFRA, forecast_per_call_nano_usd=2188000,
                largest_observed_main_call_nano_usd=0, remaining_call_capacity=2880,
                whole_completion_projection_nano_usd=34392719770, next_physical_reserve_total_nano_usd=28141279770)


class BillingAdapterTests(unittest.TestCase):
    def setup_roots(self, parent):
        old, new = Path(parent)/'old', Path(parent)/'new'; old.mkdir(); new.mkdir()
        for name in ('audit-costs.mjs', 'billing-scoped.mjs'):
            shutil.copyfile(report.ORIGINAL/name, old/name)
        events(old/'EVENTS.jsonl', [dict(sequence=1, kind='claim', **empty_main_snapshot()), dict(sequence=2, kind='hold', **empty_main_snapshot())])
        cid = 'task-900001-A-call-1'
        saved_call(new, cid)
        events(new/'EVENTS.jsonl', [dict(sequence=1, kind='model_intent', call_id=cid, task_id='BigCodeBench/900001', arm='A')])
        return old, new, cid

    def test_frozen_receipt_reconciliation_and_unknown_latency_cache(self):
        with tempfile.TemporaryDirectory() as parent:
            old, new, _ = self.setup_roots(parent)
            inspected = report.inspect_costs(old, new)
            self.assertEqual(inspected['fresh']['totals']['settled_nano_usd'], 1000000)
            arm = inspected['fresh']['totals']['by_arm']['A']
            self.assertEqual(arm['output_tokens'], 5)
            self.assertEqual(arm['reasoning_tokens'], 2)
            self.assertIsNone(arm['provider_latency_ms'])
            self.assertIsNone(arm['cache_write_tokens'])
            self.assertEqual(arm['latency_unknown_calls'], 1)

    def test_frozen_receipt_reconciliation_rejects_derived_cost_mutation(self):
        with tempfile.TemporaryDirectory() as parent:
            old, new, cid = self.setup_roots(parent)
            path = new/'calls'/cid/'charge.json'; charge = json.loads(path.read_text()); charge['cost_nano_usd'] += 1; save(path, charge)
            with self.assertRaises(subprocess.CalledProcessError):
                report.inspect_costs(old, new)

    def test_cross_phase_duplicate_physical_charge_rejected(self):
        with tempfile.TemporaryDirectory() as parent:
            old, new, _ = self.setup_roots(parent)
            cid = 'task-900002-B-call-1'; saved_call(old, cid)
            events(old/'EVENTS.jsonl', [dict(kind='model_intent', call_id=cid, task_id='BigCodeBench/900002', arm='B')])
            with self.assertRaises(subprocess.CalledProcessError):
                report.inspect_costs(old, new)

    def test_combined_accounts_keep_known_subtotals_and_unknown_totals(self):
        with tempfile.TemporaryDirectory() as parent:
            old, new, _ = self.setup_roots(parent)
            source = report.inspect_costs(old, new)['fresh']['totals']
            left, right = copy.deepcopy(source), copy.deepcopy(source)
            right['calls'][0]['call_id'] = 'task-900002-A-call-1'
            for account in (left, right):
                account['by_arm']['B'] = copy.deepcopy(account['by_arm']['A'])
                account['by_arm']['C'] = copy.deepcopy(account['by_arm']['A'])
            right['by_arm']['A']['input_tokens'] = None
            right['by_arm']['A']['usage_unknown_calls'] = 1
            total = report.combine_accounts(left, right)
            self.assertEqual(total['settled_nano_usd'], 2000000)
            self.assertEqual(total['by_arm']['A']['known_input_tokens'], 20)
            self.assertIsNone(total['by_arm']['A']['input_tokens'])
            self.assertIsNone(total['by_arm']['A']['provider_latency_ms'])


def resource_fixture(parent):
    old, new = Path(parent)/'old', Path(parent)/'new'; old.mkdir(); new.mkdir()
    evidence = report.Evidence(old, new)
    save(old/'APPROVED-CLEANUP-RESULT-v1.json', dict(name='econ-tool-recovery-main-v1-20261027-10', closure_verified=True,
                                                  deleted=True, verification={'empty': True}, usage=None))
    closures = []
    for n in (10, 11, 12):
        name = f'econ-tool-recovery-completion-v1-20261029-{n}'
        c = dict(name=name, block=n, infrastructure_reserve_usd=2, creation_dispatched=True, creation_confirmed=True,
                 stopped=True, deleted=True, verification={'empty': True}, billable_egress_bytes=100, observed_resource_cost_upper_usd=.5)
        save(new/f'block-{n}-RESOURCE-CLOSURE.json', c)
        save(new/f'block-{n}-DISPATCH.json', dict(name=name, timeout_ms=14400000, infrastructure_reserve_usd=2))
        save(new/f'block-{n}-HOST.json', dict(name=name, vcpus=2, memory=4096))
        closures.append(c)
    return evidence, {'resource_closures': closures}


def pre_dispatch_fixture(parent):
    old, new = Path(parent)/'old', Path(parent)/'new'; old.mkdir(); new.mkdir()
    evidence = report.Evidence(old, new)
    value = row()
    cid = 'task-900001-A-call-1'
    value.update(completion='incomplete', calls=1, stop_reason='operational_hold', actions=[dict(
        round=1, call_id=cid, model_path='calls/'+cid+'/result.json', action_path=cid+'.action.json', action='pending')])
    artifact = dict(call_id=cid, request_dispatched=False, financial_reserved=False, stage='pre_reserve', error_name='Error')
    save(new/(cid+'.predispatch.json'), artifact)
    ev = [dict(sequence=1, kind='claim', **report.snapshot()),
          dict(sequence=2, kind='model_pre_dispatch_hold', call_id=cid, task_id=value['task_id'], arm='A',
               block=value['block'], condition=value['condition'], artifact_path=cid+'.predispatch.json', **report.snapshot()),
          dict(sequence=3, kind='hold', **report.snapshot())]
    account = dict(calls=[], reserved_attempts=0, settled_nano_usd=0, pending_nano_usd=0)
    return evidence, value, ev, account, cid


class PreDispatchHoldTests(unittest.TestCase):
    def validate(self, evidence, value, ev, account, allowed=None, original=None, complete=False):
        return report.audit_pre_dispatch_holds(ev, [value], allowed if allowed is not None else {report.key(value)},
                                               original or set(), account, evidence, complete)

    def test_proven_hold_keeps_attempt_missing_and_excludes_only_unreserved(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, ev, account, cid = pre_dispatch_fixture(parent)
            checked = report.audit_row(r, e.continuation, e)
            report.audit_messages(r, e.continuation, e, {'instruct_prompt': 'Invented prompt'},
                                  dict(baseline='Invented baseline', warning='warning', action='action', format_error='format'))
            pre = self.validate(e, r, ev, account)
            self.assertEqual(checked['action_ids'], {cid})
            self.assertEqual(pre, {cid})
            attempts = report.reconcile_call_attempts([r], account, pre)
            self.assertEqual((attempts['attempted_calls'], attempts['reserved_calls'], attempts['pre_dispatch_unreserved']), (1, 0, 1))
            self.assertEqual((attempts['physical_post_intents'], attempts['unresolved_charge_calls'], attempts['pending_api_nano_usd']), (0, 0, 0))
            replay = report.financial_history(ev, account, {report.key(r)}, set(), pre)
            self.assertEqual(replay['terminal'], report.snapshot())
            self.assertTrue(replay['stopped'])
            self.assertIsNone(r['passed'])
            # Original offline accounting adapter ignores no financial intent;
            # it does not invent a pending charge for this interaction attempt.
            for name in ('audit-costs.mjs', 'billing-scoped.mjs'):
                shutil.copyfile(report.ORIGINAL/name, e.original/name)
            events(e.original/'EVENTS.jsonl', [dict(sequence=1, kind='claim', **empty_main_snapshot()), dict(sequence=2, kind='hold', **empty_main_snapshot())])
            events(e.continuation/'EVENTS.jsonl', ev)
            inspected = report.inspect_costs(e.original, e.continuation)['fresh']['totals']
            self.assertEqual(inspected['reserved_attempts'], 0)
            self.assertEqual(inspected['pending_nano_usd'], 0)

    def test_missing_proof_does_not_exclude_pending_action(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, ev, account, cid = pre_dispatch_fixture(parent)
            (e.continuation/(cid+'.predispatch.json')).unlink()
            with self.assertRaisesRegex(ValueError, 'artifact'):
                self.validate(e, r, ev, account)
            with self.assertRaisesRegex(ValueError, 'accounting call'):
                report.reconcile_call_attempts([r], account, set())

    def test_orphan_artifact_and_wrong_event_binding_rejected(self):
        for mutation in ('no_event', 'wrong_path', 'wrong_arm', 'wrong_condition', 'wrong_block', 'duplicate_event'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                e, r, ev, account, cid = pre_dispatch_fixture(parent)
                if mutation == 'no_event': ev.pop(1)
                elif mutation == 'wrong_path': ev[1]['artifact_path'] = '../old/'+cid+'.predispatch.json'
                elif mutation == 'wrong_arm': ev[1]['arm'] = 'B'
                elif mutation == 'wrong_condition': ev[1]['condition'] = 'misleading success'
                elif mutation == 'wrong_block': ev[1]['block'] = 11
                else: ev.insert(2, copy.deepcopy(ev[1]))
                with self.assertRaises(ValueError):
                    self.validate(e, r, ev, account)

    def test_false_artifact_claims_rejected(self):
        for field, bad in [('call_id', 'task-900002-A-call-1'), ('request_dispatched', True), ('financial_reserved', True),
                           ('stage', 'client_transport'), ('error_name', None)]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as parent:
                e, r, ev, account, cid = pre_dispatch_fixture(parent)
                path = e.continuation/(cid+'.predispatch.json'); artifact = json.loads(path.read_text()); artifact[field] = bad; save(path, artifact)
                with self.assertRaisesRegex(ValueError, 'artifact binding'):
                    self.validate(e, r, ev, account)

    def test_existing_client_directory_or_receipt_cannot_be_reclassified(self):
        for location, filename in [('new', None), ('new', 'receipt.json'), ('new', 'HOLD.json'), ('old', 'charge.json')]:
            with self.subTest(location=location, filename=filename), tempfile.TemporaryDirectory() as parent:
                e, r, ev, account, cid = pre_dispatch_fixture(parent)
                directory = (e.continuation if location == 'new' else e.original)/'calls'/cid
                directory.mkdir(parents=True)
                if filename: save(directory/filename, {'invented': True})
                with self.assertRaisesRegex(ValueError, 'client call directory/receipt'):
                    self.validate(e, r, ev, account)

    def test_financial_intent_reserved_record_original_id_and_nonuntouched_rejected(self):
        for conflict in ('intent', 'record', 'original', 'nonuntouched'):
            with self.subTest(conflict=conflict), tempfile.TemporaryDirectory() as parent:
                e, r, ev, account, cid = pre_dispatch_fixture(parent)
                if conflict == 'intent': ev.insert(1, dict(kind='model_intent', call_id=cid))
                if conflict == 'record': account['calls'] = [dict(call_id=cid)]
                with self.assertRaisesRegex(ValueError, 'conflicts|untouched'):
                    self.validate(e, r, ev, account, allowed=set() if conflict == 'nonuntouched' else None,
                                  original={cid} if conflict == 'original' else None)

    def test_terminal_missing_pending_action_and_complete_marker_enforced(self):
        for mutation in ('passed', 'complete', 'not_pending', 'after_pending', 'wrong_round', 'marker'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                e, r, ev, account, cid = pre_dispatch_fixture(parent)
                if mutation == 'passed': r['passed'] = False
                elif mutation == 'complete': r['completion'] = 'complete'
                elif mutation == 'not_pending': r['actions'][-1]['action'] = 'finish'
                elif mutation == 'after_pending': r['actions'].append(dict(action='pending', call_id='task-900001-A-call-2', round=2))
                elif mutation == 'wrong_round': r['actions'][-1]['round'] = 2
                with self.assertRaises(ValueError):
                    self.validate(e, r, ev, account, complete=mutation == 'marker')

    def test_financial_snapshot_must_stay_unchanged_and_no_later_dispatch(self):
        for mutation in ('calls', 'pending_nano_usd', 'remaining_call_capacity', 'unvalidated', 'later_intent'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as parent:
                e, r, ev, account, cid = pre_dispatch_fixture(parent)
                pre = self.validate(e, r, ev, account)
                if mutation == 'unvalidated': pre = set()
                elif mutation == 'later_intent':
                    ev.insert(2, dict(sequence=3, kind='model_intent', call_id='task-900002-A-call-1'))
                    ev[-1]['sequence'] = 4
                else: ev[1][mutation] += 1
                with self.assertRaises(ValueError):
                    report.financial_history(ev, account, {report.key(r)}, set(), pre)

    def test_actual_client_unknown_charge_remains_reserved_without_exception(self):
        with tempfile.TemporaryDirectory() as parent:
            e, r, _, _, cid = pre_dispatch_fixture(parent)
            (e.continuation/(cid+'.predispatch.json')).unlink()
            ev, account, allowed = financial_fixture(unknown=True)
            account['calls'][0]['dispatched'] = True
            pre = self.validate(e, r, ev, account)
            self.assertEqual(pre, set())
            attempts = report.reconcile_call_attempts([r], account, pre)
            self.assertEqual((attempts['attempted_calls'], attempts['reserved_calls'], attempts['physical_post_intents'], attempts['unresolved_charge_calls']), (1, 1, 1, 1))
            self.assertEqual(attempts['pending_api_nano_usd'], report.RESERVE)
            result = report.financial_history(ev, account, allowed, set(), pre)
            self.assertEqual(result['terminal']['pending_nano_usd'], report.RESERVE)


class ResourceAndRenderTests(unittest.TestCase):
    def test_new_blocks_old_unknown_usage_and_no_reserve_release(self):
        with tempfile.TemporaryDirectory() as parent:
            e, data = resource_fixture(parent)
            result = report.resource_audit(data, e, True)
            self.assertEqual(result['verified_closed'], 3)
            self.assertIsNone(result['original_host10_usage'])
            self.assertEqual(report.CARRY, 34560911115)

    def test_false_closure_and_unknown_usage_prevent_completion(self):
        for field, value in [('deleted', False), ('billable_egress_bytes', None), ('observed_resource_cost_upper_usd', 2.1)]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as parent:
                e, data = resource_fixture(parent); data['resource_closures'][0][field] = value
                save(e.continuation/'block-10-RESOURCE-CLOSURE.json', data['resource_closures'][0])
                with self.assertRaisesRegex(ValueError, 'closure'):
                    report.resource_audit(data, e, True)
                partial = report.resource_audit(data, e, False)
                self.assertTrue(partial['unresolved_blocks'] or partial['unknown_usage_blocks'])

    def test_null_verification_is_unresolved_in_held_report_not_a_crash(self):
        with tempfile.TemporaryDirectory() as parent:
            e, data = resource_fixture(parent)
            data['resource_closures'][0]['verification'] = None
            save(e.continuation/'block-10-RESOURCE-CLOSURE.json', data['resource_closures'][0])
            result = report.resource_audit(data, e, False)
            self.assertEqual(result['unresolved_blocks'], [10])
            self.assertEqual(result['verified_closed'], 2)
            with self.assertRaisesRegex(ValueError, 'complete continuation resource'):
                report.resource_audit(data, e, True)

    def test_render_labels_finances_all15_and_ambiguous_intent(self):
        analysis, original_report = report.load_original_functions(report.ORIGINAL)
        rows = [row('BigCodeBench/'+str(920000+i), a, analysis.CONDITIONS[i//60], True) for i in range(240) for a in 'ABC']
        summary = analysis.summarize(rows, 240)
        for i, stratum in enumerate(summary['strata'].values()):
            for j, contrast in enumerate(stratum['contrasts']):
                contrast['bootstrap95'] = dict(lower=0, upper=0, draws=20000, seed=analysis.SEED+i*10+j)
        summary.update(collection_status='complete', infrastructure_actual_usd=None,
                       secondary={a: original_report.secondary_metrics([r for r in rows if r['arm'] == a], {}) for a in 'ABC'},
                       descriptive_condition_exposure={}, financial_audit=dict(terminal=report.snapshot(), combined_committed_nano_usd=report.CARRY,
                       actual_plus_pending_cap_satisfied=True, remaining_forecast_cap_satisfied=True),
                       resource_audit=dict(verified_closed=3, recorded=3, unresolved_blocks=[], unknown_usage_blocks=[]),
                       evaluation_audit=dict(completed_evaluations=2, ambiguous_evaluation_intents=1),
                       recovery_status=dict(observation='observed', disagrees_with_command=True),
                       call_attempt_audit={'by_arm': {'A': dict(attempted_calls=1, reserved_calls=0, pre_dispatch_unreserved=1,
                           physical_post_intents=0, known_undispatched_reserved=0, uncertain_dispatch=0, unresolved_charge_calls=0, pending_api_nano_usd=0)}})
        text = report.render_amended(summary, original_report)
        self.assertIn('post-HOLD amended completion', text)
        self.assertIn('primary historical report', text)
        self.assertIn('not a pristine preregistered complete run', text)
        self.assertIn('new infrastructure reserve: $6', text)
        self.assertIn('$38.566028025', text)
        self.assertIn('ambiguous intents: 1', text)
        self.assertIn('disagreement: True', text)
        self.assertNotIn('12 planned', text)
        self.assertEqual(text.count('20000 / '), 15)
        self.assertIn('Attempted calls', text)
        self.assertIn('Proven pre-dispatch / unreserved', text)
        self.assertIn('| A | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0.000000000 |', text)


class StatisticsAndOneUseTests(unittest.TestCase):
    def test_exact_all15_original_default_seed_and_draws(self):
        analysis, _ = report.load_original_functions(report.ORIGINAL)
        rows = [row('BigCodeBench/'+str(910000+i), a, analysis.CONDITIONS[i//2], True) for i in range(8) for a in 'ABC']
        for i, r in enumerate(rows): r['passed'] = i % 5 == 0
        summary = analysis.summarize(rows, 8, bootstrap=True)
        comparisons = [c for s in summary['strata'].values() for c in s['contrasts']]
        self.assertEqual(len(comparisons), 15)
        self.assertEqual([c['bootstrap95']['seed'] for c in comparisons], [2026102807+i*10+j for i in range(5) for j in range(3)])
        self.assertTrue(all(c['bootstrap95']['draws'] == 20000 for c in comparisons))
        self.assertNotIn('pilot_gate', summary)

    def test_claim_is_exclusive_failure_consumes_only_new_claim(self):
        with tempfile.TemporaryDirectory() as parent:
            old, fresh = Path(parent)/'old', Path(parent)/'new'; old.mkdir(); fresh.mkdir()
            (old/'REPORT.md').write_text('Historical report bytes')
            save(fresh/'HOLD.json', {})
            with patch.object(report, '_report', side_effect=ValueError('invented failure')):
                with self.assertRaisesRegex(ValueError, 'invented failure'):
                    report.audit_and_report(fresh, old)
            self.assertTrue((fresh/'REPORT-HOLD.json').exists())
            with self.assertRaisesRegex(ValueError, 'overwrite/replay'):
                report.audit_and_report(fresh, old)
            self.assertEqual((old/'REPORT.md').read_text(), 'Historical report bytes')

    def test_no_terminal_no_claim(self):
        with tempfile.TemporaryDirectory() as parent:
            old, fresh = Path(parent)/'old', Path(parent)/'new'; old.mkdir(); fresh.mkdir()
            with self.assertRaisesRegex(ValueError, 'terminal collector'):
                report.audit_and_report(fresh, old)
            self.assertFalse((fresh/'REPORT-CLAIM.json').exists())


if __name__ == '__main__':
    unittest.main()
