# AI Governance Add-on for Splunk

*(Ready-to-paste copy for the Splunkbase "Details" tab — Markdown supported.)*

---

The **AI Governance Add-on for Splunk** gives security, compliance and
platform teams a single place to **monitor, govern and secure enterprise AI
usage** across the four major providers. It collects audit trails, user
directories, usage metrics and cost data via each vendor's official
enterprise APIs, normalizes them into a common field model, and ships
dashboards and alerts for AI governance out of the box.

## What data it collects

| Provider | Data | Interval (default) |
|---|---|---|
| **Anthropic Claude Enterprise** | Compliance API activity feed (audit), users & groups directory, usage / cost / adoption analytics | 5 min / 12 h / 24 h |
| **OpenAI** (ChatGPT Enterprise & API Platform) | Organization audit logs, user directory, aggregated token usage, daily costs | 5 min / 12 h / 24 h |
| **Google Gemini** (Workspace) | Gemini audit activity from the Admin SDK Reports API (`gemini_in_workspace_apps`, extensible) | 10 min |
| **Microsoft 365 Copilot** | Purview `copilotInteraction` audit records via the Microsoft Graph Audit Log Query API; per-user Copilot usage reports | 15 min / 24 h |
| **Self-hosted / Open-source LLMs** (Ollama, vLLM, LiteLLM, any OpenAI-compatible server) | Model inventory with `model_added`/`model_removed` audit events, availability & latency, Ollama runtime state, Prometheus request/token metrics | 5 min |

Every event carries normalized fields — `aigov_provider`, `aigov_product`,
`aigov_category` (audit / directory / usage / cost / interaction),
`aigov_action`, `aigov_user`, `aigov_src_ip` — so one search spans all
vendors.

## What's included

- **5 dashboards**: AI Governance Overview · AI Security Audit (sign-ins,
  admin/SSO changes, API-key lifecycle, data exports, off-hours activity,
  shared source IPs) · AI Usage & Cost Monitoring · Self-Hosted &
  Open-Source Models (inventory, availability, throughput, change audit)
  · AI Compliance & Directory (user lifecycle, inactive licensed users,
  shadow users)
- **8 alerts** (shipped disabled, ready to enable): API key created/deleted,
  admin or SSO configuration change, data export activity, new AI user
  seen, off-hours activity spike, daily spend threshold exceeded, new
  self-hosted model detected, self-hosted server down
- **18 sourcetypes**, eventtypes tagged for CIM (`authentication`,
  `change`, `audit`), and search macros for easy customization
- **Guided setup UI** (UCC): add provider accounts with encrypted
  credential storage, then enable inputs per data type

## Compatibility

| | |
|---|---|
| Splunk platform | Splunk Cloud Platform (Victoria & Classic), Splunk Enterprise 9.4+ / 10.x |
| Python runtime | 3.13 (`python.required = 3.13`; code is also 3.9-compatible) |
| CIM | 5.x (authentication / change / audit tags) |
| Deployment | Standalone, distributed, search head clustering (KV Store checkpointing) |
| Vendor APIs | Anthropic Admin/Compliance & Analytics APIs · OpenAI Organization APIs · Google Admin SDK Reports API · Microsoft Graph v1.0 |

## Where to install

| Splunk component | Install? | Purpose |
|---|---|---|
| Search heads | Yes | Dashboards, macros, alerts, setup UI |
| Heavy forwarder / IDM | Yes (runs the inputs) | Data collection |
| Indexers | Optional | Index-time props are not required (events are JSON with explicit timestamps) |
| Universal forwarders | No | — |

On Splunk Cloud (Victoria) install on the search head tier — inputs run
there. On Classic, request installation on the IDM.

## Prerequisites

- Admin-level API credentials for each provider you want to monitor
  (details in the Configuration guide):
  - Anthropic **Admin/Compliance API key** (`sk-ant-admin…`)
  - OpenAI **organization Admin key** (`sk-admin-…`) with
    `api.audit_logs.read` + usage scopes
  - Google Cloud **OAuth client + refresh token** authorized for
    `admin.reports.audit.readonly` by a Workspace admin
  - Microsoft **Entra app registration** with application permissions
    `AuditLogsQuery.Read.All` and `Reports.Read.All` (admin consent)
- Outbound HTTPS (443) from the collection node to:
  `api.anthropic.com`, `api.openai.com`, `oauth2.googleapis.com`,
  `admin.googleapis.com`, `login.microsoftonline.com`,
  `graph.microsoft.com` (per-account proxy supported)
- KV Store available where inputs run (checkpointing)

## Support

**Developer Supported.** Contact: <support email> · Issues:
<GitHub issues URL>. Best-effort response within 3 business days.
Documentation, source and release history: <repo/docs URL>.

## Privacy & security notes

All credentials are stored in Splunk's encrypted secure storage and are
never written to logs. All outbound connections are HTTPS with certificate
verification. The add-on collects **metadata and audit records**;
conversation content is not collected.
