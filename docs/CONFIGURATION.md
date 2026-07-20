# Configuration — AI Governance Add-on for Splunk

Two steps per provider: (A) create credentials on the vendor side,
(B) add an account in the add-on and enable inputs.

---

## 1. Anthropic (Claude Enterprise)

### Vendor-side setup
1. Sign in to the Anthropic Console as an **organization admin**.
2. Settings → API keys → create an **Admin/Compliance key**
   (`sk-ant-admin…`). For the compliance activity feed and directory the
   key needs compliance scopes (Compliance API enabled for your org —
   available on Claude Enterprise plans).
3. Optional: create a second key with `read:analytics` scope for
   usage/cost analytics, or reuse the admin key if it carries the scope.

### Add-on setup
- Configuration → AI Provider Accounts → **Add** → Provider: *Anthropic*.
  Paste the Admin/Compliance key (and optional Analytics key).
- Inputs to create:

| Input | Collects | Key parameters |
|---|---|---|
| **Anthropic Compliance Activity Feed** | Audit events; optional users/groups snapshots (12 h cadence) | `backfill_days` (≤180), `max_events_per_cycle`, `collect_directory` |
| **Anthropic Usage & Cost Analytics** | Daily usage, cost, adoption summaries | `lookback_days` (re-collects trailing days), collect toggles |

## 2. OpenAI (ChatGPT Enterprise / API Platform)

### Vendor-side setup
1. In the OpenAI platform, go to **Organization settings → Admin keys**
   (requires org Owner) and create an **Admin API key** (`sk-admin-…`).
2. Ensure the key has read access for audit logs
   (`api.audit_logs.read`), users, usage and costs.

### Add-on setup
- Add account → Provider: *OpenAI* → paste the Admin key.

| Input | Collects | Key parameters |
|---|---|---|
| **OpenAI Audit Logs** | Org audit events; optional user snapshots | `backfill_days`, `max_events_per_cycle`, `collect_users` |
| **OpenAI Usage & Costs** | Token usage buckets (grouped by model/project) and daily costs | `lookback_days`, `bucket_width` (1h/1d), collect toggles |

## 3. Google Gemini (Workspace)

### Vendor-side setup
1. In Google Cloud Console: create/select a project → **enable the Admin
   SDK API** → create an **OAuth 2.0 Client ID** (type: Web or Desktop).
2. As a **Workspace super admin** (or delegated admin with Reports
   privilege), run an OAuth consent flow for scope
   `https://www.googleapis.com/auth/admin.reports.audit.readonly` with
   `access_type=offline` and capture the **refresh token**
   (e.g. via OAuth 2.0 Playground configured with your own client, or any
   standard OAuth tooling).
3. Note your Workspace **customer ID** (Admin console → Account settings)
   or leave the default `my_customer`.

### Add-on setup
- Add account → Provider: *Google Gemini* → client ID, client secret,
  refresh token (+ optional customer ID).

| Input | Collects | Key parameters |
|---|---|---|
| **Google Gemini Audit** | Gemini activity events per application | `applications` (CSV of Reports `applicationName`s, default `gemini_in_workspace_apps`), `backfill_days` (≤180), `max_events_per_cycle` |

## 4. Microsoft 365 Copilot

### Vendor-side setup
1. Entra admin center → **App registrations → New registration** (single
   tenant). Record **Tenant ID** and **Application (client) ID**.
2. API permissions → Microsoft Graph → **Application permissions** → add
   `AuditLogsQuery.Read.All` (Copilot interaction audit) and
   `Reports.Read.All` (usage reports) → **Grant admin consent**.
3. Certificates & secrets → create a **client secret**; record the value.
4. Ensure Microsoft Purview auditing is on (default for M365 E3/E5).

### Add-on setup
- Add account → Provider: *Microsoft 365 Copilot* → tenant ID, client ID,
  client secret.

| Input | Collects | Key parameters |
|---|---|---|
| **Microsoft 365 Copilot Audit** | `copilotInteraction` (extensible via `record_types`) audit records | `backfill_days`; the Graph audit query is **asynchronous** — one cycle submits a query, later cycles fetch results; keep interval ≥ 15 min |
| **Microsoft 365 Copilot Usage** | Per-user Copilot usage report | `period` (D7/D30/D90/D180); dedupes on `reportRefreshDate` |

## 5. Self-hosted / Open-source models (Ollama, vLLM, LiteLLM, OpenAI-compatible)

### Server-side setup
1. Any server exposing the OpenAI-compatible `/v1/models` endpoint works
   out of the box (vLLM, LiteLLM proxy, llama.cpp server, TGI with the
   OpenAI shim). Ollama is supported natively (`/api/tags`, `/api/ps`).
2. Strongly recommended: front the server with TLS and authentication
   (vLLM `--api-key`, LiteLLM master key, or a reverse proxy). Plain HTTP
   is possible only behind an explicit opt-in checkbox and is intended
   for lab networks; Splunk Cloud deployments should always use HTTPS.
3. For metrics, ensure the Prometheus endpoint is enabled (vLLM and
   LiteLLM expose `/metrics` by default).

### Add-on setup
- Add account → Provider: *Self-hosted / Open-source* → base URL, server
  type (Generic OpenAI-compatible / vLLM / Ollama / LiteLLM), optional
  bearer token, optional plain-HTTP opt-in.

| Input | Collects | Key parameters |
|---|---|---|
| **Self-Hosted Model Monitor** | Health checks (latency, up/down), model inventory snapshots (12 h cadence) **plus immediate `model_added` / `model_removed` audit events**, Ollama loaded-model state, Prometheus request/token metrics | `collect_models`, `collect_metrics`, `metrics_path` (default `/metrics`), `metrics_prefixes` (default `vllm:,litellm_,ollama_`), `collect_runtime` |

Governance tips:
- Enable the **"AI Governance - New Self-Hosted Model Detected"** alert to
  catch unapproved open-source model deployments.
- Enable **"AI Governance - Self-Hosted Server Down"** for availability.
- One account + input per server; use multiple accounts to cover a fleet.

---

## Common settings

- **Index**: choose a dedicated index (e.g. `ai_governance`) on each
  input, then set the `aigov_index` macro accordingly.
- **Proxy**: each account has an optional `Proxy URL`
  (`http://host:port`) applied to that account's outbound calls.
- **Logging**: Configuration → Logging → set level (INFO default).
  Logs land in `$SPLUNK_HOME/var/log/splunk/ta_ai_governance_*.log`
  and are searchable via `index=_internal source=*ta_ai_governance*`.
- **Least privilege**: create credentials with read-only/audit scopes
  only; never use interactive user API keys.
- **Rotation**: when rotating vendor credentials, edit the account —
  inputs pick up new secrets on the next run; checkpoints are unaffected.
