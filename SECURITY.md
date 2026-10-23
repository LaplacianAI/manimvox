# Security policy

## Supported versions

manimvox is in alpha. Security fixes go into the latest release only.

| Version | Supported |
|---|---|
| 0.1.x (latest) | Yes |
| Older | No |

## Report a vulnerability

Please report vulnerabilities privately, not in a public issue.

1. Open the [private reporting form](https://github.com/LaplacianAI/manimvox/security/advisories/new) (the repository's **Security** tab, then **Report a vulnerability**).
2. Describe the problem, the version, and the steps or input that show it.

The report is visible only to you and the maintainers. We will reply in the advisory, agree a fix and a disclosure date with you, and credit you in the advisory unless you prefer not to be named.

## What is in scope

manimvox runs on your machine and talks to the network only in a few places. Issues in these are especially welcome:

- **Downloads:** voice models and the `skills` installer run by `npx`. A download must ask first, unless `--yes` is given.
- **Online voices:** OpenAI and ElevenLabs keys are read from environment variables and sent only to those services.
- **Agent tools:** the tools in `manimvox.tools` and `manimvox.integrations` are pinned to a project folder; reading or writing outside it is a bug.
- **Files a project loads:** episode files are Python and run as code. Model, scan and media files are data, and must never be executed.

Vulnerabilities in a dependency (Manim, PyAV, VTK and others) should go to that project. Tell us too if manimvox should raise its minimum version.
