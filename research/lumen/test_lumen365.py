import copy
import json
import random
import unittest
from pathlib import Path
from lumen365 import audit, PRECOMMIT_SHA256

HERE = Path(__file__).resolve().parent
FRAME = (HERE / 'lumen365_membership_precommit.json').read_bytes()
COUNTS = json.loads((HERE / 'lumen365_observations.json').read_text())['counts']
LABELS = json.loads((HERE / 'lumen365_oracle.json').read_text())['labels']

class TestPrecommit(unittest.TestCase):
    def test_precommit_matches_pinned_digest(self):
        import hashlib
        self.assertEqual(hashlib.sha256(FRAME).hexdigest(), PRECOMMIT_SHA256)
    def test_authentic_rejects(self):
        x = audit(FRAME, COUNTS, oracle=LABELS)
        self.assertEqual((x['min_errors'], x['max_errors']), (4,4))
        self.assertEqual(x['double_count_invariant'],4)
        self.assertEqual(x['decision'],'reject')
        self.assertTrue(x['membership_verified'] and x['aggregate_values_verified'])
    def test_missing_oracle_abstains(self):
        x = audit(FRAME, COUNTS)
        self.assertEqual(x['conditional_decision'],'reject')
        self.assertEqual(x['decision'],'abstain')
    def test_membership_edit_fails(self):
        edited = FRAME.replace(b'"C07", "C08"', b'"C04", "C08"', 1)
        self.assertEqual(audit(edited, COUNTS, oracle=LABELS)['reason'], 'membership_digest_mismatch')
    def test_aggregate_edit_is_not_caught_by_membership_hash(self):
        altered = dict(COUNTS, gB=1)
        x = audit(FRAME, altered)
        self.assertTrue(x['membership_verified'])
        self.assertEqual((x['min_errors'],x['max_errors']),(3,3))
        self.assertEqual(x['conditional_decision'],'accept')
        self.assertEqual(x['decision'],'abstain')
        checked = audit(FRAME, altered, oracle=LABELS)
        self.assertEqual(checked['reason'],'aggregate_oracle_mismatch')
        self.assertEqual(checked['mismatched_groups'],['gB'])
    def test_all_zero_counts_with_same_frame(self):
        x = audit(FRAME, {g:0 for g in COUNTS}, oracle=LABELS)
        self.assertEqual(x['conditional_decision'],'accept')
        self.assertEqual(x['decision'],'abstain')
    def test_infeasible_counts_abstain(self):
        x = audit(FRAME, dict(COUNTS,gA=0,gB=4,gC=0,gD=4))
        self.assertEqual(x['decision'],'abstain')
    def test_randomized_double_count_oracle(self):
        frame=json.loads(FRAME)
        rng=random.Random(365365)
        for _ in range(200):
            labels={c:rng.randrange(2) for c in frame['case_ids']}
            counts={g:sum(labels[c] for c in members) for g,members in frame['groups'].items()}
            x=audit(FRAME,counts,oracle=labels,max_error_rate=0.5)
            total=sum(labels.values())
            self.assertEqual((x['min_errors'],x['max_errors']),(total,total))
            self.assertEqual(x['double_count_invariant'],total)
            self.assertTrue(x['aggregate_values_verified'])
    def test_invalid_oracle_fails_closed(self):
        x=audit(FRAME,COUNTS,oracle={'C01':0})
        self.assertEqual(x['decision'],'abstain')
    def test_invalid_counts_fails_closed(self):
        self.assertEqual(audit(FRAME,dict(COUNTS,gA=True))['decision'],'abstain')

if __name__=='__main__':unittest.main()
