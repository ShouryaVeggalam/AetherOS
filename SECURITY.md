# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| **6.0.x (Horizon)** | Yes — current |
| 5.0.x (Nexus) | Yes — security fixes |
| 2.0.x (Intelligence RC) | Best-effort |
| 1.5.x-alpha / &lt; 1.5 | No |

## Product security posture

AetherOS is a **userspace**, **read-only**, **human-in-the-loop** intelligence platform.

| Guarantee | Detail |
|-----------|--------|
| No OS mutation | Does not execute shell commands, install kernel modules, or escalate privileges |
| Advice only | Recommendations never auto-apply; operators approve changes *outside* AetherOS |
| Userspace telemetry | Collected via `psutil` and similar APIs only |
| Twin sandboxes | Simulations clone snapshots; live baselines must remain unchanged |
| Cloud / K8s | Federation and twins are observational — no provision, delete, restart, or apply |
| Plugins | Deny-list sandbox; do not enable untrusted plugins in production |

## Reporting a vulnerability

**Do not** open a public GitHub issue for security-sensitive reports.

Prefer **GitHub Security Advisories** on this repository when enabled.

Otherwise email the maintainers (see the owning GitHub profile) with:

1. Affected version / commit SHA  
2. Description of the issue and impact  
3. Reproduction steps or non-destructive proof-of-concept  
4. Any suggested remediation  

We aim to:

- **Acknowledge** within **72 hours**
- Provide a **status / remediation plan** within **14 days**

## Severity heuristics (guidance)

| Severity | Examples |
|----------|----------|
| Critical | Sandbox escape enabling arbitrary code execution in host context |
| High | Twin / cloud path that mutates live infrastructure |
| Medium | Evidence fabrication that can mislead operators at scale |
| Low | Denial of service in local dashboard / import-time crash |

## Safe disclosure guidelines

- Prefer reports that do not require privileged OS mutation.
- Do not attempt to exploit AetherOS on systems you do not own.
- If a plugin or adapter can escape the sandbox, treat that as high severity.
- Do not attach production secrets; redact aggressively.

## Non-goals

AetherOS is not responsible for securing the host OS, container runtime, cloud IAM,
or third-party foundation models used alongside optional CELESTRA GII integrations.

## Thank you

Responsible disclosure keeps operators safe. We appreciate your help.
