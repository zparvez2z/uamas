# Security Policy

## Supported Version

Security fixes are applied to the current `main` branch. Older commits and local artifacts are not maintained as supported releases.

## Reporting a Vulnerability

Do not include credentials, tokens, private product data, or exploit details in a public issue.

Use GitHub's private vulnerability reporting or a private security advisory for this repository. Include:
- the affected endpoint or component,
- the observed and expected behavior,
- reproduction steps using non-sensitive test data,
- and the potential impact.

Rotate any credential immediately if it may have been disclosed. A report does not replace credential rotation.

## Secret Handling

- Store runtime secrets in environment variables or the deployment platform's encrypted secret store.
- Never commit `.env`, database backups, model-provider tokens, administrator tokens, API tokens, or session-signing secrets.
- Use distinct values for `UAMAS_ADMIN_TOKEN`, `UAMAS_API_TOKEN`, and `UAMAS_SESSION_SECRET`.
- Use at least 32 random characters for each UAMAS security secret.
- Treat evaluation artifacts and workflow databases as potentially sensitive operational data.

## Production Requirements

Production mode requires:
- `UAMAS_ENV=production`,
- authentication secrets and explicit allowed hosts,
- secure cookies,
- TLS termination,
- restricted access to the SQLite database and backups,
- and protected operational endpoints.

The application intentionally fails startup when required production security configuration is missing or weak.

## Operational Data

Detailed workflow history is retained according to the configured retention policy. Cleanup is explicit, dry-run by default, and backed up before applied changes. Pending reviews and resolved review evidence are not deleted by the current cleanup implementation.

Review database access, backups, retention execution, and restoration should be limited to authorized operators.

## Automated Checks

CI performs:
- tracked-file secret-pattern scanning,
- Python dependency vulnerability auditing,
- unit and integration tests,
- classifier artifact compatibility checks,
- and deterministic evaluation smoke checks.

These checks reduce risk but do not replace deployment-level access control, TLS, backups, monitoring, or periodic security review.
