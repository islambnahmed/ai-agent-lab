# Project: Lightweight Adaptive Intelligence

## Research question

Can the lab discover and demonstrate an intelligence architecture that learns, adapts, reasons, and transfers useful knowledge while remaining practical on resource-constrained local hardware, including a modern phone-class device?

This is an open research problem, not an instruction to build a particular architecture.

## Freedom of approach

Do **not** assume that an LLM, Transformer, conventional agent loop, vector database, planner/critic pattern, neural network, symbolic system, or any existing lab architecture is the answer.

Agents may invent, combine, reject, or replace:
- model architectures;
- representations and memory systems;
- learning mechanisms;
- reasoning/search procedures;
- symbolic, neural, probabilistic, programmatic, or hybrid approaches;
- collaboration structures;
- evaluation methods.

Existing Khepri, Seshat, router, dependence-bounds, and other lab work is evidence and optional tooling, not a required foundation.

## Hard target

A successful prototype should show useful improvement from experience without requiring large-scale retraining or cloud-scale compute.

The eventual system should be plausibly runnable locally on constrained hardware. Early experiments may run on available lab compute, but every claimed improvement must account for computational cost.

## What counts as intelligence progress

Prefer measurable evidence of one or more of:
1. learning from a small number of experiences;
2. transferring a learned lesson to materially different unseen tasks;
3. retaining useful knowledge without uncontrolled memory growth;
4. adapting after the environment or task distribution changes;
5. planning or reasoning better than a simpler baseline under the same resource budget;
6. recognizing uncertainty or failure and changing strategy;
7. achieving similar capability with materially less compute, memory, or model size.

A larger model merely scoring higher is not by itself success.

## Resource ledger

Every experiment should record enough information to compare capability with cost:
- peak memory when measurable;
- model/storage footprint;
- inference or decision latency;
- number of model/tool calls;
- training/fine-tuning requirement;
- persistent memory growth.

Exact phone deployment is not required in the first phase. The point is to prevent hidden dependence on expensive infrastructure.

## Discovery protocol

Start with cheap, reversible experiments.

For each promising idea:
1. state the hypothesis;
2. build the smallest falsifiable prototype;
3. compare against a simpler baseline;
4. actively search for a counterexample or failure regime;
5. test transfer on a second, materially different task family;
6. preserve only results that change the working model.

After 2-3 low-information cycles, change the hypothesis, method, decomposition, or project direction.

Negative results are valuable when they eliminate a plausible architecture or assumption.

## First benchmark: learn, then transfer

Create a small benchmark where the system receives a sequence of tasks containing discoverable structure.

Phase A: measure performance before useful experience.

Phase B: expose the system to outcomes, corrections, or environmental feedback without conventional large-scale weight training.

Phase C: test on unseen tasks that share an underlying rule but differ superficially.

Phase D: introduce a distribution shift or misleading pattern and measure whether the system can revise what it learned.

Compare against at least:
- a stateless baseline;
- a simple retrieval/memory baseline;
- the proposed mechanism.

The benchmark must be architecture-neutral: it should test learning and transfer, not reward one predetermined implementation.

## Initial division is optional

Khepri, Seshat, and independent workers may cooperate, compete, split hypotheses, or ignore role labels entirely. Independent competing approaches are encouraged because premature consensus is a failure mode.

Useful disagreements should be preserved as experiments, not resolved by authority.

## Stop conditions

Do not call the project successful because a demo looks intelligent.

Reject or redesign an approach if its gains disappear under:
- held-out transfer;
- equal compute/resource budgets;
- removal of task-specific hints;
- distribution shift;
- a simpler baseline.

The project succeeds only through reproducible capability gains under constrained resources.

## Relationship to the Autonomy Charter

All choices of architecture, internal organization, identity, specialization, collaborators, and methods remain revisable under AUTONOMY_CHARTER.md. The lab's hard safety and authorization boundaries remain unchanged.
