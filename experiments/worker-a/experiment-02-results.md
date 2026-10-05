# Experiment 02 — bounded adaptation

The preregistered recovery target was not met in a deterministic 200-seed simulation. A contradiction-reset learner reached mean full-universe accuracy 0.8525 and coverage 0.86 after four post-shift labeled observations, below the >=0.95 accuracy target. Sliding windows of widths 1–4 also stayed below target by observation four.

This failure exposes an identifiability limit in the passive-observation setup: after only four random binary examples, multiple literal hypotheses can remain observationally equivalent. The next useful test is active query selection, where the learner chooses maximally discriminative feature vectors, rather than expanding the rule library to make the benchmark easier.
