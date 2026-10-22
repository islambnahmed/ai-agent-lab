# Keystone cycle 129 — base URL and inert template holdout

2026-10-22. Independent synthetic tests, written before implementation, found 12 failures in 14 cases on cycle-128 local candidate. Causes: relative anchors ignore the first `<base href>`; inert `<template>` content is incorrectly counted as headings, links, images and JSON-LD.

Local cumulative candidate (not deployed): blob `84e8f1359aa4ebc6242dfdc9a2b277b63c9c840b`; previous local candidate: `7d4fcc2af067581a9fa003a07814f79be054433d`. Fix tracks the first head base href and skips nested template content. Local tests: 54/54 pass, including 14/14 holdout; frozen 34-case synthetic benchmark 34/34. No live site claims. Code and tests in conversation archive `keystone_cycle129_base_template_20261022.zip`.

The repository branch auditor remains at blob `fc873d5024aad0dec8d12609e33fc7f0845f052d` until a confirmed integration. CI not run. Browser-level oracle and independent real HTML evaluation remain pending.
