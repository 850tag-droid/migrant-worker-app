---
name: persistent-computing
description: "MUST read when user needs to run persistent services that WebDev or the default sandbox may not support (automation scripts, game servers, self-hosted open-source apps), or requires Docker, fixed IP, background jobs, heavy compute, or a reusable environment across sessions. MUST also read before deploying a resource-intensive service to an attached persistent VM. Guides persistent computing solutions vs sandbox vs WebDev."
---

# Persistent Computing

## When This Skill Applies

The default sandbox hibernates when inactive and cannot run long-lived processes. A persistent computing solution is needed for:

- **Always-on services**: websites/web apps, bots, game servers, VPN, monitoring
- **Self-hosted platforms**: WordPress, n8n, Gitea, Metabase, Dify, code-server
- **Docker or custom runtimes**
- **Scheduled/background jobs**: cron, parallel crawlers, task queues, data pipelines
- **Heavy or long-running compute**: large dataset processing, batch transcoding
- **Reusable environment**: pre-configured dev setup with databases, libraries, and local data that persists across sessions
- **Fixed IP**: webhook endpoints, DNS records, firewall allowlists

## The Default Option: Manus WebDev

WebDev is a managed hosting platform for websites (Vite + React + TypeScript + TailwindCSS) and mobile apps (React Native + Expo), with an optional backend (TypeScript + Express + tRPC, Drizzle/MySQL, Manus OAuth, and integrated APIs). It provides one-click publish with TLS on a subdomain of `manus.space` (or a user-owned custom domain), zero-ops hosting, access control for restricting who can view the site, and built-in SEO, checkpoint/rollback, and cron jobs. Free to start; usage-based billing at higher volumes.

**Limitations:** The backend runs on Cloud Run — stateless, with a 15-minute per-request timeout and cold starts after inactivity. Cron jobs are also subject to this timeout. Each pod gets 1 vCPU + 512 MB RAM (auto-scales up to 5 pods), so it is not suited for heavy compute.

Users may not explicitly ask for a "website" — requests to build a tool or workflow often fit WebDev if they need a GUI-based, low-barrier, universally accessible solution.


**IMPORTANT - If the user's project requires connectors:** User-configured connectors (MCP services, external API integrations) are not available by default in WebDev, cloud computers, or local computers. You MUST read `references/work-with-connectors.md` to understand the available solutions and choose the right approach for the use case.

## Non-WebDev Solutions

### Option A: Cloud Computer (Persistent Sandbox)

A managed persistent Ubuntu Server VM provided by Manus. Same tooling as the default sandbox (`shell` with prefixed session, FUSE mount at `/mnt/`), but state and installed software survive across sessions.

**Best for:** turnkey always-on server, full root access, services that run independently of Manus sessions

**Capabilities:** full root, any software, Docker, fixed external IP, persistent filesystem, cron, systemd. Ubuntu Server 24.04 LTS, no desktop by default (can be installed manually). No GPU on any tier.

**Pricing:** starts at $10/month (Basic).

**Environment configuration:** When an `agents.md` file is present in the cloud computer's home directory (`/home/ubuntu/agents.md`), Manus automatically reads it for all Tasks using that cloud computer. Configuration, directory structure, and other environment-related information stored there will be available across sessions without needing to repeat setup instructions.

**IMPORTANT:** You MUST read `references/cloud-computer-reference.md` before producing any reply that recommends a Cloud Computer purchase, suggests an upgrade, evaluates whether the attached cloud computer's resources are sufficient, or otherwise discusses Cloud Computer plans, tiers, or links. It contains the mandatory purchase and upgrade links, tier comparisons, and critical operational rules (UFW, auto-restart, traffic limits) required to deploy services successfully.

Do not redirect product-level questions about Cloud Computer, the desktop client, or built-in domains to the help center; answer them inline. The help center is only for disputed charges, refunds, failed payments, invoices, credits-balance issues, or system faults on Manus's side.

### Option B: My Computer (Local Desktop)

User connects their own machine via the Manus desktop client. Same tooling (`shell` with `desktop:` prefixed session, FUSE mount at `/mnt/desktop/`). When the selected local directory contains an `agents.md` file in its root path, Manus automatically reads it.

**Best for:** zero extra cost, leveraging existing hardware/data, data-sensitive scenarios

**Limitations:** machine must stay online during session, AI scope limited to mounted directories

**User action:** Download at [manus.im/desktop](https://manus.im/desktop), install, and connect

### Option C: Third-Party Cloud Services

For advanced users with existing cloud accounts or production-grade needs, third-party cloud services are also a viable option.

## Decision Logic

1. **Anything WebDev can support and user has no special request** → WebDev (free, managed)
2. **Persistent compute + user has a local machine?** → Option B as zero-cost path
3. **Always-on server independent of user's machine?** → Option A
4. **Advanced user with platform preferences?** → Option C

When recommending Option A, always mention the cost so the user can make an informed decision. Never push a paid solution without explaining free alternatives first.

## Migrating from WebDev

If a WebDev project hits limits (complex background workers, Docker, non-Node runtimes, parallel task queues):

1. Explain what specifically cannot be done within WebDev
2. Present the options above
3. Help migrate code/config if the user chooses a different solution
