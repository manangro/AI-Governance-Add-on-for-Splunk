# Splunkbase Publishing Runbook — AI Governance Add-on for Splunk

This is the end-to-end checklist for publishing `TA-ai-governance` on
splunkbase.splunk.com, modeled on how Splunk-supported add-ons present
themselves. Items marked ✅ are already done in this repository.

---

## 1. Understand the support tiers (what your listing can claim)

| Tier | Who can use it | What it means to users |
|---|---|---|
| **Splunk Supported** | Only apps built/maintained by Splunk | Covered by Splunk Support contracts. *Not selectable by third-party publishers.* |
| **Developer Supported** | You | You commit to being a support contact (email/portal you provide). This is the tier to choose. |
| **Community** | Anyone | No support commitment. |

➡ **Choose "Developer Supported"** and provide a monitored support email
(e.g. a team alias) plus optionally a GitHub Issues URL. Splunk-supported
TAs set the quality bar; this repo's docs mirror their structure so the
listing looks and reads like one.

## 2. Prerequisites (accounts and access)

- [ ] A splunk.com account (SSO for Splunkbase). Register the publisher
      profile at https://splunkbase.splunk.com (top-right → your profile →
      become a publisher / developer profile).
- [ ] Join the **Splunk Developer Program** (dev.splunk.com) — free; gives
      you a dev license, DAS office hours, and pre-submission help.
- [ ] Decide the **publisher name** shown on the listing (person or company).
      For company branding, have marketing sign off on name/logo usage.
- [ ] Legal review of the EULA/license. This app ships **Apache-2.0** ✅
      (`package/LICENSES/Apache-2.0.txt`, referenced from `app.manifest`).

## 3. Package readiness (technical gate)

Splunkbase runs **AppInspect** automatically on upload; Cloud
compatibility additionally runs the `cloud` tag checks ("cloud vetting").

- [x] ✅ Built with UCC (`ucc-gen build` + `ucc-gen package`)
- [x] ✅ AppInspect `splunk_appinspect` tags: 0 errors / 0 failures
- [x] ✅ AppInspect `cloud` tags (precert): 0 errors / 0 failures / 0 future-failures
- [x] ✅ `app.manifest` schema 2.0, `[id]`/`[launcher]`/`[package]` consistent,
      `check_for_updates = false`
- [x] ✅ No compiled binaries (`.so`), no `__pycache__`, no world-writable files
- [x] ✅ Credentials stored via encrypted storage only; HTTPS-only egress
- [ ] Re-run before every upload:
      ```bash
      ucc-gen build --ta-version <X.Y.Z>
      ucc-gen package --path output/TA-ai-governance -o dist
      splunk-appinspect inspect dist/TA-ai-governance-<X.Y.Z>.tar.gz --included-tags cloud --mode precert
      splunk-appinspect inspect dist/TA-ai-governance-<X.Y.Z>.tar.gz --included-tags splunk_appinspect
      ```
- [ ] **Version bump rule**: Splunkbase rejects re-uploads of the same
      version. Bump `--ta-version` (semver `X.Y.Z`) for every submission,
      including fixes to a rejected upload.
- [ ] Optional but recommended: smoke-test the exact tarball on
      **Splunk Cloud Developer Edition** (dev.splunk.com → Cloud Developer
      Edition) or a trial Splunk Cloud stack as a private app before
      submitting — this exercises the same vetting pipeline.

## 4. What to test with real credentials before going public

The add-on passed static vetting and scheme smoke tests; before v1.0.0 goes
live, verify each input against a live tenant:

- [ ] Anthropic: compliance activities + directory + analytics with a real
      `sk-ant-admin…` key
- [ ] OpenAI: audit logs + users + usage/costs with an `sk-admin-…` key
- [ ] Google: refresh-token flow and `gemini_in_workspace_apps` report
      (needs a Workspace tenant with Gemini activity)
- [ ] Microsoft: client-credential token, async audit query lifecycle
      (submit → poll → fetch), and the usage report endpoint (needs
      `AuditLogsQuery.Read.All` + `Reports.Read.All` with admin consent)
- [ ] SHC behavior: checkpoints in KV Store, only one effective collector
- [ ] Proxy path (`proxy_url`) through an egress proxy

## 5. The submission form — field-by-field (with our values)

Go to https://splunkbase.splunk.com → your profile → **Submit an app** (or
dev.splunk.com → Release apps → Submit Splunkbase apps). Provide:

| Field | Value to enter |
|---|---|
| **App package** | `dist/TA-ai-governance-1.0.0.tar.gz` |
| **App name** | AI Governance Add-on for Splunk |
| **App ID (folder)** | `TA-ai-governance` (must match package; immutable after first release) |
| **Version** | 1.0.0 (must match `app.conf`/`app.manifest`; enforced) |
| **Summary (short description)** | Monitor, govern and secure enterprise AI usage. Collects audit logs, user directories, usage and cost data from Anthropic Claude Enterprise, OpenAI, Google Gemini (Workspace) and Microsoft 365 Copilot, with security, governance and cost dashboards. |
| **Detailed description ("Details" tab)** | Paste `docs/DETAILS.md` (Markdown supported) |
| **Categories** | Security, Fraud & Compliance (primary); IT Operations; Utilities → choose up to the allowed number |
| **App type / content** | Add-on (TA); *not* visualization/SPL2 module |
| **Splunk platform compatibility** | Splunk Enterprise 9.4, 10.x; Splunk Cloud Platform (Victoria & Classic). Select all versions you actually tested. |
| **CIM compatibility** | CIM 5.x (eventtypes tagged authentication/change/audit) |
| **Products** | Splunk Enterprise, Splunk Cloud Platform |
| **Visibility** | Start **Unlisted/hidden** for a soft launch if desired, then flip to **Visible** — visibility is editable post-approval |
| **Pricing** | Free |
| **License** | Apache 2.0 — link: https://www.apache.org/licenses/LICENSE-2.0 |
| **Support tier** | **Developer Supported** |
| **Support contact / URL** | Your monitored email alias + GitHub Issues URL (e.g. https://github.com/manangro/AI-Governance-Add-on-for-Splunk/issues) |
| **Documentation URL** | The repo README / GitHub Pages, or paste docs into the listing's Details tab |
| **Release notes** | Paste the current section of `docs/RELEASE_NOTES.md` |
| **Icons** | Shipped in package (`static/appIcon.png` 36×36, `appIcon_2x.png` 72×72) ✅ — Splunkbase also lets you upload a larger listing logo; export a 512×512 PNG of the icon for the listing |
| **Screenshots** | 3–5 PNGs, ≥1280×720: each dashboard (Overview, Security Audit, Usage & Cost, Compliance) + the Accounts config page. Take them on a demo index with data loaded. |
| **Video (optional)** | 2–3 min walkthrough (YouTube link) — optional but Splunk-supported-style listings often have one |

### Repository/website prerequisites for the URLs above

- [ ] Make the GitHub repo public (or host docs elsewhere) **before**
      submission so the Documentation/Support URLs resolve.
- [ ] Tag the release in git (`v1.0.0`) and attach the same tarball to a
      GitHub Release so the artifact users get from Splunkbase matches
      source.

## 6. What happens after you click Submit

1. **Automated AppInspect** runs on the uploaded package. Failures block
   publication; you'll get a report — fix, bump version, re-upload.
2. **Cloud vetting** (`cloud` tag) determines whether the app is marked
   *Splunk Cloud compatible* and self-service installable in Splunk Cloud.
   We already pass this locally, so expect a clean pass.
3. Listing goes live (or stays hidden if you chose unlisted). There is no
   long manual review for standard add-ons; manual checks apply mainly to
   paid/licensed apps.
4. In **Manage my apps** you can then: edit metadata, upload screenshots,
   set per-release Splunk-version compatibility, view download analytics,
   respond to reviews/Q&A, and archive old releases.

## 7. Ongoing publisher obligations (Developer Supported)

- [ ] Answer support contacts within your stated SLA (put the SLA in the
      Details tab, e.g. "best effort, 3 business days").
- [ ] Watch the Splunkbase listing Q&A/reviews and GitHub Issues.
- [ ] Re-run AppInspect and re-submit when: Splunk raises Python runtime
      requirements, UCC libraries get security updates
      (`splunktaucclib`/`solnlib`), or provider APIs change.
- [ ] Keep `docs/RELEASE_NOTES.md` cumulative — Splunk-supported TAs keep
      release history per version with "New features / Fixed issues /
      Known issues / Third-party software" sections.
- [ ] Security contact: publish how to report vulnerabilities privately
      (email, not public issues).

## 8. Assets checklist (everything users see, in one place)

| Asset | Where | Status |
|---|---|---|
| Package tarball | `dist/TA-ai-governance-1.0.0.tar.gz` | ✅ |
| Listing summary + details copy | `docs/DETAILS.md` | ✅ ready to paste |
| Release notes | `docs/RELEASE_NOTES.md` | ✅ |
| Install guide | `docs/INSTALLATION.md` | ✅ |
| Configuration guide (per provider) | `docs/CONFIGURATION.md` | ✅ |
| Reference (sourcetypes, macros, alerts, endpoints) | `docs/REFERENCE.md` | ✅ |
| Troubleshooting | `docs/TROUBLESHOOTING.md` | ✅ |
| In-app icons | `package/static/` | ✅ |
| Listing logo 512×512 | export from icon | ☐ |
| Screenshots (5) | capture on demo data | ☐ |
| Support email alias | your org | ☐ |
| Public repo / docs URL | GitHub | ☐ |
| Live-tenant credential tests | §4 | ☐ |
