# Keystone cycle 121: duplicate receipt guard

Synthetic regression against the Cycle 120 local proof-aware settlement module: two unique horizon-1 receipts with model errors 10 and 30 have descriptive MAE 20. Copying the lower-error receipt three additional times changed the original implementation's MAE to 14. A conflicting record with the same receipt id also changed the result. This is evidence inflation, not actual market performance.

Local corrective implementation groups by receipt id, ignores identical copies, and quarantines all records with conflicting versions of an id. Verified prospective metrics remain null absent external publication and vendor first-availability proof.

Node.js 22.16.0: 18/18 unit tests passed, including 1,000 seeded duplicate/permutation trials. No live gold data or verified predictive skill. Integration and full repository CI are not yet complete.
