# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in starlette-admin, **please do not open a public GitHub issue.**

Instead, report it privately by emailing the maintainer or using [GitHub's private vulnerability reporting](https://github.com/jowilf/starlette-admin/security/advisories/new).

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce or a minimal proof-of-concept
- The version of starlette-admin affected
You can expect an acknowledgement within **72 hours** and a fix or mitigation plan within **14 days**, depending on complexity.

## Scope

This policy covers the `starlette-admin` package itself. Vulnerabilities in third-party dependencies (SQLAlchemy, MongoEngine, Starlette, FastAPI, etc.) should be reported to their respective maintainers.

## Security Considerations for Users

starlette-admin provides an administrative interface with full CRUD access to your data. Please follow these best practices:

- **Always enable authentication** — never expose the admin interface without it.
- **Restrict access by IP or network** when possible.
- **Use HTTPS** in production.
- **Limit admin user permissions** using the built-in authorization features.
- Keep starlette-admin and all dependencies up to date.
