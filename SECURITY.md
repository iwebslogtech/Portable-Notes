# Security Policy

## Reporting

Please do not disclose a vulnerability publicly before a fix is available. Report it through GitHub private vulnerability reporting, if enabled, or contact the repository owner privately. Include reproduction steps and affected versions.

## Scope

Portable Notes Web binds to `127.0.0.1` by default. Do not change it to `0.0.0.0` without adding authentication, CSRF controls, stricter validation, TLS through a trusted reverse proxy, and a deployment security review. Keep Python updated and back up `data/notes.db`.
