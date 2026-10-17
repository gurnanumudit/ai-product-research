"""Verify the sensitivity supplement without changing saved evidence.

Default: hashes, deterministic tests and independent saved-result audit.
--rerun: also replay the frozen 23-cell extension into a fresh temporary copy.
No models, API keys, network requests or installed packages are required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "evaluation-reliability"


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    if not __debug__:
        raise SystemExit('Do not use Python -O; assertions are part of verification.')
    frozen = json.loads((ROOT/'FREEZE.json').read_text())
    for family, base in (('local',ROOT), ('frozen_inputs',ORIGINAL)):
        for relative, expected in frozen['files'][family].items():
            assert sha(base/relative) == expected, relative
    receipt = json.loads((ROOT/'results/execution.json').read_text())
    assert receipt['status'] == 'passed'
    for name, expected in receipt['files'].items():
        assert sha(ROOT/'results'/name) == expected, name
    reviewed = json.loads((ROOT/'independent-review.json').read_text())
    assert reviewed['status'] == 'passed'
    for name, expected in reviewed['files'].items():
        assert sha(ROOT/name) == expected, name

    temp = Path(tempfile.mkdtemp(prefix='eval-sensitivity-reproduce-'))
    work = temp/ROOT.name
    work.mkdir()
    # The fixed runner only reads this original study; never writes to it.
    (temp/'evaluation-reliability').symlink_to(ORIGINAL, target_is_directory=True)
    names = set(frozen['files']['local']) | {'FREEZE.json','independent_review.py'}
    for name in names:
        shutil.copy2(ROOT/name,work/name)
    subprocess.run([sys.executable,'-B','-m','unittest','-v','test_sensitivity'],cwd=work,check=True)
    if args.rerun:
        subprocess.run([sys.executable,'-B','analyze.py','run'],cwd=work,check=True)
        for name in ('analysis.json','table-source.json','paired-contrasts.json','cohort-outcomes.jsonl.gz'):
            assert sha(work/'results'/name) == sha(ROOT/'results'/name), name
    else:
        (work/'results').mkdir()
        for name in ('analysis.json','paired-contrasts.json','cohort-outcomes.jsonl.gz'):
            shutil.copy2(ROOT/'results'/name,work/'results'/name)
    subprocess.run([sys.executable,'-B','independent_review.py'],cwd=work,check=True)
    audit = json.loads((work/'independent-review.json').read_text())
    assert audit['status'] == 'passed' and audit['checks'] == reviewed['checks']
    print(json.dumps({'status':'passed','full_extension_replay':args.rerun,
                      'output_directory':str(work),'original_evidence_modified':False},indent=2))


if __name__ == '__main__':
    main()
