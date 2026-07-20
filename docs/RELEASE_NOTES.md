# Release notes — AI Governance Add-on for Splunk

## Version 1.0.0 (initial release)

**Release date:** TBD

### Compatibility

| | |
|---|---|
| Splunk platform | Splunk Cloud Platform (Victoria & Classic); Splunk Enterprise 9.4+, 10.x |
| Python | 3.13 (`python.required = 3.13`; source is 3.9-compatible) |
| CIM | 5.x |
| Built with | Splunk UCC framework 6.5.x, splunktaucclib 8.2, solnlib 8.1, splunk-sdk 3.0 |

### New features

- Multi-provider account management (Anthropic, OpenAI, Google Gemini,
  Microsoft 365 Copilot) with provider-specific credential forms and
  encrypted secret storage.
- Seven modular inputs:
  - `anthropic_compliance` — Compliance API activity feed + users/groups directory
  - `anthropic_analytics` — usage, cost and adoption summaries
  - `openai_audit` — organization audit logs + user directory
  - `openai_usage` — aggregated token usage + daily costs
  - `gemini_audit` — Workspace Admin SDK Reports (Gemini applications)
  - `copilot_audit` — Purview `copilotInteraction` records via Graph Audit Log Query API (async submit/poll/fetch)
  - `copilot_usage` — Microsoft 365 Copilot per-user usage reports
  - `selfhosted_monitor` — self-hosted / open-source LLM servers (Ollama,
    vLLM, LiteLLM, any OpenAI-compatible endpoint): health checks, model
    inventory with `model_added`/`model_removed` audit events, Ollama
    runtime state, Prometheus metrics
- Cross-provider normalized field model (`aigov_*`) on every event.
- Dashboards: AI Governance Overview, AI Security Audit, AI Usage & Cost
  Monitoring, AI Compliance & Directory.
- Six disabled-by-default governance/security alerts.
- CIM-tagged eventtypes (authentication, change, audit); search macros.
- SHC-safe KV Store checkpointing; per-account HTTPS proxy support;
  retry with exponential backoff and Retry-After handling.

### Known issues

- Google Gemini collection uses a delegated OAuth refresh token; if the
  authorizing admin's account is disabled, collection stops until a new
  refresh token is configured.
- Microsoft audit results arrive with Purview's inherent ingestion delay
  (typically 15–60 minutes; the input maintains a 15-minute safety lag).
- OpenAI usage/costs endpoints return aggregate buckets; per-user
  attribution is limited to what the OpenAI API exposes.
- Dashboards use the `aigov_index` macro; update it after choosing a
  custom index or panels will search `index=*`.

### Fixed issues

- N/A (initial release).

### Third-party software

| Package | Version | License |
|---|---|---|
| splunktaucclib | 8.2.x | Apache-2.0 |
| solnlib | 8.1.x | Apache-2.0 |
| splunk-sdk (Python) | 3.0.x | Apache-2.0 |
| opentelemetry-api / -sdk / -semantic-conventions | 1.44.x | Apache-2.0 |
| urllib3 | 1.26.x | MIT |
| defusedxml | 0.7.x | PSF-2.0 |
| PySocks | 1.7.x | BSD |
| sortedcontainers | 2.4.x | Apache-2.0 |
| typing_extensions | 4.16.x | PSF-2.0 |

(gRPC / protobuf binary wheels are intentionally excluded from the package;
solnlib only uses them for optional OTLP export, which this add-on does not
enable.)
