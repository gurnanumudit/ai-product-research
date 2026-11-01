"""One remote evaluation; only invented fixtures may be evaluated locally."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
COMMIT = 'fd584be94e606dcc605a5b37c108e0a70a93ea20'
VENDOR = {
    'bigcodebench/eval/__init__.py': 'b27e25489377305adbca69987277ac3be739cb3eca6c0c0ac65d0c0ed8f9e055',
    'bigcodebench/eval/utils.py': 'f891d31d711fc0db602763330db834fe54c6d4a159d32033826fe62b7fd30f57',
    'bigcodebench/eval/_special_oracle.py': '0cf930163987d30f455547aec6cbc500a154bc58a2eb109aa247ef4e0962448b',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def uid_pids(uid):
    """Return non-zombie UID processes; nobody is exclusive to evaluations."""
    require(sys.platform == 'linux' and os.geteuid() == 0 and uid != 0, 'UID cleanup requires Linux root supervisor')
    found = []
    for path in Path('/proc').glob('[0-9]*/status'):
        try:
            lines = path.read_text().splitlines()
            row = next(x for x in lines if x.startswith('Uid:'))
            state = next(x for x in lines if x.startswith('State:')).split()[1]
            if int(row.split()[1]) == uid and state != 'Z':
                found.append(int(path.parent.name))
        except (FileNotFoundError, ProcessLookupError):
            pass
    return found


def cleanup_uid(uid):
    for _ in range(3):
        for pid in uid_pids(uid):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        time.sleep(.05)
        if not uid_pids(uid):
            return True
    return False


def feedback(details):
    """Keep ordinary traceback locations/errors; omit indented source/caret lines."""
    lines = []
    for trace in details.values():
        for line in str(trace).splitlines():
            if line and (not line[0].isspace() or line.lstrip().startswith('File "')):
                lines.append(line)
    return '\n'.join(lines)[:4000]


def classify(status, details, observation):
    ran = observation.get('tests_run', 0)
    expected = observation.get('tests_expected', 0)
    valid = (observation.get('suite_completed') is True and expected > 0 and ran == expected
             and observation.get('skipped', 0) == 0 and observation.get('expected_failures', 0) == 0)
    text = feedback(details)
    if observation.get('phase') not in ('exec', 'suite'):
        result, reason = 'unknown', 'evaluator_setup_error'
    elif status == 'pass' and valid:
        result, reason = 'pass', 'all_tests_passed'
    elif status == 'pass':
        result, reason = 'unknown', 'empty_skipped_or_incomplete_suite'
    elif status == 'timeout' or 'TimeoutException' in text or 'Timed out!' in text:
        result, reason = 'fail', 'timeout'
        valid = False
    elif status == 'fail':
        result = 'fail'
        reason = ('syntax_error' if 'SyntaxError' in text else
                  'import_error' if 'ImportError' in text or 'ModuleNotFoundError' in text else 'test_failure')
    else:
        result, reason = 'unknown', 'unrecognized_evaluator_result'
    return dict(status=result, passed=True if result == 'pass' else False if result == 'fail' else None,
                reason=reason, test_run_valid=valid, tests_run=ran, tests_expected=expected,
                skipped=observation.get('skipped', 0), failures=observation.get('failures'),
                errors=observation.get('errors'), official_status=status, feedback=text)


def child(payload):
    require(os.geteuid() != 0, 'candidate execution must be nonroot')
    import multiprocessing as mp
    import traceback
    import importlib
    mp.set_start_method('fork', force=True)
    sys.path.insert(0, str(HERE/'vendor'))
    for name, pin in VENDOR.items():
        require(sha((HERE/'vendor'/name).read_bytes()) == pin, 'vendor hash mismatch')
    official = importlib.import_module('bigcodebench.eval')
    # The upstream guard imports pyplot. Warm it before forking so font-cache
    # setup is inside the outer deadline, not mistaken for candidate timeout.
    import matplotlib.pyplot
    source = (HERE/'vendor/bigcodebench/eval/__init__.py').read_text()
    # Exact, fail-closed instrumentation; vendored bytes remain untouched.
    patches = [
        ('timeout = max(os.getenv("EVALPLUS_TIMEOUT_PER_TASK", 120), time_limit) + 1',
         'timeout = time_limit'),
        ('full_code = code + "\\n" + test_code',
         '_worker_observation["phase"] = "exec"\n            full_code = code + "\\n" + test_code'),
        ('start_time = time.time()',
         '_worker_observation.update(phase="suite", tests_expected=suite.countTestCases())\n                start_time = time.time()'),
        ('issues = test_result.failures + test_result.errors',
         '_worker_observation.update(suite_completed=True, tests_run=test_result.testsRun, skipped=len(test_result.skipped), expected_failures=len(test_result.expectedFailures), failures=len(test_result.failures), errors=len(test_result.errors))\n            issues = test_result.failures + test_result.errors'),
        ('details["ALL"] = str(e)', 'details["ALL"] = _worker_traceback.format_exc()'),
    ]
    for before, after in patches:
        require(source.count(before) == 1, 'official instrumentation anchor changed')
        source = source.replace(before, after)
    exec(compile(source, str(HERE/'vendor/bigcodebench/eval/__init__.py'), 'exec'), official.__dict__)
    with mp.Manager() as manager:
        observed = manager.dict()
        official._worker_observation = observed
        official._worker_traceback = traceback
        status, details = official.untrusted_check(payload['code'], payload['test'], payload['entry_point'],
                                                  min_time_limit=payload['timeout'], gt_time_limit=payload['timeout'])
        result = classify(status, details, dict(observed))
    result['execution_uid'] = os.geteuid()
    return result


def evaluate(request, tasks_dir, timeout=60, hard_timeout=90):
    """Supervisor: load one protected task, run evaluator in a fresh process/tempdir."""
    started = time.monotonic()
    result = dict(schema=1, task_id=request.get('task_id'), is_reference=request.get('is_reference'),
                  status='unknown', passed=None, test_run_valid=False, reason='worker_error', feedback='',
                  tests_run=0, tests_expected=0, official_status=None, execution_uid=None,
                  evaluator_commit=COMMIT, vendor_sha256=VENDOR, worker_sha256=sha(Path(__file__).read_bytes()))
    try:
        require(set(request) == {'task_id', 'solution', 'is_reference'}, 'request fields')
        match = re.fullmatch(r'BigCodeBench/(\d+)', request['task_id'])
        require(match is not None and type(request['is_reference']) is bool and isinstance(request['solution'], str), 'request types')
        require(0 < timeout <= 60 and timeout < hard_timeout <= 90, 'timeout bounds')
        root = Path(tasks_dir).resolve()
        path = root/(match.group(1)+'.json')
        require(not path.is_symlink() and path.resolve().parent == root, 'task path')
        raw = path.read_bytes()
        task = json.loads(raw)
        require(task['task_id'] == request['task_id'], 'task identity')
        require(all(isinstance(task[k], str) for k in ('code_prompt', 'canonical_solution', 'test', 'entry_point')), 'task schema')
        code = task['code_prompt']+task['canonical_solution'] if request['is_reference'] else request['solution']
        payload = dict(code=code, test=task['test'], entry_point=task['entry_point'], timeout=timeout)
        result.update(task_sha256=sha(raw), solution_sha256=sha(code.encode()), timeout_seconds=timeout, hard_timeout_seconds=hard_timeout)
        privilege = {}
        if os.geteuid() == 0:
            import pwd
            user = pwd.getpwnam('nobody')
            privilege = dict(user=user.pw_uid, group=user.pw_gid, extra_groups=[])
            require(not uid_pids(user.pw_uid), 'execution UID already occupied')
        # No provider credentials or inherited Python startup hooks in candidate environment.
        env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TZ') if k in os.environ}
        env.update(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MPLBACKEND='Agg')
        with tempfile.TemporaryDirectory(prefix='idea19-grade-') as temp:
            if privilege:
                os.chown(temp, privilege['user'], privilege['group'])
            env.update(HOME=temp, TMPDIR=temp, MPLCONFIGDIR=temp)
            output_stream = tempfile.TemporaryFile(mode='w+t', dir=temp)
            proc = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--child'],
                                    stdin=subprocess.PIPE, stdout=output_stream, stderr=subprocess.DEVNULL,
                                    cwd=temp, env=env, start_new_session=True, text=True, **privilege)
            try:
                proc.communicate(json.dumps(payload), timeout=hard_timeout)
                require(proc.returncode == 0, 'evaluator process failed')
                output_stream.seek(0)
                output = output_stream.read(65537)
                require(len(output) <= 65536, 'evaluator output bound')
                observed = json.loads(output)
                require(observed['execution_uid'] != 0, 'root execution')
                result.update(observed)
            except subprocess.TimeoutExpired:
                result.update(reason='hard_timeout', feedback='Evaluator exceeded hard deadline; outcome unknown.')
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
                output_stream.close()
                for stream in (proc.stdin, proc.stdout):
                    if stream is not None:
                        stream.close()
                if privilege:
                    result['execution_uid_cleanup_verified'] = cleanup_uid(privilege['user'])
                    if not result['execution_uid_cleanup_verified']:
                        result.update(status='unknown', passed=None, test_run_valid=False,
                                      reason='execution_uid_cleanup_failed', feedback='Nonroot subprocess closure unresolved.')
                else:
                    result['execution_uid_cleanup_verified'] = False
                    result['local_synthetic_only'] = True
    except Exception as error:
        # Do not echo task JSON, test source, reference, or arbitrary request values.
        result.update(status='unknown', passed=None, test_run_valid=False,
                      reason='worker_error', feedback=type(error).__name__+': evaluator admission/setup failed')
    result['elapsed_seconds'] = time.monotonic()-started
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request')
    parser.add_argument('--tasks-dir')
    parser.add_argument('--output')
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        try:
            result = child(json.load(sys.stdin))
        except BaseException:
            result = dict(status='unknown', passed=None, test_run_valid=False, reason='evaluator_setup_error',
                          feedback='Evaluator setup failed.', execution_uid=os.geteuid())
        print(json.dumps(result, allow_nan=False))
        return
    parser.error('--request, --tasks-dir and --output are required') if not all((args.request, args.tasks_dir, args.output)) else None
    with open(args.request) as stream:
        request = json.load(stream)
    result = evaluate(request, args.tasks_dir)
    with open(args.output, 'x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ('task_id', 'status', 'test_run_valid', 'reason')}))


if __name__ == '__main__':
    main()
