# Connecting a repository to Baton

Enter the GitHub repository URL and your own Fine-grained Personal Access Token in Repository, then choose **Connect repository**. A token is required for public and private repositories. Baton uses it for authenticated repository access and higher API limits; GitHub limits still apply.

Create the token using [GitHub’s official instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). Choose the correct resource owner and select the repository you want to analyze. Minimum repository permissions are **Metadata: Read** and **Contents: Read**. Do not grant write, administration, Actions write or pull-request write for Baton. An organization can require approval or restrict PAT access; being a collaborator does not guarantee that GitHub permits the chosen token to access that resource.

Baton checks token acceptance separately from repository metadata and Contents-read access. A successful connection resolves the actual default-branch commit; analysis remains an explicit next step. GitHub permission headers describe endpoint requirements, not a complete list of token grants. Hidden private repositories and missing repositories can both return 404.

The token stays in tab memory and travels to Baton in X-GitHub-Token over HTTPS in production. It is never saved in browser storage, snapshots, AI context, URLs or documentation. Reload requires reentry. **Validate repository access** replaces a connected token after preflight; **Clear GitHub token** revokes the tab’s GitHub authorization while keeping nonsecret configuration. File reads use the validated credential, never the input draft. No anonymous or server-token fallback occurs.

Analysis uses an exact-commit TAR archive and authoritative Git tree to reduce individual file calls while preserving blob evidence. Downloads, decompression, inventory and selected text are bounded; unsafe or oversized archives use the existing bounded tree/content collector. Quota/auth/network failures abort without triggering an alternate collection. GitHub’s private download redirect contains a temporary grant; the PAT is not forwarded to the download host, and redirect queries are not logged or retained.

For a primary limit, wait for the displayed reset time. Secondary limits use cooldown/backoff. Baton disables premature retries and does not retry aggressively. An invalid/expired/revoked token must be replaced; changing the repository URL cannot repair its authorization.

Permission references: [Fine-grained endpoint permissions](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens), [repository archives](https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-tar).
