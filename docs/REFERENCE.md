# Reference — AI Governance Add-on for Splunk

## Sourcetypes

| Sourcetype | Provider | Category | Event time source |
|---|---|---|---|
| `aigov:anthropic:activity` | Anthropic | audit | `created_at` |
| `aigov:anthropic:user` | Anthropic | directory | snapshot time |
| `aigov:anthropic:group` | Anthropic | directory | snapshot time |
| `aigov:anthropic:usage` | Anthropic | usage | report date |
| `aigov:anthropic:cost` | Anthropic | cost | report date |
| `aigov:anthropic:summary` | Anthropic | summary | report date |
| `aigov:openai:audit` | OpenAI | audit | `effective_at` |
| `aigov:openai:user` | OpenAI | directory | snapshot time |
| `aigov:openai:usage` | OpenAI | usage | bucket start |
| `aigov:openai:cost` | OpenAI | cost | bucket start |
| `aigov:gemini:audit` | Google | audit | `id.time` |
| `aigov:copilot:interaction` | Microsoft | interaction/audit | `createdDateTime` |
| `aigov:copilot:usage` | Microsoft | usage | `reportRefreshDate` |
| `aigov:selfhosted:model` | Self-hosted | directory | snapshot time |
| `aigov:selfhosted:audit` | Self-hosted | audit | detection time |
| `aigov:selfhosted:metric` | Self-hosted | metrics | scrape time |
| `aigov:selfhosted:runtime` | Self-hosted | runtime | poll time |
| `aigov:selfhosted:health` | Self-hosted | health | check time |

All events are JSON (`KV_MODE = json`), search-time extraction only.

### Legacy interoperability

Events already collected by the **Anthropic Claude Enterprise Add-on**
(`anthropic:compliance:activity|user|group|organization|chat_content|file_metadata`,
`anthropic:analytics:summary|usage|cost|user_usage|user_cost|user_activity|spend_limit|spend_limit_request`)
are automatically projected into the `aigov_*` field model via search-time
`EVAL` props and are included in the `aigov_all` / `aigov_audit` /
`aigov_directory` / `aigov_usage` / `aigov_cost` macros. Dashboards and
alerts therefore work on that data without re-ingestion.

## Normalized fields (present on every event)

| Field | Values / example |
|---|---|
| `aigov_provider` | `anthropic` \| `openai` \| `gemini` \| `microsoft` |
| `aigov_product` | e.g. `OpenAI Platform` |
| `aigov_category` | `audit` \| `directory` \| `usage` \| `cost` \| `summary` \| `interaction` |
| `aigov_action` | provider event type, e.g. `api_key.created`, `user_signed_in_sso`, `CopilotInteraction` |
| `aigov_user` | actor email / UPN when available |
| `aigov_src_ip` | source IP when available |

## Search macros

| Macro | Purpose |
|---|---|
| `aigov_index` | Index scope for all content — **edit after install** (default `index=*`) |
| `aigov_all` | All add-on events |
| `aigov_audit` | Audit sourcetypes across providers |
| `aigov_directory` | Directory snapshots |
| `aigov_usage` / `aigov_cost` | Usage / cost sourcetypes |
| `aigov_signin_actions` | Sign-in action filter |
| `aigov_admin_actions` | Admin/SSO/role/domain change filter |
| `aigov_key_actions` | API key & service account lifecycle filter |
| `aigov_export_actions` | Data export / file movement filter |

## Eventtypes and CIM tags

| Eventtype | Tags |
|---|---|
| `aigov_audit_events` | `audit` |
| `aigov_authentication_events` | `authentication` |
| `aigov_admin_change_events` | `change`, `account` |
| `aigov_usage_events`, `aigov_cost_events` | — |

## Alerts (shipped disabled)

| Alert | Schedule | Notes |
|---|---|---|
| AI Governance - API Key Created or Deleted | */30 min | |
| AI Governance - Admin or SSO Configuration Change | */30 min | |
| AI Governance - Data Export Activity | */30 min | |
| AI Governance - New AI User Seen | daily 06:00 | 30-day baseline |
| AI Governance - Off-Hours Activity Spike | daily 07:00 | tune hours/threshold to your timezone |
| AI Governance - Daily Spend Threshold Exceeded | daily 08:00 | default threshold 1000 — adjust |
| AI Governance - New Self-Hosted Model Detected | */30 min | unapproved model deployments |
| AI Governance - Self-Hosted Server Down | */15 min | availability |

## Dashboards

`ai_governance_overview`, `ai_security_audit`, `ai_usage_cost`,
`ai_selfhosted`, `ai_compliance` (SimpleXML, dark/light aware) plus the
UCC data-ingestion monitoring dashboard (`dashboard`).

## Network endpoints

Allow outbound HTTPS (443) from the collection node to:

| Provider | Hosts |
|---|---|
| Anthropic | `api.anthropic.com` |
| OpenAI | `api.openai.com` |
| Google | `oauth2.googleapis.com`, `admin.googleapis.com` |
| Microsoft | `login.microsoftonline.com`, `graph.microsoft.com` |
| Self-hosted | your configured base URL(s) — HTTPS recommended; plain HTTP only via explicit per-account opt-in |

All clients enforce HTTPS with certificate verification, retry with
exponential backoff, and honor `Retry-After` on HTTP 429.

## Storage & internals

- **Checkpoints**: KV Store collection `ta_ai_governance_checkpoints`
  (SHC-safe). Keyed per input stanza.
- **Credentials**: Splunk encrypted secure storage
  (`passwords.conf` realm scoped to the add-on).
- **Logs**: `$SPLUNK_HOME/var/log/splunk/ta_ai_governance_*.log`
  (also `index=_internal source=*ta_ai_governance*`).
- **Conf files**: `ta-ai-governance_account.conf` (accounts, secrets
  masked), `ta-ai-governance_settings.conf` (logging), `inputs.conf`.

## Sizing guidance

Event volume is modest (audit/metadata, not content): typical orgs see
1k–100k events/day across providers — well under 1 GB/day of license in
almost all cases. Interval defaults are safe for provider rate limits;
`max_events_per_cycle` caps catch-up bursts after backfill.
