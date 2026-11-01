"""Invented only: three-phase integration plus adversarial evidence binding.
RELEASE is never rebuilt and CLAIM is never changed after mock collection.
"""
import copy
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import manifest_freeze_fixture as fixture
import report_completion as report


@contextmanager
def replace_json(path, value):
    """Adversarial mutation of temporary evidence; restore exact original bytes."""
    original = path.read_bytes()
    try:
        path.write_text(json.dumps(value))
        yield
    finally:
        path.write_bytes(original)


def read(path):
    return json.loads(path.read_text())


class CompletionIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = fixture.Fixture()
        cls.addClassCleanup(cls.f.close)
        cls.f.collect()
        cls.audit = cls.f.audit()
        cls.data = read(cls.f.new/'RESULTS.json')
        cls.previous = read(cls.f.previous/'RESULTS.json')
        cls.analysis = read(cls.f.new/'ANALYSIS.json')
        cls.events = [json.loads(line) for line in (cls.f.new/'EVENTS.jsonl').read_text().splitlines()]
        cls.amendment = read(cls.f.new/'AMENDMENT.json')
        cls.h = report.load_helpers(cls.f.previous, completion=True)
        cls.saved = next(r for r in cls.data['results'] if report.key(r)==report.SAVED_KEY)
        cls.late = dict(generation_id=cls.amendment['saved_response_generation_id'],
                        charge=read(cls.f.previous/'POSTHOLD-CHARGE-ADDENDUM-v1.json')['charge'])

    def evidence(self):
        return self.h.Evidence(self.f.old, self.f.new)

    def saved_check(self, events=None, row=None):
        return report.validate_saved_response(self.f.new, self.f.previous, row or self.saved,
                                             events if events is not None else self.events,
                                             self.amendment, self.late, self.evidence(), True)

    def test_complete720_preserves628_and_recovery(self):
        self.assertTrue(self.audit['accepted'])
        self.assertEqual(self.audit['observed_arms'],720)
        self.assertEqual(self.f.collection['new_calls'],183)
        preserved = [(a,b) for a,b in zip(self.previous['results'],self.data['results']) if a['observation']=='observed']
        self.assertEqual(len(preserved),628)
        self.assertTrue(all(a==b for a,b in preserved))
        old = read(self.f.old/'RESULTS.json')['results']
        self.assertEqual(sum(r['observation']=='observed' for r in old),576)
        recovery = next(r for r in self.data['results'] if report.key(r)==self.h.RECOVERY)
        self.assertEqual([e['kind'] for e in recovery['evaluations']], ['candidate','final','final_recovery'])
        self.assertEqual(recovery['evaluations'][1]['status'],'intent')
        self.assertEqual(self.audit['evaluation_audit']['ambiguous_evaluation_intents'],1)

    def test_prelaunch_release_claim_and_history_are_immutable(self):
        self.f.assert_immutable()
        generated = list(self.f.new.glob('*.candidate.py'))
        self.assertTrue(generated)
        release = read(self.f.new/'RELEASE.json')
        self.assertTrue(all(str(p) not in release['files'] for p in generated))
        self.assertTrue(all(str(p) in self.audit['files'] for p in generated))
        self.assertIn('transport.mjs',report.IMPLEMENTATION_FILES)
        self.assertNotIn('candidate.py',report.IMPLEMENTATION_FILES)

    def test_all15_original_intervals_and_seeds(self):
        self.assertEqual(len(self.analysis['strata']),5)
        for i,stratum in enumerate(self.analysis['strata'].values()):
            self.assertEqual(len(stratum['contrasts']),3)
            for j,c in enumerate(stratum['contrasts']):
                self.assertEqual(c['bootstrap95']['draws'],20000)
                self.assertEqual(c['bootstrap95']['seed'],2026102807+i*10+j)
                self.assertEqual(c['observed_pairs'],240 if i==0 else 60)

    def test_three_phase_finance_and_retained_capacity(self):
        a=self.audit
        self.assertEqual(a['historical_previous_accounting']['pending_nano_usd'],50000000)
        self.assertEqual(a['previous_known_accounting']['pending_nano_usd'],0)
        self.assertEqual(a['previous_known_accounting']['settled_nano_usd'],37691825)
        self.assertEqual(a['accounting']['reserved_attempts'],1647+137+183)
        self.assertEqual(a['accounting']['settled_nano_usd'],469631345+37691825+18300)
        self.assertEqual(a['financial_audit']['terminal']['remaining_call_capacity'],1096-183)
        self.assertEqual(a['financial_audit']['initial_combined_forecast_nano_usd'],42208706860)
        self.assertEqual(a['financial_audit']['terminal']['whole_completion_projection_nano_usd'],38648602940+18300+(1096-183)*3248270)
        self.assertEqual(self.analysis['historical_buffer_nano_usd'],50000000)
        self.assertIsNone(self.analysis['infrastructure_actual_usd'])
        self.assertTrue(all(a['accounting']['by_arm'][arm]['provider_latency_ms'] is None for arm in 'ABC'))

    def test_saved_response_is_consumed_once_without_new_post(self):
        self.assertTrue(self.saved_check())
        self.assertEqual(len([e for e in self.events if e['kind']=='saved_response_consumed']),1)
        self.assertEqual(self.saved['calls'],2)
        self.assertFalse((self.f.new/'calls'/report.SAVED_ID).exists())
        self.assertEqual(self.saved['actions'][0]['model_path'],report.SAVED_RESULT)
        self.assertEqual(sum(c['call_id']==report.SAVED_ID for c in self.audit['accounting']['calls']),1)

    def test_duplicate_saved_consumption_rejected(self):
        events=self.events+[next(e for e in self.events if e['kind']=='saved_response_consumed')]
        with self.assertRaisesRegex(ValueError,'more than once'):
            self.saved_check(events)

    def test_saved_post_or_financial_replay_rejected(self):
        directory=self.f.new/'calls'/report.SAVED_ID
        directory.mkdir()
        try:
            with self.assertRaisesRegex(ValueError,'POST/directory forbidden'):
                self.saved_check()
        finally:
            directory.rmdir()
        with self.assertRaisesRegex(ValueError,'financially dispatched again'):
            self.saved_check(self.events+[dict(kind='model_intent',call_id=report.SAVED_ID)])

    def test_reconstructed_model_identity_and_provenance_rejected(self):
        path=self.f.new/report.SAVED_RESULT
        for field,value in [('generation_id','other'),('response_id','other'),('model_request_attempts',2),('cost_nano_usd',0)]:
            with self.subTest(field=field),replace_json(path,{**read(path),field:value}):
                with self.assertRaisesRegex(ValueError,'reconstructed saved model'):
                    self.saved_check()
        path=self.f.new/'SAVED-RESPONSE-RECOVERY.json'
        with replace_json(path,{**read(path),'no_new_post':False}):
            with self.assertRaisesRegex(ValueError,'provenance binding'):
                self.saved_check()
        row=copy.deepcopy(self.saved);row['actions'][0]['model_path']='calls/'+report.SAVED_ID+'/result.json'
        with self.assertRaisesRegex(ValueError,'saved action result path'):
            self.saved_check(row=row)

    def test_saved_request_full_configuration_rejected(self):
        path=self.f.previous/'calls'/report.SAVED_ID/'request.json'
        changed=read(path);changed['body']['truncation']='auto'
        with replace_json(path,changed):
            with self.assertRaisesRegex(ValueError,'exact request configuration'):
                self.saved_check()

    def test_preserved_outcome_cannot_be_replaced(self):
        changed=copy.deepcopy(self.data['results']);changed[0]['passed']=True
        with self.assertRaisesRegex(ValueError,'preserved628 outcome changed'):
            report.partition_completion(self.previous['results'],changed,self.amendment['remaining'])
        changed=copy.deepcopy(self.amendment['remaining']);changed[0]['calls']=0
        with self.assertRaisesRegex(ValueError,'remaining original metadata'):
            report.partition_completion(self.previous['results'],self.data['results'],changed)

    def test_grade_private_worker_vendor_hashes_bound(self):
        grade=read(self.f.new/self.saved['final_grade_path'])
        candidate_hash=report.digest(self.f.new/self.saved['final_candidate_path'])
        self.h.validate_grade(grade,self.saved,candidate_hash,self.evidence())
        for field in ('task_sha256','worker_sha256','vendor_sha256','solution_sha256'):
            with self.subTest(field=field):
                changed={**grade,field:({} if field=='vendor_sha256' else '0'*64)}
                with self.assertRaises(ValueError):
                    self.h.validate_grade(changed,self.saved,candidate_hash,self.evidence())
        with self.assertRaisesRegex(ValueError,'all-tests pass'):
            self.h.validate_grade({**grade,'status':'pass','passed':True,'tests_run':1},self.saved,candidate_hash,self.evidence())

    def routed_row(self):
        row=copy.deepcopy(self.saved);row['actions'][0]['model_path']='calls/'+report.SAVED_ID+'/result.json'
        evidence=report.saved_evidence_adapter(self.h,self.f.old,self.f.previous,self.f.new,{},self.late['charge'])
        return row,evidence

    def test_exact_request_history_priority_and_feedback_bound(self):
        row,evidence=self.routed_row()
        task=next(t for t in read(self.f.old/'TASKS.json')['selected_rows'] if t['task_id']==row['task_id'])
        prompts=read(self.f.old/'PROMPTS.json')
        self.h.audit_messages(row,self.f.new,evidence,task,prompts)
        path=self.f.new/'calls/task-533-C-call-2/request.json'
        original=read(path)
        for i in range(len(original['body']['input'])):
            with self.subTest(message=i):
                changed=copy.deepcopy(original);changed['body']['input'][i]['content']+=' tampered'
                with replace_json(path,changed):
                    _,reader=self.routed_row()
                    with self.assertRaises(ValueError):
                        self.h.audit_messages(row,self.f.new,reader,task,prompts)

    def test_generated_and_private_files_only_hashed(self):
        row,evidence=self.routed_row()
        original=Path.read_text
        def guarded(path,*args,**kwargs):
            if path.suffix=='.py' or path.is_relative_to(self.f.old/'private'):
                raise AssertionError('semantic private/generated read forbidden')
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',guarded):
            self.h.audit_row(row,self.f.new,evidence)
        candidate=self.f.new/self.saved['final_candidate_path'];original_bytes=candidate.read_bytes()
        try:
            candidate.write_bytes(b'opaque altered invented candidate')
            row,evidence=self.routed_row()
            with self.assertRaisesRegex(ValueError,'candidate hash binding'):
                self.h.audit_row(row,self.f.new,evidence)
        finally:
            candidate.write_bytes(original_bytes)

    def test_command_and_incomplete_retrieval_artifacts_are_pinned(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            files=['task-1-A-eval-1-candidate.command.json','task-1-A-eval-1-candidate.retrieval-attempt-1.json','task-1-A-call-1.candidate.py']
            for name in files:
                (root/name).write_bytes(b'invented opaque incomplete evidence')
            evidence=self.h.Evidence(self.f.old,root)
            report.pin_runtime(evidence,root)
            self.assertEqual(set(evidence.pins),{str(root/name) for name in files})

    def test_reporting_one_use_guard_preserves_claim(self):
        before=report.digest(self.f.new/'REPORT-CLAIM.json')
        with self.assertRaisesRegex(ValueError,'overwrite/replay'):
            self.f.audit()
        self.assertEqual(report.digest(self.f.new/'REPORT-CLAIM.json'),before)
        self.assertFalse((self.f.new/'REPORT-HOLD.json').exists())

    def test_report_labels_historical_primacy_and_policy_change(self):
        text=(self.f.new/'REPORT.md').read_text()
        for phrase in ('post-HOLD amended completion','primary historical report','after results were known','not a pristine preregistered','regardless of agreement','old ambiguous grade-retrieval intent','unused slots are not credited','Unknown charges'):
            self.assertIn(phrase,text)
        self.assertFalse(self.analysis['pristine_preregistered_complete'])

    def test_valid_predispatch_hold_and_adversarial_receipt(self):
        branch=self.f.branch('precall');branch.collect('precall');audit=branch.audit()
        data=read(branch.new/'RESULTS.json');events=[json.loads(l) for l in (branch.new/'EVENTS.jsonl').read_text().splitlines()]
        self.assertEqual(audit['observed_arms'],628)
        self.assertEqual(data['calls'],0)
        self.assertEqual(data['pending_nano_usd'],0)
        self.assertEqual(audit['call_attempt_audit']['attempted_calls'],1785)
        self.assertEqual(audit['call_attempt_audit']['reserved_calls'],1784)
        event=next(e for e in events if e['kind']=='model_pre_dispatch_hold');cid=event['call_id']
        self.assertEqual(cid,'task-533-C-call-2')
        self.assertEqual(audit['call_attempt_audit']['pre_dispatch_unreserved'],1)
        self.assertTrue(all(r['passed'] is None for r in data['results'] if r['observation']=='missing'))
        allowed={report.key(r) for r in self.previous['results'] if r['observation']=='missing'}
        ids={c['call_id'] for c in audit['accounting']['calls']}
        empty={'calls':[],'reserved_attempts':0,'settled_nano_usd':0,'pending_nano_usd':0}
        def check():
            return self.h.audit_pre_dispatch_holds(events,data['results'],allowed,ids,empty,self.h.Evidence(self.f.old,branch.new),False)
        self.assertEqual(check(),{cid})
        path=branch.new/event['artifact_path']
        with replace_json(path,{**read(path),'request_dispatched':True}):
            with self.assertRaises(ValueError):check()
        directory=branch.new/'calls'/cid;directory.mkdir(parents=True)
        (directory/'receipt.json').write_text('{}')
        try:
            with self.assertRaises(ValueError):check()
        finally:
            (directory/'receipt.json').unlink();directory.rmdir();directory.parent.rmdir()
        branch.assert_immutable()

    def test_null_resource_verification_is_unresolved_hold(self):
        branch=self.f.branch('closure');branch.collect('closure');audit=branch.audit()
        self.assertEqual(audit['observed_arms'],720)
        self.assertEqual(audit['resource_audit']['unresolved_blocks'],[12])
        self.assertEqual(read(branch.new/'ANALYSIS.json')['collection_status'],'held')
        data=read(branch.new/'RESULTS.json')
        self.assertIsNone(data['resource_closures'][-1]['verification'])
        with self.assertRaisesRegex(ValueError,'complete resource closure'):
            report.validate_resources(data,self.h.Evidence(self.f.old,branch.new),(11,12),'econ-tool-recovery-completion-v2-20261029-',True)
        branch.assert_immutable()


class ForecastIsolation(unittest.TestCase):
    def test_new_capacity_does_not_mutate_historical_replay(self):
        old=report.load_helpers()
        new=report.load_helpers(completion=True)
        self.assertEqual(old.snapshot()['whole_completion_projection_nano_usd'],38566028025)
        self.assertEqual(new.snapshot()['whole_completion_projection_nano_usd'],42208706860)
        self.assertEqual(old.MAX_CALLS,572)
        self.assertEqual(new.MAX_CALLS,367)
        self.assertEqual(new.snapshot(367,0,0)['remaining_call_capacity'],729)
        self.assertEqual(old.snapshot()['remaining_call_capacity'],1233)


if __name__ == '__main__':
    unittest.main(verbosity=2)
