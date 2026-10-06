# GitHub validation audit — 2026-10-06

## Confirmed runtime evidence

- Production browser: submitted the requested URL without a token; existing Repository UI displays `GitHub request failed`.
- Production POST `https://baton-shl3.onrender.com/api/v1/github/validate-repository`: initially HTTP 404, body `{"detail":"GitHub request failed"}`. Subsequent probes returned HTTP 403 for both the requested repository and `octocat/Hello-World`. The existing deployed implementation suppresses the upstream cause of 403; permission vs rate limit cannot be determined from this body.
- Direct unauthenticated GET `https://api.github.com/repos/ghoshSG2347/No-Way-Home3`: HTTP 404, GitHub message `Not Found`, rate limit remaining 59 at the initial probe. GitHub intentionally makes nonexistent and inaccessible private repositories indistinguishable here.
- Direct request using the locally configured backend token: HTTP 401, `Bad credentials`. Local FastAPI route reproduces this and now returns `github_authentication_failure`. No credential was printed or saved in this audit.
- Direct unauthenticated public control `octocat/Hello-World`: HTTP 200.
- Production CORS allows the actual frontend origin `https://baton-sigma-six.vercel.app`. Browser receives the backend error. CORS is not the observed failure.

## End-to-end code trace

1. Repository.tsx sends the URL and optional input token to batonApi.validateRepository; existing catch displays Error.message in the existing layout. No visual change needed.
2. batonApi POSTs `{repo_url}` to `/api/v1/github/validate-repository`; the local VITE_BATON_API_URL points to `https://baton-shl3.onrender.com`. Browser reproduction confirms this deployment is failing. Vite URL is embedded at build time.
3. FastAPI route checks the optional Baton access key, parses the URL, resolves GitHub credentials and calls the existing GitHubService.repository.
4. Dependency token precedence is nonblank X-GitHub-Token, then nonblank GITHUB_TOKEN, then anonymous. Both dependency and service trim credentials. An invalid configured token therefore fails even for public repositories; it is not silently discarded.
5. URL parser yields `ghoshSG2347`, `No-Way-Home3`. Service constructs `/repos/ghoshSG2347/No-Way-Home3` against `https://api.github.com`. Authorization is `Bearer <token>` only when a token exists. These are correct.
6. BatonError handler preserves the HTTP status and now includes an optional stable error code. Existing response safety middleware remains in place.
7. Frontend preserves code/status and displays safe detail, redacting supplied credentials. Non-JSON/invalid success responses and network failures have explicit errors.

## Part 3 and deployment

Commit 135e3c3 changed GitHubService from propagating upstream messages to using `GitHub request failed` for every upstream error and transport failure. This is the confirmed diagnostic regression. Part 3 also moved the Baton access key from a public Vite environment value to memory-only workspace settings; a missing operator key can independently produce Baton HTTP 401, but the observed deployed request reached GitHub error handling (404/403).

Render blueprint has the existing uvicorn start command, health endpoint, allowed frontend origin, and server-only AI/access-key settings. It does not declare GITHUB_TOKEN; an operator may still configure it in the Render dashboard. Production dashboard settings, deployment revision, original user's browser Network capture and Render logs are unavailable in this session. Do not infer production token validity from the local .env. Current browser tooling reproduces the rendered error but does not expose response-body Network capture; response status/body above were independently reproduced by HTTP requests.

## Minimum fix

Retain existing integration and token precedence. Return fixed, safe messages and stable codes for invalid URL, GitHub authentication, permission, rate limit, inaccessible/missing repository/resource, GitHub API failure and upstream network failure. Do not echo upstream bodies, transport exception text or credentials. Keep generic Baton backend and browser network errors separate in BatonApiError. Preserve all frontend styling and leave the context generator and AI chatbot untouched.

This code cannot grant access to an inaccessible repository. Correct the URL or provide a valid token with repository access; replace the invalid local GITHUB_TOKEN through secret configuration. No secrets or live deployment settings were changed and the patch has not been deployed.

## Validation

- Backend: 218 passed. Initial run hit an existing Windows pytest temporary-directory permission issue; rerun with a unique --basetemp passed.
- New regression cases cover authentication, permission, primary/secondary rate limiting, 404, upstream 503, transport failure, malformed JSON, invalid URL and secret non-disclosure.
- Frontend typecheck: passed.
- Frontend lint: passed.
- Frontend production build: passed.
- Frontend API regression harness: 9 passed (status/code propagation, token trimming, credential redaction, network failure, non-JSON backend error and invalid success JSON).
- git diff --check: passed.
- Restored dependencies with npm ci using the unchanged lockfile; initial node_modules was missing the already-declared react-markdown package. Existing Starlette deprecation and Browserslist age warnings remain.
