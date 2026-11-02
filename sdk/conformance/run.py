"""Check a Plugin against the recorded protocol exchanges in fixtures/.

    python sdk/conformance/run.py -- ruby sdk/ruby/conformance/plugin.rb

Each fixture line is {"in": message} (written to the Plugin's stdin) or {"out": message} (expected on its stdout, in
order). Standard library only, so any SDK's CI can run it.
"""

import json
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def run_fixture(path, command):
    lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    stdin = ''.join(json.dumps(line['in']) + '\n' for line in lines if 'in' in line)
    expected = [line['out'] for line in lines if 'out' in line]
    # Every fixture ends with shutdown, so a conforming Plugin exits by itself
    result = subprocess.run(command, input=stdin, capture_output=True, text=True, timeout=60, check=False)
    try:
        actual = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    except json.JSONDecodeError as error:
        return [f'stdout is not JSON lines ({error}):\n{result.stdout}']

    problems = []
    for index in range(max(len(expected), len(actual))):
        want = expected[index] if index < len(expected) else None
        got = actual[index] if index < len(actual) else None
        if want != got:
            problems.append(f'message {index + 1}:\n    expected {json.dumps(want)}\n    got      {json.dumps(got)}')
    if result.returncode != 0:
        problems.append(f'exited with {result.returncode} after shutdown; stderr:\n{result.stderr}')
    return problems


def main(argv):
    if '--' not in argv or argv.index('--') == len(argv) - 1:
        print(__doc__, file=sys.stderr)
        return 2
    command = argv[argv.index('--') + 1 :]
    failed = 0
    for path in sorted(FIXTURES.glob('*.jsonl')):
        problems = run_fixture(path, command)
        print(f'{"ok  " if not problems else "FAIL"} {path.name}')
        for problem in problems:
            print(f'  {problem}')
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
