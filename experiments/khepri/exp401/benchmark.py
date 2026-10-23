import itertools
import json
import tempfile
from crash_recovery import CUTS, run_sequence
from test_crash_recovery import SCOPES


def main():
    results = {}
    for mode in ('replay', 'freeze', 'keyed'):
        for scope in SCOPES:
            counts = {'total': 0, 'zero': 0, 'one': 0, 'multiple': 0, 'completed': 0}
            for cuts in itertools.product(CUTS, repeat=2):
                with tempfile.TemporaryDirectory() as td:
                    r = run_sequence(td, scope, {'text': 'same payload'}, mode, cuts)
                counts['total'] += 1
                counts['zero' if r['effects']==0 else 'one' if r['effects']==1 else 'multiple'] += 1
                counts['completed'] += (r['ledger']=='complete')
            results[mode + '/' + scope['operation']] = counts
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
