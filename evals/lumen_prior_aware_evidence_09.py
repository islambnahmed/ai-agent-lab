"""Lumen experiment 09: prior-aware evidence can resolve noisy streams.

Previous experiments established an identifiability limit: without assumptions,
an alternating old/new stream cannot reveal whether the world changed or labels
are corrupted. Here we make the missing assumption explicit.

For one key, compare two hypotheses:
H0: old rule is still true.
H1: rule flipped persistently.
Observed labels are independently corrupted with known noise probability q < .5.

Maintain only one scalar: log posterior odds for H1 versus H0. Each observation
adds a constant log-likelihood increment. This is constant-memory sequential
Bayesian evidence, not stored history.

Important: perfectly balanced old/new evidence remains ambiguous. A persistent
shift observed through sub-50% noise produces positive drift; an unchanged rule
produces negative drift. The experiment tests both and a near-boundary case.
"""
import math


class LogOddsDetector:
    def __init__(self, noise=0.2, prior_shift=0.1):
        assert 0 < noise < 0.5
        assert 0 < prior_shift < 1
        self.noise = noise
        self.log_odds = math.log(prior_shift / (1 - prior_shift))
        self.step = math.log((1 - noise) / noise)

    def observe(self, contradicts_old):
        self.log_odds += self.step if contradicts_old else -self.step

    @property
    def shift_probability(self):
        odds = math.exp(self.log_odds)
        return odds / (1 + odds)

    @property
    def choose_shift(self):
        return self.log_odds > 0


def run(bits, noise=0.2, prior_shift=0.1):
    d = LogOddsDetector(noise=noise, prior_shift=prior_shift)
    for bit in bits:
        d.observe(bit)
    return d


def main():
    # 8 contradictions / 2 agreements: plausible persistent shift through 20% noise.
    shifted = run([1, 1, 0, 1, 1, 1, 0, 1, 1, 1])
    # Mirror image: unchanged rule with occasional corrupt observations.
    stable = run([0, 0, 1, 0, 0, 0, 1, 0, 0, 0])
    assert shifted.choose_shift
    assert not stable.choose_shift
    assert shifted.shift_probability > 0.99
    assert stable.shift_probability < 0.001

    # Balanced evidence cannot overcome the explicit prior: the likelihood ratio
    # cancels exactly, preserving the prior rather than inventing information.
    balanced = run([1, 0] * 5)
    assert math.isclose(balanced.shift_probability, 0.1, rel_tol=1e-12)
    assert not balanced.choose_shift

    # Same observations, different noise assumptions => different confidence.
    # This is deliberate: experiment 08 showed an assumption is unavoidable.
    low_noise = run([1, 1, 0, 1], noise=0.1)
    high_noise = run([1, 1, 0, 1], noise=0.4)
    assert low_noise.shift_probability > high_noise.shift_probability

    print(f"shift_p={shifted.shift_probability:.6f}")
    print(f"stable_p={stable.shift_probability:.6f}")
    print(f"balanced_p={balanced.shift_probability:.6f}")
    print("memory=one_log_odds_scalar_per_key")
    print("lesson=priors make ambiguity explicit; evidence drift resolves only identifiable streams")


if __name__ == "__main__":
    main()
