# Durable Job Runner

A real application built on the Reliable Queue rather than another queue feature.

Initial use case:
- register named handlers;
- submit durable jobs with arguments;
- delayed execution/deduplication inherited from the queue;
- execute one job;
- retry handler failures through queue semantics.

The application immediately creates a new integration requirement: **job results**. Returning a result to the current worker is insufficient after restart. A durable job system needs persisted result/error inspection independent of the process that executed the handler.

That requirement should drive the next change rather than adding speculative queue features.
