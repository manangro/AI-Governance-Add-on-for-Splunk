# AI Governance Add-on for Splunk

A Splunk Cloud vetted-app-compatible add-on (`TA-ai-governance`) that gives security, compliance and platform teams one place to **monitor, govern and secure enterprise AI usage** across the four major providers:

| Provider | Data collected | Auth |
|---|---|---|
| **Anthropic** (Claude Enterprise) | Compliance API activity feed, users & groups directory, usage/cost/adoption analytics | Admin/Compliance API key (+ optional Analytics key) |
| **OpenAI** (ChatGPT Enterprise / API Platform) | Organization audit logs, user directory, aggregated token usage, daily costs | Organization Admin API key |
| **Google Gemini** (Workspace) | Gemini audit activity via Admin SDK Reports API (`gemini_in_workspace_apps`) | OAuth 2.0 client + refresh token |
| **Microsoft 365 Copilot** | Purview `copilotInteraction` audit records via Microsoft Graph Audit Log Query API, per-user Copilot usage reports | Entra app registration (client credentials) |
| **Self-hosted / Open-source** (Ollama, vLLM, LiteLLM, any OpenAI-compatible server) | Model inventory + `model_added`/`model_removed` audit events, availability & latency, Ollama runtime state, Prometheus request/token metrics | Base URL (+ optional bearer token) |

Built with the [Splunk UCC framework](https://splunk.github.io/addonfactory-ucc-generator/) — the standard toolchain for Splunk Cloud vetted apps. **AppInspect passes with 0 errors / 0 failures / 0 future-failures** for both the `cloud` and `splunk_appinspect` tag sets.

## Highlights

- **Multi-provider account management** — one Configuration page; the credential fields adapt to the selected provider. All secrets stored in Splunk encrypted secure storage.
- **Cross-provider normalization** — every event carries `aigov_provider`, `aigov_product`, `aigov_category` (audit / directory / usage / cost / interaction), `aigov_action`, `aigov_user`, `aigov_src_ip`, so one search spans all vendors.
- **Dashboards** (dark/light):
  - *AI Governance Overview* — activity by provider, active users, adoption trends, collection health
  - *AI Security Audit* — sign-ins, admin/SSO changes, API-key lifecycle, data exports, off-hours activity, shared source IPs
  - *AI Usage & Cost Monitoring* — tokens and spend by provider/model/project, Copilot per-app usage
  - *AI Compliance & Directory* — user lifecycle, role posture, inactive licensed users, shadow users
  - *Self-Hosted & Open-Source Models* — model inventory, availability/latency, Prometheus throughput, inventory-change audit
- **Ready-to-enable alerts** (shipped disabled): API key created/deleted, admin/SSO change, data export, new AI user, off-hours spike, daily spend threshold.
- **Cloud & on-prem** — SHC-safe KV Store checkpointing, `python.required = 3.13` (code also runs on 3.9 for older on-prem), HTTPS-only with cert verification, optional per-account proxy.
- **CIM hooks** — eventtypes tagged `authentication`, `change`, `audit`.
- **Works with existing Anthropic TA data** — if the Anthropic Claude Enterprise Add-on (`TA-anthropic_claude_enterprise`) is already ingesting data (`anthropic:compliance:*`, `anthropic:analytics:*` sourcetypes), search-time field mappings project those events into the `aigov_*` model so every dashboard, macro and alert works on that data too — no re-ingestion needed.

## Repository layout

```
globalConfig.json        UCC configuration (accounts, inputs, UI)
additional_packaging.py  post-build prune of optional binary deps (AArch64-safe)
package/
  app.manifest           Splunk Cloud app manifest
  bin/ai_governance/     collectors: providers/ (API clients), inputs/ (7 modular inputs)
  bin/*_helper.py        UCC input helper shims
  default/               props, macros, eventtypes, tags, savedsearches, dashboards, nav
  lib/requirements.txt   runtime libs (splunktaucclib, solnlib, splunk-sdk)
  static/                app icons
dist/                    packaged .tar.gz ready for Splunkbase / private-app upload
```

## Building from source

```bash
python3.13 -m venv .venv && . .venv/bin/activate
pip install splunk-add-on-ucc-framework splunk-appinspect
ucc-gen build --ta-version 1.0.0
ucc-gen package --path output/TA-ai-governance -o dist
splunk-appinspect inspect dist/TA-ai-governance-1.0.0.tar.gz --included-tags cloud --mode precert
```

## Installation

- **Splunk Cloud**: upload `dist/TA-ai-governance-1.0.0.tar.gz` as a private app (it passes the automated vetting checks) or install from Splunkbase once published. On Victoria, install on the search head; inputs run there. On Classic, request installation on the IDM.
- **Splunk Enterprise**: install on a search head (standalone) or on the SH tier **and** the heavy forwarder that runs the inputs (distributed). KV Store must be available where inputs run.

## Provider setup

<details>
<summary><b>Anthropic (Claude Enterprise)</b></summary>

1. In the Anthropic Console, create an **Admin/Compliance API key** (`sk-ant-admin…`) with compliance scopes (`read:compliance_activities`, directory read). Optionally a second key with `read:analytics`.
2. Add an account with provider *Anthropic*, then create **Anthropic Compliance Activity Feed** and/or **Anthropic Usage & Cost Analytics** inputs.
</details>

<details>
<summary><b>OpenAI</b></summary>

1. In the OpenAI platform (Organization settings → Admin keys), create an **Admin API key** (`sk-admin-…`) with `api.audit_logs.read` and usage/users read scopes.
2. Add an account with provider *OpenAI*, then create **OpenAI Audit Logs** and/or **OpenAI Usage & Costs** inputs.
</details>

<details>
<summary><b>Google Gemini (Workspace)</b></summary>

1. Create a Google Cloud OAuth client, enable the **Admin SDK API**, and authorize a Workspace admin for scope `https://www.googleapis.com/auth/admin.reports.audit.readonly`, capturing the **refresh token**.
2. Add an account with provider *Google Gemini* (client ID, client secret, refresh token), then create a **Google Gemini Audit** input. Additional Reports-API applications can be added as a comma-separated list.
</details>

<details>
<summary><b>Microsoft 365 Copilot</b></summary>

1. Create an Entra ID app registration; grant **application** permissions `AuditLogsQuery.Read.All` (Copilot interaction audit) and `Reports.Read.All` (usage reports) with admin consent; create a client secret. Microsoft Purview auditing must be enabled (default for M365 E3/E5).
2. Add an account with provider *Microsoft 365 Copilot*, then create **Microsoft 365 Copilot Audit** and/or **Usage** inputs. Audit queries are asynchronous on Microsoft's side — the input submits a query one cycle and retrieves results on subsequent cycles.
</details>

<details>
<summary><b>Self-hosted / Open-source models (Ollama, vLLM, LiteLLM, OpenAI-compatible)</b></summary>

1. Add an account with provider *Self-hosted / Open-source*: base URL (e.g. `https://vllm.example.com` or `https://ollama.internal:11434`), server type, and an optional bearer token (vLLM `--api-key`, LiteLLM master key). Plain HTTP is available behind an explicit opt-in for lab servers.
2. Create a **Self-Hosted Model Monitor** input. Each cycle it health-checks the server, snapshots the model inventory (emitting `model_added`/`model_removed` audit events on changes — your unapproved-model detector), collects Ollama runtime state, and scrapes Prometheus metrics (vLLM/LiteLLM) filtered by configurable prefixes.
</details>

After creating inputs, point the `aigov_index` macro (Settings → Advanced search → Search macros) at the index you chose.

## Sourcetypes

`aigov:anthropic:activity|user|group|usage|cost|summary`, `aigov:openai:audit|user|usage|cost`, `aigov:gemini:audit`, `aigov:copilot:interaction|usage`, `aigov:selfhosted:model|audit|metric|runtime|health`

## License

Apache-2.0

## Documentation

Full user and publisher docs live in [`docs/`](docs/):

- [Installation](docs/INSTALLATION.md) · [Configuration](docs/CONFIGURATION.md) · [Reference](docs/REFERENCE.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Release notes](docs/RELEASE_NOTES.md)
- [Splunkbase publishing runbook](docs/SPLUNKBASE_SUBMISSION.md) and ready-to-paste [listing copy](docs/DETAILS.md)
