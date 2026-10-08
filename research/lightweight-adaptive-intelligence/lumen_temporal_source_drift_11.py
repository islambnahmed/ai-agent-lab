"""Lumen 11 — prequential source-dependence drift benchmark.

Run: python lumen_temporal_source_drift_11.py
Only past, unlabeled source answers may inform the current grouping.
Compare frozen, cumulative, and bounded-window source clustering under
an abrupt shift in a five-source wrong-answer copying bloc.
This is a synthetic identifiability/robustness study, not truth detection.
"""
from collections import Counter, deque
from random import Random
from statistics import mean

N = 7
PRETRAIN = 120
ONLINE = 200
CHANGE_AT = 60  # in online stream; first 60 test items use old topology
REPS = 60
CLUSTER_THRESHOLD = .90
WINDOW = 60


def plurality(labels):
    counts = Counter(labels)
    top = max(counts.values())
    winners = [v for v, c in counts.items() if c == top]
    return winners[0] if len(winners) == 1 else None


def groups_from_agreement(pair_counts, samples, threshold=CLUSTER_THRESHOLD):
    if not samples:
        return tuple((i,) for i in range(N))
    clusters = [(i,) for i in range(N)]
    while True:
        choices = []
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                cross = min(pair_counts[a][b] / samples for a in clusters[i]
                            for b in clusters[j])
                if cross >= threshold:
                    choices.append((cross, i, j))
        if not choices:
            return tuple(sorted(clusters))
        _, i, j = max(choices)
        merged = tuple(sorted(clusters[i] + clusters[j]))
        clusters = [c for k, c in enumerate(clusters) if k not in (i, j)]
        clusters.append(merged)
        clusters.sort()


def predict(row, groups):
    votes = [plurality([row[i] for i in g]) for g in groups]
    return plurality([x for x in votes if x is not None]) if any(x is not None for x in votes) else None


class AgreementHistory:
    def __init__(self, maxlen=None):
        self.maxlen = maxlen
        self.rows = deque()
        self.counts = [[0] * N for _ in range(N)]

    def add(self, row):
        if self.maxlen and len(self.rows) >= self.maxlen:
            self._change(self.rows.popleft(), -1)
        self.rows.append(tuple(row))
        self._change(row, 1)

    def _change(self, row, delta):
        for i in range(N):
            for j in range(i + 1, N):
                self.counts[i][j] += delta * (row[i] == row[j])
                self.counts[j][i] = self.counts[i][j]

    def groups(self):
        return groups_from_agreement(self.counts, len(self.rows))


def source_row(rng, regime, switched):
    truth = rng.randrange(61)
    wrong = (truth + 1) % 61
    bloc = (2, 3, 4, 5, 6) if switched else (0, 1, 2, 3, 4)
    row = [None] * N
    for i in range(N):
        if i in bloc:
            row[i] = truth if regime == 'near' and rng.random() < .03 else wrong
        else:
            row[i] = truth if rng.random() < .9 else wrong
    return truth, row


def expected(switched):
    bloc = (2, 3, 4, 5, 6) if switched else (0, 1, 2, 3, 4)
    return {bloc} | {(i,) for i in range(N) if i not in bloc}


def experiment(reps=REPS):
    output = {}
    for regime in ('exact', 'near'):
        for drift in (False, True):
            label = f'{regime}/{"switch" if drift else "stable"}'
            metrics = {p: Counter() for p in ('raw', 'frozen', 'cumulative', 'rolling', 'oracle')}
            phases = {p: {q: Counter() for q in ('before', 'first20', 'next40', 'late')}
                      for p in metrics}
            group_recovery = {p: {q: Counter() for q in phases['raw']}
                              for p in ('frozen', 'cumulative', 'rolling')}
            per_rep_rolling_lags = []
            for rep in range(reps):
                rng = Random(110000 + rep * 9973 + (0 if regime == 'exact' else 1) + (0 if not drift else 17))
                cumulative, rolling = AgreementHistory(), AgreementHistory(WINDOW)
                for _ in range(PRETRAIN):
                    _, row = source_row(rng, regime, False)
                    cumulative.add(row)
                    rolling.add(row)
                frozen = cumulative.groups()
                recovered = []
                for t in range(ONLINE):
                    switched = drift and t >= CHANGE_AT
                    truth, row = source_row(rng, regime, switched)
                    phase = ('before' if t < CHANGE_AT else 'first20' if t < CHANGE_AT + 20
                             else 'next40' if t < CHANGE_AT + 60 else 'late')
                    groups = {'frozen': frozen, 'cumulative': cumulative.groups(),
                              'rolling': rolling.groups()}
                    target = expected(switched)
                    for policy, gr in groups.items():
                        ok = set(gr) == target
                        group_recovery[policy][phase]['correct' if ok else 'wrong'] += 1
                    if switched:
                        recovered.append(set(groups['rolling']) == target)
                    decisions = {'raw': plurality(row),
                                 'oracle': predict(row, tuple(sorted(target))),
                                 **{p: predict(row, gr) for p, gr in groups.items()}}
                    for policy, decision in decisions.items():
                        state = 'abstain' if decision is None else 'correct' if decision == truth else 'wrong'
                        metrics[policy][state] += 1
                        phases[policy][phase][state] += 1
                    # prequential: update only AFTER scoring the current item
                    cumulative.add(row)
                    rolling.add(row)
                if drift:
                    # Earliest 5 consecutive correct topologies after change.
                    first = next((i for i in range(len(recovered) - 4)
                                  if all(recovered[i:i + 5])), None)
                    per_rep_rolling_lags.append(first)
            def summarise(c):
                n = sum(c.values())
                answered = n - c['abstain']
                return {'n': n, 'accuracy_all': round(c['correct'] / n, 4),
                        'coverage': round(answered / n, 4),
                        'error_given_answer': round(c['wrong'] / answered, 4) if answered else None}
            output[label] = {
                'total': {p: summarise(c) for p, c in metrics.items()},
                'phase': {p: {q: summarise(c) for q, c in d.items()} for p, d in phases.items()},
                'topology_recovery': {p: {q: round(c['correct'] / sum(c.values()), 4)
                                           for q, c in d.items()} for p, d in group_recovery.items()},
                'rolling_recovery_lag': ({'recovered': sum(x is not None for x in per_rep_rolling_lags),
                                          'of': reps,
                                          'mean_lag_if_recovered': round(mean(x for x in per_rep_rolling_lags if x is not None), 1)
                                          if any(x is not None for x in per_rep_rolling_lags) else None}
                                         if drift else None),
            }
    # Guard against data leakage and a misleading apparent universal result.
    assert output['exact/switch']['topology_recovery']['frozen']['late'] == 0
    assert output['exact/switch']['topology_recovery']['rolling']['late'] > .95
    assert output['exact/switch']['phase']['rolling']['late']['accuracy_all'] > .75
    assert output['exact/switch']['phase']['rolling']['late']['accuracy_all'] > output['exact/switch']['phase']['frozen']['late']['accuracy_all']
    assert output['exact/stable']['topology_recovery']['frozen']['late'] == 1
    for label, data in output.items():
        print('\n' + label)
        print('late accuracy:', {p: d['late']['accuracy_all'] for p, d in data['phase'].items()})
        print('late topology recovery:', {p: d['late'] for p, d in data['topology_recovery'].items()})
        print('early post-change recovery:', {p: d['first20'] for p, d in data['topology_recovery'].items()})
        print('rolling lag:', data['rolling_recovery_lag'])
    print('\nLimit: matching answer histories cannot prove copying or truth. Switch and regime are synthetic.')
    return output


if __name__ == '__main__':
    experiment()
