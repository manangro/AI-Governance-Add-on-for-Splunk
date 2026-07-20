# Installation — AI Governance Add-on for Splunk

## Where to install

| Splunk component | Required | Notes |
|---|---|---|
| Search heads | Yes | Dashboards, macros, eventtypes, alerts, setup UI. In SHC, deploy via the deployer. |
| Heavy forwarder / IDM / collection node | Yes | Runs the modular inputs. Needs KV Store *or* run inputs on the SH tier. |
| Indexers | Optional | No index-time transforms required; events are JSON with explicit timestamps set by the inputs. |
| Universal forwarders | No | — |

Enable inputs on **exactly one** collection node per account to avoid
duplicate ingestion (checkpoints are per-Splunk-instance KV Store).

## Splunk Cloud Platform

1. **Victoria Experience**: Apps → Find More Apps → install from
   Splunkbase, or Apps → Manage Apps → *Install app from file* (private
   app upload — the package passes cloud vetting). Inputs run on the
   search head tier automatically.
2. **Classic Experience**: install on the search head for dashboards, and
   open a support ticket to install on the IDM for data collection.
3. Verify outbound HTTPS from the collection tier to the provider
   endpoints listed in [REFERENCE.md](REFERENCE.md#network-endpoints).

## Splunk Enterprise — single instance

1. Apps → Manage Apps → *Install app from file* →
   `TA-ai-governance-<version>.tar.gz` → restart if prompted.
2. Confirm KV Store is running: `| rest /services/server/info | fields kvStoreStatus`.

## Splunk Enterprise — distributed

1. **Search head (or SHC deployer)**: install the full app. For SHC, place
   in `$SPLUNK_HOME/etc/shcluster/apps/` on the deployer and push.
2. **Heavy forwarder**: install the full app; configure accounts and
   enable inputs here.
3. **Indexers**: optional copy for sourcetype definitions (recommended for
   consistency; no restart-sensitive settings).

## Post-install (all deployments)

1. Open the app → **Configuration → AI Provider Accounts** → add accounts
   (see [CONFIGURATION.md](CONFIGURATION.md)).
2. **Inputs → Create New Input** → choose input type, account, interval,
   and target index.
3. Update the **`aigov_index` macro** (Settings → Advanced search → Search
   macros → `aigov_index`) to the index you selected, e.g.
   `index=ai_governance`.
4. Optionally enable the shipped alerts (Settings → Searches, reports, and
   alerts → filter on "AI Governance") and tune thresholds.

## Upgrading

1. Install the new version over the old one (same app ID); restart if
   prompted. Accounts, inputs and checkpoints are preserved (encrypted
   credentials live in `passwords.conf`; checkpoints in KV Store).
2. Review the release notes for new input parameters; new parameters take
   defaults without reconfiguration.

## Uninstalling

1. Disable all inputs first (stops API calls).
2. Remove the app: `$SPLUNK_HOME/etc/apps/TA-ai-governance` (or via UI /
   ACS on Cloud).
3. Optional cleanup: delete the KV Store collection
   `ta_ai_governance_checkpoints` and stored credentials for the app
   context.
