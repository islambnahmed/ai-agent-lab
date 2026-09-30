# Reliable Queue — ChatGPT Peer project 001

## Product goal
Build a small local persistent task queue and evolve it under real reliability requirements. This is a software project, not an experiment counter.

## v0.1 implemented
- persistent JSON state
- atomic replace on writes
- add / claim / complete / fail lifecycle
- retry delay
- max attempts and dead-task state
- reload after process restart
- standard-library only

## Known engineering problem already exposed
A process can crash **after claim but before complete/fail**. The task remains `running` forever. Persistence alone therefore creates a new liveness bug.

The next version should solve this with a lease/visibility timeout rather than simply resetting every running task on startup, because immediate reset can duplicate genuinely active work in multi-worker use.

## Current status
Source and test scenario are committed. Runtime PASS is not claimed until the repository code is actually executed.
