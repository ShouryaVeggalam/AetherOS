# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 5.0.x (Nexus) | Yes |
| 2.0.x (Intelligence RC) | Security fixes on a best-effort basis |
| 1.5.x-alpha | No |
| &lt; 1.5 | No |

## Product security posture

AetherOS is a **userspace**, **read-only**, **human-in-the-loop** intelligence platform.

- It does **not** execute shell commands, install kernel modules, or escalate privileges.
- Recommendations are advice-only; operators approve any change outside AetherOS.
- Telemetry is collected via `psutil` and similar userspace APIs only.
- Plugin loading uses a deny-list sandbox; untrusted plugins must not be enabled in production.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security-sensitive reports.

Email the maintainers with:

1. Affected version / commit
2. Description of the issue and impact
3. Reproduction steps or proof-of-concept (non-destructive preferred)
4. Any suggested remediation

We aim to acknowledge reports within **72 hours** and to provide a remediation plan or status update within **14 days**.

Contact: repository owner via GitHub Security Advisories when enabled, or the email listed on the owning GitHub profile.

## Safe disclosure guidelines

- Prefer reports that do not require privileged OS mutation.
- Do not attempt to exploit AetherOS on systems you do not own.
- If a plugin or adapter can escape the sandbox, treat that as high severity.

## Non-goals

AetherOS is not responsible for securing the host OS, container runtime, or third-party foundation models used alongside CELESTRA GII integrations.
