# Baton engineering instructions

Before changing Baton, read PROJECT_CONTEXT.md and PROJECT_AUDIT.md and inspect the current Git state.

For every engineering task, update PROJECT_CONTEXT.md with verified current behavior and PROJECT_AUDIT.md with findings, fixes, executed checks and remaining limitations before the final commit. Revise obsolete statements in place. Distinguish local fixtures, actual GitHub checks and live provider/production verification. Never claim a deployed revision or live Gemini result without evidence.

Preserve the existing architecture unless the user explicitly authorizes an architectural change. Never place credentials in documentation, logs, browser storage, tests or Git.
