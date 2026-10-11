# Worker A — GitHub commit witness registration canary

trial_id: worker-a-2026-10-11-1626Z-registration-canary
instrument: none
forecast_issued: false
market_data_collected: false
prediction: null
purpose: Verify GitHub's actual commit and server timestamp can serve as external first-registration evidence; do not count this as a live market forecast or model performance.
local_request_window_utc: 2026-10-11T16:26Z
verification_plan: Read this file back by commit SHA, retrieve commit metadata, compare GitHub server commit timestamp with local clock and confirm content exactly. Record caveat that commit author/committer dates can be user-supplied and are not automatically an independent trusted timestamp; GitHub API created_at of issue is server-assigned but issue contents are mutable. Preserve the actual GitHub commit SHA and verify its historical reachability separately.
