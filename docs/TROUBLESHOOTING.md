# Troubleshooting — AI Governance Add-on for Splunk

## First checks

1. **Input logs**:
   `index=_internal source=*ta_ai_governance* (ERROR OR WARN)`
   Each input logs start/end, ingested counts and full exceptions.
2. **Data arriving?** `| tstats count where index=<your index> by sourcetype`
3. **Collection health panel**: AI Governance Overview → "Data Collection
   Health" shows minutes since the last event per sourcetype.
4. Raise verbosity: Configuration → Logging → DEBUG (revert to INFO after).

## Common issues

| Symptom | Cause / fix |
|---|---|
| `Account 'X' has provider 'Y' but this input requires provider 'Z'` | Input bound to wrong account — select an account whose provider matches the input type. |
| `missing required credential field(s)` | Account saved while fields were hidden — edit the account, re-select the provider and fill all shown fields. |
| HTTP 401/403 (Anthropic) | Key is not an admin/compliance key, or Compliance API not enabled on your plan. Verify scope `read:compliance_activities` / `read:analytics`. |
| HTTP 401 (OpenAI) | Key is a project key, not an **Admin** key (`sk-admin-…`), or missing `api.audit_logs.read`. |
| `invalid_grant` (Google) | Refresh token revoked/expired (password change, admin disabled, 7-day expiry on "Testing" OAuth consent screens — publish the app to Production). Re-authorize and paste a new refresh token. |
| `AADSTS700016` / `AADSTS7000215` (Microsoft) | Wrong tenant/client ID or expired client secret — create a new secret. |
| `Authorization_RequestDenied` (Microsoft) | Application permissions granted but **admin consent** missing, or wrong permission type (delegated instead of application). |
| Copilot audit input logs "still running" for many cycles | Normal: Graph audit queries are asynchronous and can take tens of minutes for large windows. If stuck >24 h, delete the checkpoint (below) to force a fresh query. |
| Dashboards empty but data exists | `aigov_index` macro still `index=*` restricted by role, or events in an index the role can't search. Point the macro at the right index. |
| Duplicate events after re-enabling an input | Checkpoint was cleared; overlap with `backfill_days`. Dedup on provider event `id` if needed. |
| No events on an SHC member | Expected — inputs should run on one collection node; checkpoints are per-instance KV Store. |
| `KV Store initialization failed` | KV Store disabled on the collection node (common on HFs with `kvstore disabled=true`). Enable KV Store or run inputs on the SH tier. |
| Proxy errors (`Network error`) | Verify per-account Proxy URL, and that the proxy allows CONNECT to the provider hosts on 443. |
| `Only HTTPS endpoints are supported` (self-hosted) | The account's base URL is `http://` but the "Allow plain HTTP" checkbox is off. Prefer TLS; enable the checkbox only for trusted lab networks. |
| Self-hosted metrics empty | Server type has no Prometheus endpoint (generic/Ollama), wrong `metrics_path`, or `metrics_prefixes` doesn't match the server's metric names — check `curl <base>/metrics`. |
| Spurious `model_removed` events | The server briefly served an empty model list (restart). Events resume as `model_added` next cycle; correlate with the health sourcetype. |

## Resetting a checkpoint (re-collect or unstick)

```spl
| inputlookup ta_ai_governance_checkpoints_lookup
```
is not shipped; use the KV Store REST API instead:

```bash
# list checkpoints
curl -k -u admin:*** https://localhost:8089/servicesNS/nobody/TA-ai-governance/storage/collections/data/ta_ai_governance_checkpoints
# delete one (key = URL-encoded input stanza, e.g. openai_audit:my_input)
curl -k -u admin:*** -X DELETE https://localhost:8089/servicesNS/nobody/TA-ai-governance/storage/collections/data/ta_ai_governance_checkpoints/<key>
```

The next run re-collects from `backfill_days`.

## Getting help

- Review logs at DEBUG and the relevant provider's API status page.
- Open an issue with: add-on version, Splunk version/topology, input type,
  sanitized ERROR lines (never include API keys or tokens).
