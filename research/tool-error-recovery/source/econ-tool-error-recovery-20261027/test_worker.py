"""Only invented tiny tasks. Never loads TASKS.json or selected pilot material."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import worker
from worker import evaluate, feedback

TEST = '''import unittest
class TestCases(unittest.TestCase):
    def test_answer(self):
        self.assertEqual(task_func(), 7)
'''


class WorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Darwin cannot set the upstream RLIMIT_AS. Only this disposable synthetic
        # copy disables the memory-limit argument; production vendor/worker unchanged.
        # Linux tests use the actual worker and all upstream guard operations.
        cls.local_copy = None
        if sys.platform == 'darwin':
            cls.local_copy = tempfile.TemporaryDirectory(prefix='.synthetic-worker-', dir=worker.HERE)
            cls.original_file, cls.original_here = worker.__file__, worker.HERE
            directory = Path(cls.local_copy.name)
            source = Path(worker.__file__).read_text()
            anchor = '    exec(compile(source, str(HERE/'
            position = source.index(anchor)
            source = source[:position] + '    source = source.replace("maximum_memory_bytes = 128 * 1024 * 1024 * 1024", "maximum_memory_bytes = None")\n' + source[position:]
            (directory/'worker.py').write_text(source)
            shutil.copytree(worker.HERE/'vendor', directory/'vendor')
            worker.__file__, worker.HERE = str(directory/'worker.py'), directory

    @classmethod
    def tearDownClass(cls):
        if cls.local_copy:
            worker.__file__, worker.HERE = cls.original_file, cls.original_here
            cls.local_copy.cleanup()

    def grade(self, solution, test=TEST, reference=False, timeout=2, hard_timeout=20):
        with tempfile.TemporaryDirectory(prefix='idea19-invented-') as folder:
            task = dict(task_id='BigCodeBench/99999', code_prompt='def task_func():\n',
                        canonical_solution='    return 7\n', test=test, entry_point='task_func')
            Path(folder, '99999.json').write_text(json.dumps(task))
            return evaluate(dict(task_id=task['task_id'], solution=solution, is_reference=reference),
                            folder, timeout=timeout, hard_timeout=hard_timeout)

    def test_success(self):
        result = self.grade('def task_func(): return 7')
        self.assertEqual(result['status'], 'pass', result)
        self.assertTrue(result['test_run_valid'])
        self.assertEqual(result['tests_run'], 1)
        self.assertNotEqual(result['execution_uid'], 0)

    def test_reference_concatenation(self):
        result = self.grade('raise AssertionError("must ignore this")', reference=True)
        self.assertEqual(result['status'], 'pass', result)

    def test_assertion(self):
        result = self.grade('def task_func(): return 0')
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(result['test_run_valid'])
        self.assertIn('AssertionError', result['feedback'])
        self.assertNotIn('self.assertEqual', result['feedback'])

    def test_syntax(self):
        result = self.grade('def task_func(:')
        self.assertEqual((result['status'], result['reason']), ('fail', 'syntax_error'), result)
        self.assertFalse(result['test_run_valid'])

    def test_import(self):
        result = self.grade('import definitely_nonexistent_idea19_synthetic\ndef task_func(): return 7')
        self.assertEqual((result['status'], result['reason']), ('fail', 'import_error'), result)
        self.assertFalse(result['test_run_valid'])

    def test_suite_timeout(self):
        result = self.grade('def task_func():\n    while True: pass', timeout=.2)
        self.assertEqual((result['status'], result['reason']), ('fail', 'timeout'), result)
        self.assertFalse(result['test_run_valid'])

    def test_import_time_loop(self):
        result = self.grade('while True: pass', timeout=.2)
        self.assertEqual((result['status'], result['reason']), ('fail', 'timeout'), result)

    def test_empty_suite_unknown(self):
        result = self.grade('def task_func(): return 7', 'import unittest\nclass TestCases(unittest.TestCase): pass')
        self.assertEqual(result['status'], 'unknown', result)
        self.assertIsNone(result['passed'])

    def test_skipped_suite_unknown(self):
        result = self.grade('def task_func(): return 7', TEST.replace('    def test_answer', '    @unittest.skip("invented")\n    def test_answer'))
        self.assertEqual(result['status'], 'unknown', result)

    def test_generated_code_not_completed(self):
        result = self.grade('return 7')
        self.assertEqual(result['reason'], 'syntax_error', result)

    def test_hard_timeout_unknown(self):
        result = self.grade('while True: pass', timeout=.1, hard_timeout=.15)
        self.assertEqual((result['status'], result['reason']), ('unknown', 'hard_timeout'), result)

    def test_identity_missing_and_traversal_unknown(self):
        for task_id in ('BigCodeBench/99999', '../secret'):
            result = evaluate(dict(task_id=task_id, solution='', is_reference=False), '/nonexistent-idea19-synthetic')
            self.assertEqual(result['status'], 'unknown')

    def test_capped_source_stripping(self):
        trace = 'Traceback (most recent call last):\n  File "__test__.py", line 5, in test\n    SECRET_TEST_SOURCE\nAssertionError: '+('x'*6000)
        result = feedback({'test': trace})
        self.assertNotIn('SECRET_TEST_SOURCE', result)
        self.assertLessEqual(len(result), 4000)

    @unittest.skipUnless(sys.platform == 'linux' and os.geteuid() == 0, 'Linux root supervisor cleanup integration')
    def test_new_session_subprocess_cleanup(self):
        code = 'import subprocess, sys\ndef task_func():\n    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])\n    return 7'
        result = self.grade(code)
        self.assertEqual(result['status'], 'pass', result)
        self.assertTrue(result['execution_uid_cleanup_verified'], result)


if __name__ == '__main__':
    unittest.main()
