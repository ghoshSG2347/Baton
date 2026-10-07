# Baton provider setup

Configure `GEMINI_API_KEY`, `GEMINI_MODEL` and `BATON_ACCESS_KEY` in the backend deployment environment. Keep the key and operator access key outside Git and frontend `VITE_*` settings. Choose a model identifier available to the configured Google account; Baton does not guess or certify a model from the presence of settings. Restart/redeploy the backend after configuration changes.

The user supplies their GitHub token through the repository form and the operator access key through workspace settings; both remain in browser memory. The GitHub token is required separately and is never replaced by a server or anonymous credential. Inspection reports safe missing-setting names, configured status and model validation status. A grounded snapshot can support context and deterministic artifacts while Gemini is unavailable.

For live acceptance, connect with a user-owned Fine-grained token granting repository Metadata: Read and Contents: Read; explicitly analyze; ask a repository question; inspect original evidence/citations; ask a follow-up with the same conversation ID and returned revision. Confirm snapshot reuse, zero repeated collection, safe errors and provider-reported usage. Configured status, HTTP 200, fixtures and mocked transport do not certify live Gemini quality or billing.

Usage Center displays numeric measurements from existing API responses. Missing provider token metadata and abandoned operations remain UNKNOWN. Reported total may include thinking tokens; no sum-based estimate or billing cost is shown. Stop cancels local waiting and remote work may finish. Rate limits require an explicit retry after the displayed delay.

Current audit: live Gemini UNVERIFIED. Production inspection on Render implementation 9f321e0 reports configured=false with all three settings missing; the inspected local configuration lacks model/operator settings. No model was guessed and no provider credential was copied to tests or browser code. `tests/phase3_runtime.py` is an explicit local-only mocked Google transport harness; it is not production application setup.
