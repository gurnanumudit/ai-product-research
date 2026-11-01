"""Additive completion-v2 audit; offline, one use, no historical writes.

Implementation pins are an explicit prelaunch allowlist. Runtime candidate/code
artifacts are mechanically bound and hashed only after collection terminates.
"""
from collections import Counter
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
MAIN = HERE.parent/'econ-tool-error-recovery-20261027-main-v1'
PREVIOUS = HERE.parent/'econ-tool-error-recovery-20261029-continuation-v1'
NODE = '/Users/muditgurnani/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
PHASE = 'completion-v2'
SAVED_KEY = ('BigCodeBench/533', 'C')
SAVED_ID = 'task-533-C-call-1'
SAVED_RESULT = 'recovered-task-533-C-call-1.result.json'
CARRY, MAX_CALLS, FORECAST_CAPACITY = 38648602940, 367, 1096
PRIOR_KNOWN_API, PILOT_API, LATE_COST = 598602940, 91279770, 1272700
HISTORICAL_BUFFER, INFRA_RESERVE = 50000000, 38000000000
LABEL = 'post-HOLD amended completion — completion-v2'
# Never discover implementation files using *.py or any other runtime glob.
IMPLEMENTATION_FILES = ('report_completion.py', 'test_report_completion.py', 'manifest_freeze_fixture.py',
                        'REPORTER-NOTES.json', 'continuation.mjs', 'accounting.mjs', 'host.mjs', 'transport.mjs', 'model-client.mjs', 'monitor.py')
STATIC_FILES = ('OWNER-AUTHORIZATION.json', 'AMENDMENT.json', 'PROTOCOL.md')
HISTORY_FILES = ('RELEASE.json', 'CLAIM.json', 'RESULTS.json', 'EVENTS.jsonl', 'HOLD.json',
                 'REPORT-CLAIM.json', 'REPORT-HOLD.json', 'ACTUAL-HOLD-REVIEW-v1.json',
                 'POSTHOLD-RECEIPT-CHECK-v1.json', 'POSTHOLD-CHARGE-ADDENDUM-v1.json',
                 'ROOT-LATE-FINANCIAL-ADDENDUM-v1.json', 'RECOVERY-PROVENANCE.json', 'report_continuation.py')
OUTPUTS = ('REPORT-CLAIM.json', 'REPORT-HOLD.json', 'ACTUAL-AUDIT.json', 'ANALYSIS.json', 'REPORT.md')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def key(row):
    return row['task_id'], row['arm']


def write_once(path, value):
    with Path(path).open('x') as handle:
        handle.write(value if isinstance(value, str) else json.dumps(value, indent=2, allow_nan=False)+'\n')
        handle.flush()
        os.fsync(handle.fileno())


def load_helpers(previous=PREVIOUS, completion=False):
    """Load read-only helpers, not their CLI. Separate module instances avoid
    changing historical replay constants when replaying the new phase."""
    spec = importlib.util.spec_from_file_location('_completion_offline_helpers', Path(previous)/'report_continuation.py')
    module = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    if completion:
        module.CARRY = CARRY
        module.MAX_CALLS = MAX_CALLS
        module.FORECAST_CAPACITY = FORECAST_CAPACITY
    return module


def validate_release(root, main, previous, evidence):
    release = evidence.read(root, 'RELEASE.json')
    require(release.get('accepted') is True and release.get('phase') == PHASE
            and release.get('independent_review_accepted') is True, 'independent completion-v2 release required')
    require(all(Path(p).is_absolute() for p in release['files']), 'absolute release pin map required')
    required = [root/name for name in (*IMPLEMENTATION_FILES, *STATIC_FILES)]
    required += [previous/name for name in HISTORY_FILES]
    required += [main/name for name in ('RELEASE.json', 'RESULTS.json', 'ACTUAL-AUDIT.json', 'ANALYSIS.json', 'REPORT.md',
                                       'analyze.py', 'actual_report.py', 'audit-costs.mjs', 'billing-scoped.mjs')]
    require(all(str(p) in release['files'] for p in required), 'explicit immutable implementation/history pin absent')
    evidence.verify_pins(root, release['files'])
    claim = evidence.read(root, 'CLAIM.json')
    require(claim['phase'] == PHASE and claim['release_sha256'] == evidence.pin(root/'RELEASE.json'), 'prelaunch claim/release binding')
    require(claim['previous_results_sha256'] == evidence.pin(previous/'RESULTS.json')
            and claim['retained_observed'] == 628 and claim['missing_to_complete'] == 92, 'claim preserved cohort binding')
    authorization = evidence.read(root, 'OWNER-AUTHORIZATION.json')
    require(authorization['approved'] is True, 'owner authorization absent')
    return release


def partition_completion(previous_rows, rows, remaining):
    require(len(previous_rows) == len(rows) == 720, 'all720 assignments required')
    prior, new = {key(r): r for r in previous_rows}, {key(r): r for r in rows}
    require(len(prior) == len(new) == 720 and [key(r) for r in previous_rows] == [key(r) for r in rows], 'assignment identity/order changed')
    observed = {k for k, r in prior.items() if r['observation'] == 'observed'}
    untouched = {k for k, r in prior.items() if r['completion'] == 'not_started'}
    require(len(observed) == 628 and len(untouched) == 91 and set(prior)-observed-untouched == {SAVED_KEY}, '628/91/1 partition')
    require(len(remaining) == 92 and {key(r) for r in remaining} == untouched | {SAVED_KEY}, 'remaining amendment binding')
    for r in remaining:
        require(all(prior[key(r)].get(k) == v for k, v in r.items()), 'remaining original metadata changed')
    for k, row in new.items():
        require(set(row) == set(prior[k]), 'row schema changed')
        for field in ('schema', 'task_id', 'arm', 'condition', 'block'):
            require(row[field] == prior[k][field], 'assignment field changed')
        if k in observed:
            require(row == prior[k], 'preserved628 outcome changed')
    old = prior[SAVED_KEY]
    require(old['calls'] == 1 and len(old['actions']) == 1 and old['actions'][0]['call_id'] == SAVED_ID
            and old['actions'][0]['action'] == 'pending' and not old['evaluations'] and not old['feedback_paths']
            and old['candidate_count'] == 0 and old['final_candidate_path'] is None, 'saved response already consumed historically')
    return prior, new, observed, untouched


def inspect_costs(main, previous, root, node=NODE):
    """Frozen billing reconciliation on all three physical-call directories.
    Late charge reconciliation is additive; the historical ledger stays intact."""
    script = r"""
import fs from 'node:fs'; import path from 'node:path'; import {pathToFileURL} from 'node:url';
const [main,previous,root]=process.argv.slice(1),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const {inspectCosts,inspectFinancialHistory}=await import(pathToFileURL(path.join(main,'audit-costs.mjs')));
const {reconcile,generationId}=await import(pathToFileURL(path.join(main,'billing-scoped.mjs')));
const original=inspectCosts(main),prior=inspectCosts(previous),fresh=inspectCosts(root),ids=[];
for(const [dir,a] of [[main,original],[previous,prior],[root,fresh]])for(const c of a.totals.calls){
 const p=path.join(dir,'calls',c.call_id,'response.json');if(fs.existsSync(p))ids.push(generationId(read(p)));
}
if(new Set(ids).size!==ids.length)throw Error('duplicate physical generation across phases');
const d=path.join(previous,'calls','task-533-C-call-1'),response=read(path.join(d,'response.json'));
const http=read(path.join(d,'response.http.json')),late=read(path.join(previous,'POSTHOLD-RECEIPT-CHECK-v1.json'));
const id=generationId(response);
if(http.status!==200||JSON.stringify(JSON.parse(http.body))!==JSON.stringify(response))throw Error('saved raw response binding');
if(late.status!==200||late.generation_id!==id)throw Error('late receipt identity');
const charge=reconcile(response,JSON.parse(late.body),id);
if(JSON.stringify(charge)!==JSON.stringify(read(path.join(previous,'POSTHOLD-CHARGE-ADDENDUM-v1.json')).charge))throw Error('late addendum reconciliation');
console.log(JSON.stringify({original,prior,fresh,late:{generation_id:id,charge},original_financial:inspectFinancialHistory(main,original.totals)}));
"""
    return json.loads(subprocess.check_output([node, '--input-type=module', '-e', script, str(main), str(previous), str(root)], text=True, stderr=subprocess.PIPE))


def settle_late(account, charge):
    result = copy.deepcopy(account)
    calls = [c for c in result['calls'] if c['call_id'] == SAVED_ID]
    require(len(calls) == 1, 'unique historical saved call required')
    c = calls[0]
    require(c['dispatched'] is True and c['pending_nano_usd'] == HISTORICAL_BUFFER and c['settled_nano_usd'] == 0 and c['usage'] is None, 'historical late-call liability binding')
    require(charge['cost_nano_usd'] == LATE_COST, 'late charge amount')
    usage, latency = charge['usage'], charge['raw_receipt_data'].get('latency')
    writes = charge.get('cache_write_tokens')
    if writes is None:
        writes = usage.get('cache_write')
    c.update(settled_nano_usd=LATE_COST, pending_nano_usd=0, usage=usage, provider_latency_ms=latency, cache_write_tokens=writes)
    for a in (result, result['by_arm']['C']):
        a['settled_nano_usd'] += LATE_COST
        a['pending_nano_usd'] -= HISTORICAL_BUFFER
        a['settled_calls'] += 1
    a = result['by_arm']['C']
    a['usage_known_calls'] += 1; a['usage_unknown_calls'] -= 1
    for name, source in [('input_tokens', 'input'), ('output_tokens', 'output'), ('reasoning_tokens', 'reasoning'), ('cached_tokens', 'cached')]:
        a['known_'+name] += usage[source]
        a[name] = None if a['usage_unknown_calls'] else a['known_'+name]
    if type(writes) is int and writes >= 0:
        a['cache_write_unknown_calls'] -= 1; a['known_cache_write_tokens'] += writes
    a['cache_write_tokens'] = None if a['cache_write_unknown_calls'] else a['known_cache_write_tokens']
    if type(latency) in (int, float) and latency >= 0:
        a['latency_unknown_calls'] -= 1; a['latency_known_calls'] += 1; a['known_provider_latency_ms'] += latency
    a['provider_latency_ms'] = None if a['latency_unknown_calls'] else a['known_provider_latency_ms']
    result['receipt_gets'] += 1
    result['late_receipt_addendum_applied_once'] = True
    return result


def validate_saved_response(root, previous, row, events, amendment, late, evidence, complete):
    consumed = [e for e in events if e['kind'] == 'saved_response_consumed']
    require(len(consumed) <= 1, 'saved response consumed more than once')
    require(not (root/'calls'/SAVED_ID).exists(), 'saved call1 POST/directory forbidden')
    require(not any(e.get('call_id') == SAVED_ID and e['kind'] in ('model_intent', 'model_settled', 'model_hold', 'model_pre_dispatch_hold') for e in events), 'saved call1 financially dispatched again')
    require(not (previous/(SAVED_ID+'.action.json')).exists(), 'saved response previously acted upon')
    response_path = previous/'calls'/SAVED_ID/'response.json'
    require(evidence.pin(response_path) == amendment['source_response_sha256'], 'saved response amendment hash')
    require(late['generation_id'] == amendment['saved_response_generation_id'] and late['charge']['cost_nano_usd'] == amendment['late_charge_nano_usd'], 'saved generation/late receipt binding')
    request = evidence.read(previous, 'calls/'+SAVED_ID+'/request.json')
    # audit_messages separately reconstructs the input from frozen prompts/tasks.
    # Bind every other requestBody field too, including disabled truncation.
    require(request['body'] == dict(model='openai/gpt-6-luna', input=request['body']['input'],
                                   reasoning={'effort': 'medium'}, service_tier='default', max_output_tokens=8192,
                                   store=False, stream=False, truncation='disabled', tools=[],
                                   providerOptions={'gateway': {'only': ['openai']}}), 'saved exact request configuration')
    if not consumed:
        require(not complete and row['passed'] is None and row['calls'] == 1 and not row['evaluations']
                and len(row['actions']) == 1 and row['actions'][0]['action'] == 'pending', 'unconsumed saved response must remain missing')
        return False
    event = consumed[0]
    require(key(event) == SAVED_KEY and event['call_id'] == SAVED_ID and event['block'] == row['block']
            and event['condition'] == row['condition'] and event['new_model_posts'] == 0
            and event['provenance_path'] == 'SAVED-RESPONSE-RECOVERY.json', 'saved consumption event binding')
    provenance = evidence.read(root, 'SAVED-RESPONSE-RECOVERY.json')
    require(provenance['call_id'] == SAVED_ID and provenance['generation_id'] == late['generation_id']
            and provenance['source_response_sha256'] == amendment['source_response_sha256']
            and provenance['charge'] == late['charge'] and provenance['no_new_post'] is True
            and provenance['prior_request_counts_toward_four'] is True and provenance['result_path'] == SAVED_RESULT, 'saved response provenance binding')
    required = {str(previous/'calls'/SAVED_ID/name) for name in ('request.json', 'response.json', 'DISPATCH.json', 'HOLD.json')}
    required |= {str(previous/name) for name in ('POSTHOLD-RECEIPT-CHECK-v1.json', 'POSTHOLD-CHARGE-ADDENDUM-v1.json')}
    require(set(provenance['files']) == required, 'saved provenance exact pin coverage')
    evidence.verify_pins(root, provenance['files'])
    model = evidence.read(root, SAVED_RESULT)
    response = evidence.read(previous, 'calls/'+SAVED_ID+'/response.json')
    response_id = response.get('id', late['generation_id'])
    require(model['call_id'] == SAVED_ID and model['generation_id'] == late['generation_id'] and model['model_request_attempts'] == 1
            and model['response_id'] == response_id and model['responseid'] == response_id
            and model['call_consumed'] is True and model['pending_nano_usd'] == 0 and model['cost_nano_usd'] == LATE_COST
            and model['usage'] == late['charge']['usage'], 'reconstructed saved model identity/cost')
    require(row['actions'][0]['call_id'] == SAVED_ID and row['actions'][0]['model_path'] == SAVED_RESULT, 'saved action result path')
    return True


def saved_evidence_adapter(helper, main, previous, root, shared_pins, charge):
    """Virtual read-only alias for the saved first call. No historical copies or
    synthetic call directory: all actual evidence paths stay in the pin map."""
    class SavedEvidence(helper.Evidence):
        def path(self, base, name):
            if Path(base).resolve() == root and name in ('calls/'+SAVED_ID+'/request.json', 'calls/'+SAVED_ID+'/response.json'):
                return super().path(previous, name)
            return super().path(base, name)

        def read(self, base, name):
            if Path(base).resolve() == root:
                if name == 'calls/'+SAVED_ID+'/result.json':
                    return super().read(root, SAVED_RESULT)
                if name == 'calls/'+SAVED_ID+'/charge.json':
                    return copy.deepcopy(charge)
                if name in ('calls/'+SAVED_ID+'/request.json', 'calls/'+SAVED_ID+'/response.json'):
                    return super().read(previous, name)
                if name == SAVED_ID+'.action.json':
                    saved = super().read(root, name)
                    require(saved['model_path'] == SAVED_RESULT, 'saved action alias mismatch')
                    return {**saved, 'model_path': 'calls/'+SAVED_ID+'/result.json'}
            return super().read(base, name)
    e = SavedEvidence(main, root)
    e.pins = shared_pins
    return e


def validate_resources(data, evidence, blocks, name_prefix, complete):
    closures = data['resource_closures']
    require(len(closures) <= len(blocks) and [c['block'] for c in closures] == list(blocks[:len(closures)]), 'resource block sequence')
    recorded = {c['block'] for c in closures}
    for suffix in ('HOST', 'DISPATCH', 'RESOURCE-CLOSURE'):
        require(all(int(p.name.split('-')[1]) in recorded for p in evidence.continuation.glob('block-*-'+suffix+'.json')), 'unreported resource')
    unresolved, unknown = [], []
    for c in closures:
        n = c['block']; name = name_prefix+str(n)
        require(evidence.read(evidence.continuation, f'block-{n}-RESOURCE-CLOSURE.json') == c, 'resource closure binding')
        require(c.get('name', name) == name and c['infrastructure_reserve_usd'] == 2, 'host name/reserve binding')
        if c.get('creation_dispatched'):
            d = evidence.read(evidence.continuation, f'block-{n}-DISPATCH.json')
            require(d['name'] == name and d['timeout_ms'] == 14400000 and d['infrastructure_reserve_usd'] == 2, 'host dispatch bounds')
        if c.get('creation_confirmed'):
            h = evidence.read(evidence.continuation, f'block-{n}-HOST.json')
            require(h['name'] == name and h['vcpus'] == 2 and h['memory'] == 4096, 'host size bounds')
        verification = c.get('verification')
        if not (c.get('stopped') is True and c.get('deleted') is True and isinstance(verification, dict) and verification.get('empty') is True):
            unresolved.append(n)
        if not (type(c.get('billable_egress_bytes')) in (int, float) and 0 <= c['billable_egress_bytes'] <= 2e9
                and type(c.get('observed_resource_cost_upper_usd')) in (int, float) and 0 <= c['observed_resource_cost_upper_usd'] <= 2):
            unknown.append(n)
        if complete:
            require(c.get('creation_dispatched') is True and c.get('creation_confirmed') is True, 'completed host creation evidence')
    if complete:
        require(len(closures) == len(blocks) and not unresolved and not unknown, 'complete resource closure/usage bounds')
    return dict(recorded=len(closures), verified_closed=len(closures)-len(unresolved), unresolved_blocks=unresolved,
                unknown_usage_blocks=unknown, planned_hosts=len(blocks))


def pin_runtime(evidence, root):
    # Classification is intentionally separate from IMPLEMENTATION_FILES.
    for p in root.iterdir():
        if p.is_file() and (p.name.startswith(('task-', 'result-', 'recovery-', 'recovered-', 'block-')) or p.name in ('SAVED-RESPONSE-RECOVERY.json', 'EVENTS.jsonl')):
            evidence.pin(p)
    if (root/'calls').exists():
        for p in (root/'calls').rglob('*'):
            if p.is_file():
                evidence.pin(p)


def render_report(summary, original_report):
    lines = original_report.render_report(summary).splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith('Main settled API:'))
    end = next(i for i, line in enumerate(lines) if line.startswith('Resource closures verified:'))
    f, resources = summary['financial_audit'], summary['resource_audit']
    lines[start:end+1] = [
        f"Original main API: $0.469631345; first continuation known API including the late receipt: $0.037691825; completion-v2 API: ${f['terminal']['settled_nano_usd']/1e9:.9f}. Pilot API $0.091279770 is retained in financial carry but excluded from main outcomes and efficiency denominators.",
        f"Retained infrastructure reserves across all phases: $38.00, including $4.00 for these two new hosts. The historical $0.05 buffer is retained separately; the old late charge is known, not a second pending liability. New pending API reserve: ${f['terminal']['pending_nano_usd']/1e9:.9f}. Infrastructure invoices, original host10 usage and human/Codex costs remain unknown/unmeasured.",
        f"Starting carry: $38.648602940; starting remaining-capacity forecast: $42.208706860. New actual-call ceiling: 367. Forecast capacity remains 1096 minus new reserved calls; completed-arm unused slots are not credited. Terminal forecast: ${f['terminal']['whole_completion_projection_nano_usd']/1e9:.9f}; commitment including reserves: ${f['combined_committed_nano_usd']/1e9:.9f} / $50. These forecasts are not completion guarantees.",
        f"Completion-v2 resource closures verified: {resources['verified_closed']}/{resources['recorded']} (2 planned, blocks11/12); unresolved: {resources['unresolved_blocks']}; unknown usage: {resources['unknown_usage_blocks']}. The two first-continuation host closures were independently rebound to their saved evidence. All historical reserves remain retained.",
    ]
    lines[0] = '# Tool-error recovery — '+LABEL
    lines = [line.replace('This final main report', 'This additive report').replace('| Arm | Calls |', '| Arm | Attempted calls |') for line in lines]
    lines[1:1] = ['', 'The original main-v1 report remains the primary historical report. All old HOLDs, failed report claims and releases remain immutable. This repaired additive audit preserves 576 original and 52 first-continuation observations (628 total), including the original B/131 recovery unchanged. Only the remaining92 outcomes can be filled. Recovery and receipt/retrieval policies changed after results were known; this is not a pristine preregistered complete run.',
                  '', 'The C/533 recovery policy permits consuming its exact already-posted first response once after the late receipt is verified. That response counts as call1 of four, is billed once in historical costs, and is never posted again. Later rounds are new calls. The recorded consumption status is shown below.',
                  '', f"B/131 retains the original completed grader-command evidence (exit0; saved command status {summary['recovery_audit']['prior_command_status']}) separately from its old ambiguous grade-retrieval intent. The first continuation's single recovery grade determines that amended outcome regardless of agreement; disagreement with the old command summary: {summary['recovery_audit']['disagrees_with_command']}. The command is not used to infer or replace the original missing outcome, and recovery is not repeated here.",
                  '', f"Saved-response consumption verified: {summary['saved_response_consumed']}. Evaluations with saved grades: {summary['evaluation_audit']['completed_evaluations']}; ambiguous intents: {summary['evaluation_audit']['ambiguous_evaluation_intents']}. Tool seconds are observed subtotals; ambiguous durations remain unknown."]
    attempts = summary['call_attempt_audit']
    lines += ['', 'Interaction attempts, financial reservations and physical POST intents are distinct. Proven pre-dispatch attempts remain missing and unreserved; client failures retain their saved billing liabilities. The saved first response contributes one historical physical call, not a new charge.', '',
              '| Arm | Attempted | Reserved | Pre-dispatch unreserved | Physical POST intents | Uncertain dispatch | Unknown charges | Pending API reserve USD |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for arm, a in attempts['by_arm'].items():
        lines.append('| '+' | '.join(map(str, [arm, a['attempted_calls'], a['reserved_calls'], a['pre_dispatch_unreserved'], a['physical_post_intents'], a['uncertain_dispatch'], a['unresolved_charge_calls'], f"{a['pending_api_nano_usd']/1e9:.9f}"]))+' |')
    return '\n'.join(lines)+'\n'


def audit_and_report(root=HERE, main=MAIN, previous=PREVIOUS, node=NODE):
    root, main, previous = map(lambda p: Path(p).resolve(), (root, main, previous))
    require(len({root, main, previous}) == 3, 'separate output/history directories required')
    require(all(not (root/n).exists() for n in OUTPUTS), 'refusing report overwrite/replay')
    markers = [n for n in ('HOLD.json', 'COLLECTION-COMPLETE.json') if (root/n).exists()]
    require(len(markers) == 1, 'exactly one collector terminal marker required')
    write_once(root/'REPORT-CLAIM.json', dict(phase=PHASE, at=datetime.datetime.now(datetime.timezone.utc).isoformat(), pid=os.getpid(), no_replay=True))
    try:
        return _report(root, main, previous, node, markers[0])
    except Exception as error:
        write_once(root/'REPORT-HOLD.json', dict(error_type=type(error).__name__, reason=str(error), no_replay=True))
        raise


def _report(root, main, previous, node, marker_name):
    # Verify executable helper bytes before importing them. Remaining release
    # paths and evidence are checked by the imported read-only Evidence class.
    manifest = json.loads((root/'RELEASE.json').read_text())
    helper_path = previous/'report_continuation.py'
    require(manifest.get('files', {}).get(str(helper_path)) == digest(helper_path), 'helper source pin before import')
    h = load_helpers(previous)
    v = load_helpers(previous, completion=True)
    evidence, prev_evidence = v.Evidence(main, root), h.Evidence(main, previous)
    prev_evidence.pins = evidence.pins
    read = evidence.read
    validate_release(root, main, previous, evidence)
    for source in (main, previous):
        release = read(source, 'RELEASE.json')
        evidence.verify_pins(source, release['files'])
    old_audit = read(main, 'ACTUAL-AUDIT.json')
    require(old_audit['accepted'] is True and old_audit['observed_arms'] == 576, 'historical original audit')
    evidence.verify_pins(main, old_audit['files'])
    historical_review = read(previous, 'ACTUAL-HOLD-REVIEW-v1.json')
    evidence.verify_pins(previous, historical_review['files'])
    previous_claim = read(previous, 'CLAIM.json')
    require(previous_claim['release_sha256'] == evidence.pin(previous/'RELEASE.json'), 'historical claim/release binding')
    amendment, old_data, prev_data, data = read(root, 'AMENDMENT.json'), read(main, 'RESULTS.json'), read(previous, 'RESULTS.json'), read(root, 'RESULTS.json')
    require(amendment['source_results_sha256'] == evidence.pin(previous/'RESULTS.json'), 'amendment previous-results hash')
    require(amendment['phase'] == PHASE and amendment['retained_observed'] == 628
            and Path(amendment['source_main']).resolve() == main and Path(amendment['source_previous']).resolve() == previous,
            'amendment phase/source binding')
    for field, expected in dict(conservative_carry_nano_usd=CARRY, new_model_call_maximum=MAX_CALLS, inherited_forecast_capacity=FORECAST_CAPACITY,
                                nondecreasing_forecast_per_call_nano_usd=3248270, initial_combined_forecast_nano_usd=42208706860,
                                all_known_API_including_late_nano_usd=PRIOR_KNOWN_API, historical_pending_reserve_retained_nano_usd=HISTORICAL_BUFFER,
                                combined_cap_nano_usd=50000000000, new_hosts_maximum=2, new_infra_reserve_usd=4, prior_infra_reserves_retained_usd=34).items():
        require(amendment[field] == expected, 'amendment finance binding: '+field)
    require(data['phase'] == PHASE and Path(data['source_main']).resolve() == main and Path(data['source_previous']).resolve() == previous
            and data['original_calls'] == 1647 and data['previous_calls'] == 137 and data['prior_known_api_including_pilot_nano_usd'] == PRIOR_KNOWN_API
            and data['assigned_tasks'] == 240 and data['assigned_arms'] == 720, 'completion dataset identity')
    complete = marker_name == 'COLLECTION-COMPLETE.json'
    require(data['collection_status'] == ('complete' if complete else 'held'), 'terminal collection status')
    old, prev, original_observed, first_untouched = h.partition_rows(old_data['results'], prev_data['results'], read(previous, 'AMENDMENT.json')['todo'])
    prior, new, preserved, untouched = partition_completion(prev_data['results'], data['results'], amendment['remaining'])
    require(preserved >= original_observed and len(preserved-original_observed) == 52, '576 plus52 preserved')
    h.validate_recovery(old[h.RECOVERY], prev[h.RECOVERY], read(previous, 'RECOVERY-PROVENANCE.json'), prev_evidence)
    tasks, schedule, prompts = read(main, 'TASKS.json')['selected_rows'], read(main, 'SCHEDULE.json'), read(main, 'PROMPTS.json')
    bytask, byschedule = {t['task_id']: t for t in tasks}, {s['task_id']: s for s in schedule}
    require(len(bytask) == len(byschedule) == 240 and bytask.keys() == byschedule.keys(), 'schedule identity')
    require(Counter(s['condition'] for s in schedule) == dict.fromkeys(h.load_original_functions(main)[0].CONDITIONS, 60), 'condition allocation')
    # Repaired historical actual audit: no old reporter entrypoint or write.
    historical_actions = set()
    for row in prev_data['results']:
        k = key(row); source = main if k in original_observed or k == h.RECOVERY else previous
        if row['completion'] != 'not_started':
            result_source = previous if k == h.RECOVERY else source
            require(read(result_source, 'result-'+row['task_id'].split('/')[1]+'-'+row['arm']+'.json') == row, 'historical result binding')
        checked = h.audit_row(row, source, prev_evidence, k == h.RECOVERY)
        h.audit_messages(row, source, prev_evidence, bytask[row['task_id']], prompts)
        require(not historical_actions & checked['action_ids'], 'duplicate historical action')
        historical_actions |= checked['action_ids']
    costs = inspect_costs(main, previous, root, node)
    for source, name in ((main, 'original'), (previous, 'prior'), (root, 'fresh')):
        evidence.verify_pins(source, costs[name]['pins'])
    orig_account, prev_account, fresh = (costs[n]['totals'] for n in ('original', 'prior', 'fresh'))
    require(orig_account == old_audit['accounting'] and orig_account['reserved_attempts'] == 1647 and orig_account['settled_nano_usd'] == 469631345 and orig_account['pending_nano_usd'] == 0, 'historical main accounting')
    require(prev_account['reserved_attempts'] == 137 and prev_account['settled_nano_usd'] == 36419125 and prev_account['pending_nano_usd'] == HISTORICAL_BUFFER, 'historical continuation accounting')
    historical = h.combine_accounts(orig_account, prev_account)
    require({c['call_id'] for c in historical['calls']} == historical_actions, 'historical actions/costs')
    previous_financial = h.financial_history(read(previous, 'EVENTS.jsonl'), prev_account, first_untouched, {c['call_id'] for c in orig_account['calls']})
    prev_marker = read(previous, 'HOLD.json')
    for field, expected in previous_financial['terminal'].items():
        require(prev_data[field] == expected and prev_marker[field] == expected, 'historical terminal snapshot')
    previous_resources = validate_resources(prev_data, prev_evidence, (10, 11), 'econ-tool-recovery-completion-v1-20261029-', True)
    cleanup = read(main, 'APPROVED-CLEANUP-RESULT-v1.json')
    require(cleanup.get('closure_verified') is True and cleanup.get('deleted') is True and (cleanup.get('verification') or {}).get('empty') is True, 'historical main cleanup')
    normalized = settle_late(prev_account, costs['late']['charge'])
    require(orig_account['settled_nano_usd'] + normalized['settled_nano_usd'] + PILOT_API == PRIOR_KNOWN_API and normalized['pending_nano_usd'] == 0, 'known prior API carry')
    late_finance = read(previous, 'ROOT-LATE-FINANCIAL-ADDENDUM-v1.json')
    evidence.verify_pins(previous, late_finance['files'])
    require(late_finance['combined_known_API_nano_usd'] == PRIOR_KNOWN_API and late_finance['late_cost_nano_usd'] == LATE_COST
            and late_finance['historical_pending_reserve_retained_nano_usd'] == HISTORICAL_BUFFER, 'late financial addendum binding')
    account = h.combine_accounts(h.combine_accounts(orig_account, normalized), fresh)
    events = read(root, 'EVENTS.jsonl')
    consumed = validate_saved_response(root, previous, new[SAVED_KEY], events, amendment, costs['late'], evidence, complete)
    routed = saved_evidence_adapter(v, main, previous, root, evidence.pins, costs['late']['charge'])
    rows, evaluations = [], Counter()
    for row in data['results']:
        k = key(row); sched = byschedule[row['task_id']]
        require(row['condition'] == sched['condition'] and row['block'] == sched['block'] and row['arm'] in sched['arms'], 'row schedule binding')
        source, reader, recovery = root, evidence, False
        if k in original_observed or k == h.RECOVERY:
            source, reader, recovery = main, prev_evidence, k == h.RECOVERY
        elif k in preserved:
            source, reader = previous, prev_evidence
        elif k == SAVED_KEY:
            source, reader = root, routed
        if k not in preserved and (row != prior[k] or (root/('result-'+row['task_id'].split('/')[1]+'-'+row['arm']+'.json')).exists()):
            require(read(root, 'result-'+row['task_id'].split('/')[1]+'-'+row['arm']+'.json') == row, 'new individual result binding')
        audited_row = copy.deepcopy(row)
        if k == SAVED_KEY:
            require(row['actions'][0]['model_path'] in (SAVED_RESULT, 'calls/'+SAVED_ID+'/result.json'), 'saved action model path')
            audited_row['actions'][0]['model_path'] = 'calls/'+SAVED_ID+'/result.json'
        checked = v.audit_row(audited_row, source, reader, recovery)
        v.audit_messages(audited_row, source, reader, bytask[row['task_id']], prompts)
        checked.pop('action_ids'); evaluations.update(checked)
        rows.append({**row, 'domain': bytask[row['task_id']]['domain'], 'completed': row['completion'] == 'complete'})
    old_ids = {c['call_id'] for c in historical['calls']}
    allowed = untouched | {SAVED_KEY}
    require(not {c['call_id'] for c in fresh['calls']} & old_ids, 'original/previous call ID repeated')
    pre_dispatch = v.audit_pre_dispatch_holds(events, rows, allowed, old_ids, fresh, evidence, complete)
    for cid in pre_dispatch:
        require(not (previous/'calls'/cid).exists(), 'pre-dispatch conflicts with previous client evidence')
    attempts = v.reconcile_call_attempts(rows, account, pre_dispatch)
    financial = v.financial_history(events, fresh, allowed, old_ids, pre_dispatch)
    marker = read(root, marker_name)
    for field, expected in financial['terminal'].items():
        require(data[field] == expected and marker[field] == expected, 'completion terminal financial snapshot')
    resource = validate_resources(data, evidence, (11, 12), 'econ-tool-recovery-completion-v2-20261029-', complete)
    if complete:
        require(all(r['observation'] == 'observed' for r in rows) and financial['actual_plus_pending_cap_satisfied'] and financial['remaining_forecast_cap_satisfied'], 'completed coverage/finance')
    analysis, original_report = h.load_original_functions(main)
    summary = analysis.summarize(rows, 240, bootstrap=True)
    summary.update(phase=PHASE, label=LABEL, collection_status=data['collection_status'], accounting=account,
                   financial_audit=financial, previous_historical_financial_audit=previous_financial,
                   historical_previous_accounting=prev_account, previous_known_accounting=normalized,
                   resource_audit=resource, previous_resource_audit=previous_resources, evaluation_audit=dict(evaluations),
                   call_attempt_audit=attempts, pre_dispatch_unreserved_call_ids=sorted(pre_dispatch), saved_response_consumed=consumed,
                   recovery_audit=dict(prior_command_status=prev[h.RECOVERY]['recovery_prior_command_status'],
                                       disagrees_with_command=prev[h.RECOVERY]['recovery_disagrees_with_command'],
                                       policy=prev[h.RECOVERY]['recovery_policy']),
                   infrastructure_actual_usd=data['actual_infrastructure_usd'], infrastructure_reserve_usd=38,
                   historical_buffer_nano_usd=HISTORICAL_BUFFER, original_report_primary_historical=True,
                   pristine_preregistered_complete=False, unchanged_observed_rows=628, human_codex_costs='unmeasured')
    summary['secondary'] = {a: original_report.secondary_metrics([r for r in rows if r['arm'] == a], account['by_arm'][a]) for a in 'ABC'}
    exposure = ('assigned', 'first_grade_observed', 'first_actual_failed', 'first_report_differs', 'first_verdict_differs', 'first_report_comparison_unknown', 'first_fail_final_pass')
    summary['descriptive_condition_exposure'] = {c: {a: {k: value for k, value in original_report.secondary_metrics([r for r in rows if r['arm'] == a and r['condition'] == c], {}).items() if k in exposure} for a in 'ABC'} for c in analysis.CONDITIONS}
    summary['descriptive_domains'] = {d: {a: analysis.metrics([r for r in rows if r['domain'] == d and r['arm'] == a]) for a in 'ABC'} for d in sorted({t['domain'] for t in tasks})}
    for directory in (main, previous, root):
        pin_runtime(evidence, directory)
    evidence.pin(root/'REPORT-CLAIM.json')
    require(all(digest(p) == value for p, value in evidence.pins.items()), 'evidence changed during audit')
    audit = dict(accepted=True, phase=PHASE, label=LABEL, observed_arms=sum(r['observation'] == 'observed' for r in rows),
                 preserved_original_observed=576, preserved_previous_observed=52, unchanged_observed_rows=628,
                 files=evidence.pins, verified_files=len(evidence.pins), accounting=account, financial_audit=financial,
                 previous_historical_financial_audit=previous_financial, historical_previous_accounting=prev_account,
                 previous_known_accounting=normalized, resource_audit=resource, previous_resource_audit=previous_resources,
                 call_attempt_audit=attempts, saved_response_consumed=consumed, evaluation_audit=dict(evaluations),
                 no_execution_or_provider_calls=True, independent_actual_review_pending=True, further_study_authorized=False)
    text = render_report(summary, original_report)
    write_once(root/'ACTUAL-AUDIT.json', audit); write_once(root/'ANALYSIS.json', summary); write_once(root/'REPORT.md', text)
    return audit


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actual', action='store_true', required=True)
    parser.parse_args()
    result = audit_and_report()
    print(json.dumps({'accepted': True, 'phase': PHASE, 'observed_arms': result['observed_arms']}))
