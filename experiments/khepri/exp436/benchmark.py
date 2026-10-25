"""Two synthetic leakage mechanisms: SEO alias join and gold derived conversion."""
import json
import random
from lineage import Artifact, Revision, choose_revision, guarded_join, lineage_ready


def seo_alias_join(seed=43601, cases=2000):
    rng = random.Random(seed)
    counts = dict(cases=cases, unsafe_correct=0, guarded_correct=0,
                  unsafe_future_mappings=0, guarded_future_mappings=0)
    for _ in range(cases):
        label = rng.randrange(2)
        old_alias = rng.choice(('a', 'b'))
        future_alias = 'b' if label else 'a'
        revisions = [Revision('old', 1, 1, 0, old_alias),
                     Revision('future', 1, 11, 1, future_alias)]
        artifacts = {
            'raw_a': Artifact('raw_a', 1), 'raw_b': Artifact('raw_b', 1),
            'map_old': Artifact('map_old', 1),
            'map_future': Artifact('map_future', 11),
            'join_old': Artifact('join_old', 2, ('raw_a', 'raw_b', 'map_old')),
            'join_future': Artifact('join_future', 2, ('raw_a', 'raw_b', 'map_future')),
        }
        unsafe = choose_revision(revisions, 10, enforce_capture=False)
        safe_alias = guarded_join(revisions, artifacts, 10)
        assert safe_alias is not None
        counts['unsafe_correct'] += int((unsafe.selected_alias == 'b') == label)
        counts['guarded_correct'] += int((safe_alias == 'b') == label)
        counts['unsafe_future_mappings'] += int(unsafe.revision_id == 'future')
        counts['guarded_future_mappings'] += int(safe_alias != old_alias)
    counts['unsafe_accuracy'] = round(counts['unsafe_correct']/cases, 4)
    counts['guarded_accuracy'] = round(counts['guarded_correct']/cases, 4)
    return counts


def gold_derived_conversion(seed=43602, cases=2000):
    rng = random.Random(seed)
    counts = dict(cases=cases, naive_correct=0, early_fallback_correct=0,
                  late_dependency_rejected=0, early_fallback_accepted=0)
    for _ in range(cases):
        # Old price series is historical, but conversion coefficient for a
        # derived feature is first observed AFTER the decision cutoff.
        # Synthetic future coefficient is adversarially set to the label.
        label = rng.randrange(2)
        old_conversion = rng.randrange(2)
        late_conversion = label
        nodes = {
            'price': Artifact('price', 1),
            'fx_old': Artifact('fx_old', 1),
            'fx_future': Artifact('fx_future', 11),
            'derived_old': Artifact('derived_old', 2, ('price', 'fx_old')),
            'derived_latest': Artifact('derived_latest', 2, ('price', 'fx_future')),
        }
        ready_latest, _ = lineage_ready(nodes, 'derived_latest', 10)
        ready_old, _ = lineage_ready(nodes, 'derived_old', 10)
        counts['naive_correct'] += int(late_conversion == label)
        counts['early_fallback_correct'] += int(old_conversion == label)
        counts['late_dependency_rejected'] += int(not ready_latest)
        counts['early_fallback_accepted'] += int(ready_old)
    counts['naive_accuracy'] = round(counts['naive_correct']/cases, 4)
    counts['early_fallback_accuracy'] = round(counts['early_fallback_correct']/cases, 4)
    return counts


def main():
    results = {'seo_alias_join': seo_alias_join(), 'gold_derived_conversion': gold_derived_conversion()}
    print(json.dumps(results, indent=2, sort_keys=True))
    with open('results.json', 'w', encoding='utf8') as f:
        json.dump(results, f, indent=2, sort_keys=True)
        f.write('\n')


if __name__ == '__main__':
    main()
