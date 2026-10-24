"""Synthetic conditional attack cases; no external writes or security-rate claims."""
import json
import random
from plan_guard import new_guard_runtime  # adds the two sibling experiment dirs
from approval_receipts import Plan, REPO, BRANCH, PREFIX, new_runtime
from identity_receipts import new_strict_runtime


class AlwaysEqualPlan(Plan):
    def __eq__(self, other):
        return True


def run(n=3000, seed=419):
    rng = random.Random(seed)
    output = {}
    for label in ('seo', 'gold'):
        for name, factory in [('original417', new_runtime), ('strict418', new_strict_runtime), ('guard419', new_guard_runtime)]:
            accepted_redirect = 0
            accepted_mutated_plan = 0
            accepted_legitimate = 0
            for i in range(n):
                issuer, executor = factory()
                approved = Plan('write', REPO, BRANCH, PREFIX + label + '_approved.txt')
                payload = rng.randbytes(rng.randrange(0, 80))
                receipt = issuer.issue(approved, payload)
                redirected = AlwaysEqualPlan('write', REPO, BRANCH, PREFIX + label + f'_redirect_{i}.txt')
                result = executor.simulate(receipt, redirected, payload)
                if result.accepted and result.simulated_action[-1] == redirected.path:
                    accepted_redirect += 1
                # Separate issued plan object mutated after issuance.
                original_plan = Plan('write', REPO, BRANCH, PREFIX + label + '_original.txt')
                changed_receipt = issuer.issue(original_plan, payload)
                object.__setattr__(original_plan, 'path', PREFIX + label + f'_changed_{i}.txt')
                mutation_result = executor.simulate(changed_receipt, original_plan, payload)
                if mutation_result.accepted and mutation_result.simulated_action[-1] == original_plan.path:
                    accepted_mutated_plan += 1
                # Fresh receipt for legitimate-control path, not reused.
                fresh = issuer.issue(approved, payload)
                if executor.simulate(fresh, approved, payload).accepted:
                    accepted_legitimate += 1
            output[f'{label}:{name}'] = {
                'attempts': n,
                'redirects_accepted': accepted_redirect,
                'mutated_plans_accepted': accepted_mutated_plan,
                'fresh_legitimate_accepted': accepted_legitimate,
            }
    return {'seed': seed, 'conditional_attacks': ['holder of genuine receipt supplies Plan subclass', 'caller can mutate originally approved Plan reference after issuance'], 'results': output}


if __name__ == '__main__':
    print(json.dumps(run(), indent=2, sort_keys=True))
