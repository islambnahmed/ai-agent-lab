# Catoni robustness to second-moment misspecification

## Question

Suppose the conditional null mean remains correct,
E[X_t | F_{t-1}] <= 0,
but the advertised conditional second-moment bound M2 is occasionally too small. Does the Catoni e-process degrade gracefully?

## Exact one-step sensitivity

For the Catoni factor

e_t = exp(phi(lambda_t X_t) - lambda_t^2 M2/2),

the same envelope used in the valid construction gives

E[e_t | F_{t-1}]
<= exp(-lambda_t^2 M2/2)
   (1 + lambda_t^2 V_t/2),

where V_t = E[X_t^2 | F_{t-1}].

Using 1+x <= exp(x),

E[e_t | F_{t-1}]
<= exp(lambda_t^2 (V_t-M2)/2).

Therefore a rare bound violation is not governed by its frequency alone. Its relevant quantity is the predictable excess second moment

d_t = (V_t-M2)_+.

A rare but arbitrarily large d_t can destroy any fixed nominal validity guarantee.

## Repair with an excess-moment budget

If before observing X_t we have a predictable allowance c_t >= d_t, define

e_t^robust =
exp(phi(lambda_t X_t)
    - lambda_t^2 (M2+c_t)/2).

Then E[e_t^robust | F_{t-1}] <= 1, so the product remains an e-process.

More generally, if only a predictable cumulative budget C_t is known with
sum_{s<=t} lambda_s^2 d_s <= C_t
pathwise, then multiplying the original product by exp(-C_t/2) restores the corresponding supermartingale bound when the compensation is implemented predictably/incrementally.

This gives a useful engineering interpretation: misspecification has an evidence debt of roughly

(1/2) sum_t lambda_t^2 d_t

in log-evidence units.

## Why "1% bad steps" is insufficient

A frequency statement such as "the M2 bound fails on at most 1% of steps" says nothing about the magnitude of V_t on those steps. One bad step can have enormous conditional second moment and arbitrarily large one-step inflation. Robustness therefore requires a magnitude budget, a stronger tail model, or an explicit contamination model—not just a violation count.

## Concrete stress test

Use a null martingale-difference process. On ordinary steps let X_t be symmetric +/-1. On designated contamination steps let X_t be symmetric +/-H, so the conditional mean remains exactly zero. Run the e-process pretending M2=1.

The violating step has V_t=H^2 and excess d_t=H^2-1. Sweep H and contamination spacing separately. Compare:

1. naive Catoni with M2=1;
2. compensated Catoni using the true predictable d_t;
3. conservative Catoni using a predeclared upper allowance c_t.

Prediction: false-positive inflation tracks cumulative lambda^2 d_t, not contamination frequency by itself; the compensated variants retain nominal anytime validity.

## Design consequence

The earlier latent-sign counterexample attacked conditional-mean validity. This experiment isolates a different failure mode: the conditional mean remains correct while only the moment budget is wrong. That makes it a cleaner negative control for implementations claiming robustness to rare variance spikes.

Next implementation target: add this stress test to the common benchmark and report crossing probability against cumulative misspecification debt rather than merely percent contaminated steps.
