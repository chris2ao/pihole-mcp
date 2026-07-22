# homenet-device-profile plan

**Date:** 2026-04-18
**Owner:** Chris (chris2ao)
**Status:** Draft (pre-build)

## Goal

Combine UniFi client data and Pi-hole DNS data into a per-device behavior profile so unknown endpoints on the home LAN can be classified, trends can be spotted over time, and DNS drift can be flagged. Scope is **device-first**: we describe what each MAC-bound endpoint does on the network, not which human uses it.

## Motivation

Today the HomeNetwork repo tracks *identity* (MAC, hostname, SSID binding) but not *behavior*. An unknown MAC on the IoT VLAN shows up in `inventory.md` as "unknown transient with hostname `HS105`", with no view of what it is actually talking to. Pi-hole holds the answer (query patterns, domains, volume) but keys by IP, which drifts with DHCP. A skill that does the join-at-query-time and writes a durable profile closes that gap.

## Non-goals

- **No human attribution.** Time-of-day + service signatures can infer which household member is using a shared device, but that is surveillance-grade on a home network. Keep it opt-in behind `--include-temporal` and never write per-user claims to the HomeNetwork repo.
- **No mutations.** This is a read/report skill. No allowlist writes, no firewall changes, no MCP tool calls that modify Pi-hole or UniFi state. If a profile suggests action (add MAC to allowlist, move to IoT VLAN), surface it as a recommendation; the existing homenet-allow-mac / homenet-filter skills remain the authoritative applyers.
- **No ML.** Classification is explicit rules over OUI + DNS-domain substrings. Deterministic, reviewable, and auditable.
- **No per-device deep packet inspection.** UniFi DPI is used at the aggregate level only; no per-flow logging.

## Skill contract

### Invocation

```
/homenet-device-profile [--window DAYS] [--device MAC] [--include-temporal] [--write] [--force]
```

| Flag | Default | Meaning |
|---|---|---|
| `--window DAYS` | `7` | Pi-hole lookback window for behavior data |
| `--device MAC` | unset | Narrow to a single device; print full detail |
| `--include-temporal` | off | Add time-of-day cadence analysis per device (opt-in for privacy) |
| `--write` | off | Persist report to `HomeNetwork/devices/device-profiles.md` (default: stdout only) |
| `--force` | off | Overwrite existing report even if HomeNetwork tree is dirty |

This is a **read-only** skill, so it inverts the preview/apply pattern used by mutating homenet-* skills: default is the safe action (stdout), and `--write` is the explicit opt-in. No `--apply` flag (nothing to apply).

### Inputs (MCP tools)

**UniFi:**
- `list_all_clients` — current snapshot: MAC, IP, hostname, vendor/OUI, SSID/network, first/last seen, RSSI, is_guest
- `get_client_history` — per-device session history (invoked only for `--device MAC`)
- `get_top_talkers` — traffic volume by client (joined as tx/rx totals)
- `get_dpi_by_app` — aggregate only (used for classification hints: "has Netflix DPI entries → likely streaming device")
- `list_mac_filter` — membership in any SSID allowlist

**Pi-hole:**
- `get_stats` — overall context
- `get_top_clients` — top N clients by query volume over window
- `get_history` — time-bucketed query counts (feeds temporal analysis if opted in)
- `get_query_log` — per-client detail (invoked only for `--device MAC` or top-N sample)
- `get_top_permitted` / `get_top_blocked` — used for global baselines (what is "normal" across the LAN)

### Join

Join key is **current IP at profile-run time**:

1. Fetch UniFi clients → in-memory table keyed by MAC with current IP, hostname, vendor, SSID, first/last seen.
2. Fetch Pi-hole client list → keyed by IP.
3. Left-join: each UniFi client gets zero or more Pi-hole query rows (zero = not active in DNS lookback).
4. Detect drift: if the same IP resolves to multiple MACs in the UniFi historical-client set across the lookback window, flag the row with `⚠ ip-drift: MAC changed during window` and skip behavioral attribution for that IP.
5. Privacy MACs (Apple randomized MACs, locally-administered bit set) are flagged but not profiled per-device; they are reported as an aggregate "privacy-mac pool on SSID X".

### Classification schema

Four orthogonal dimensions, each from a narrow rule table. Unknown on any dimension is fine and expected.

**1. Type** (narrow enum, explicit rules):
- `apple-mobile` — OUI in Apple ranges AND DNS includes `push.apple.com` / `gs-loc.apple.com`
- `apple-desktop` — Apple OUI AND DNS includes `swscan.apple.com` / `mdm.apple.com` / macOS-specific
- `android-mobile` — Google/Samsung/OnePlus OUI AND DNS includes `android.clients.google.com`
- `windows-desktop` — Dell/HP/Lenovo OUI AND DNS includes `microsoft.com` / `windowsupdate.com`
- `streaming-stick` — DNS fingerprint matches Roku / Fire TV / Apple TV / Chromecast signature
- `smart-tv` — Vizio/Samsung/LG OUI AND characteristic CDN DNS
- `smart-speaker` — Amazon/Google/Sonos OUI AND device-specific telemetry domains
- `iot-appliance` — any IoT-brand OUI + low query volume + brand-specific domain (ring.com, tplinkcloud.com, meethue.com, nest.com, ecobee.com, …)
- `camera` — UniFi Protect MAC range OR Ring/Nest/Wyze camera DNS
- `printer` — HP/Canon/Epson printer OUI AND `hpeprint.com` / printer-specific
- `network-gear` — Ubiquiti OUI or device MCP-reported
- `privacy-mac-pool` — MAC has locally-administered bit set; aggregate only
- `unclassified` — nothing matched; report top 5 domains and top OUI fields for manual labeling

**2. Trust tier** (from UniFi state):
- `allowlist-member-{ssid}` — MAC on one or more SSID allowlists
- `ppsk-holder` — MAC bound to a PPSK record
- `default-access` — connected via unrestricted SSID / wired default
- `iot-vlan` — on VLAN tagged for IoT (topology.md designates this)
- `guest` — on guest/roaming-quarantine network
- `corporate-managed` — OUI marks as corporate-issued device (Dell Technologies corporate range, etc.)

**3. Cadence** (from UniFi first/last-seen + Pi-hole active-hours):
- `continuous` — online fraction of window > 90%
- `business-hours` — activity concentrated weekday 08-18 local
- `sporadic` — online fraction 10-90%
- `dormant` — online fraction < 10%
- `offline` — not seen in current window (present in historical only)

**4. DNS behavior** (from Pi-hole):
- `volume_quintile` — 1 (lowest) to 5 (highest) by query count vs. LAN baseline
- `blocked_pct` — raw percentage
- `top_categories` — domain clusters, ranked:
  - `apple-services` (apple.com, icloud.com, mzstatic.com, apple-dns.net, apple.news)
  - `google-services` (google.com, googleapis.com, gstatic.com, doubleclick.net, 1e100.net)
  - `microsoft-services` (microsoft.com, office.com, azure.com, live.com, msedge.net)
  - `meta-services` (facebook.com, fbcdn.net, instagram.com, whatsapp.net)
  - `video-streaming` (netflix.com, youtube.com, hulu.com, disneyplus.com, prime-video.com, max.com, tiktok.com)
  - `gaming` (xboxlive.com, playstation.net, ea.com, steampowered.com, roblox.com, epicgames.com)
  - `iot-telemetry` (deviceportalservice.com, amazonaws.com with IoT brand patterns, tplinkcloud.com, meethue.com, ring.com, nest.com, ecobee.com)
  - `ads-trackers` (doubleclick.net, adservice.google.com, criteo.com, known ad-tech domains)
  - `dev-tools` (github.com, npmjs.com, pypi.org, anthropic.com, openai.com, docker.com)
  - `other` — ranked domain list if nothing clusters
- `new_domains_since_last` — set difference vs last profile run (drift signal)

### Output format

Single file: `HomeNetwork/devices/device-profiles.md`. Overwritten on each `--write` run (idempotent; the ground truth is live MCP data, not the markdown).

Structure:

```markdown
# Device Profiles

Generated: <ISO8601>
Window: <N days>  (Pi-hole lookback)
Snapshot: <unifi-snapshot-ts> (from homenet-snapshot convention)

## Summary
- Total devices observed: N (M active, K historical-only)
- Classification coverage: X% typed, Y% trust-tiered
- Flags: <count> ip-drift, <count> new-domains, <count> volume-spike

## Devices by category

### apple-mobile (count)
| MAC | Hostname | SSID | Trust | Cadence | Volume | Blocked% | Top categories | Flags |
|---|---|---|---|---|---|---|---|---|
| … | … | … | … | … | q3 | 8% | apple-services, video | — |

### streaming-stick (count)
…

### unclassified (count)
| MAC | Hostname | OUI | Top 5 domains (for labeling) |
…

## Privacy-MAC pools
Per SSID aggregate (no per-MAC attribution since addresses rotate).

## Drift (vs last run)
- MAC aa:bb:cc:… (Roku): new domains — `scribe.logs.roku.com`, `…`
- MAC dd:ee:ff:… : query volume 3.2x rolling avg

## Open questions (cross-reference to investigations.md)
- …
```

Raw join state is saved to `~/.claude/state/device-profiles/<ts>.json` (outside HomeNetwork repo) so the next run can compute drift. A symlink `last.json` points to the most recent.

### Safety / refusals

- **Read-only.** No MCP calls that mutate. Script wraps all MCP invocations in a fixed allowlist.
- **No plaintext query logs in repo.** The markdown report summarizes (top categories, counts) but never emits raw query log lines. Full query logs stay in Pi-hole.
- **Redaction pass before write.** Before touching `HomeNetwork/`, run a check that the report contains no full URLs (only registrable domains), no plaintext passwords, no PPSK keys. Refuse on match.
- **Privacy-MAC handling.** Rotating MACs are aggregated only; the report never pins a per-rotating-MAC profile because it is inherently unstable.
- **No temporal unless asked.** Default run omits time-of-day. `--include-temporal` adds cadence bins; even then, the output is per-device, not per-household-member.
- **IP-drift guard.** If IP→MAC mapping is ambiguous in the window, behavioral attribution is skipped for that IP and the row is flagged.
- **Dirty-tree refusal.** If `HomeNetwork/devices/device-profiles.md` has uncommitted changes on disk, refuse `--write` unless `--force`.

### File layout

```
~/.claude/skills/homenet-device-profile/
  SKILL.md                           # skill definition, invocation instructions
~/.claude/scripts/
  homenet-device-profile.py          # main: joins UniFi + Pi-hole, classifies, emits markdown
  device-signatures.yml              # OUI + DNS-domain → type/category rules (reviewable)
  homenet-lib.sh                     # shared (already exists); sourced for secrets + logging
~/.claude/state/device-profiles/
  <ts>.json                          # raw join per run
  last.json                          # symlink to most-recent
HomeNetwork/devices/
  device-profiles.md                 # output; also referenced from README protocol
```

Python (not bash) for the script — the join + classification is clearer in Python with dataclasses and the YAML rule file. Follow the pattern of `homenet-render-diagrams.py` which is already Python.

## Docs enrichment (HomeNetwork repo)

Two small changes to HomeNetwork to land alongside the new skill:

1. **README.md protocol block:** add a bullet under the maintenance protocol — "For behavioral/DNS analysis of any device, run `/homenet-device-profile --device <mac>` or refresh the full report with `/homenet-device-profile --write`."
2. **devices/device-profiles.md seed:** create the file with a header + placeholder summary so git tracks it; first real run overwrites it.
3. **investigations.md cross-reference:** for each open "unknown MAC" question, add a line "Profile: see `devices/device-profiles.md#mac-xxx` for behavioral fingerprint." After the first run these links become live.

No changes to `inventory.md` itself — the tier table stays identity-only. Profiles are a separate lens.

## Execution order

1. Write plan (this doc).
2. Create `~/.claude/scripts/device-signatures.yml` with initial OUI and DNS substring rules.
3. Create `~/.claude/scripts/homenet-device-profile.py`.
4. Create `~/.claude/skills/homenet-device-profile/SKILL.md`.
5. Run the skill once in stdout mode against live MCPs; sanity-check classification on known devices (Chris Mac mini, Vizio TV, UniFi APs, iPhones).
6. Iterate signatures.yml if obvious misclassifications show up.
7. Run with `--write` to populate `HomeNetwork/devices/device-profiles.md`.
8. Enrich `HomeNetwork/README.md` and `HomeNetwork/investigations.md` with cross-references.
9. Commit the HomeNetwork changes (user approves commit).
10. Save vector memory: skill built, design decisions, signature coverage, drift baseline established.

## Open design questions (pre-build)

- **Signature file ownership.** `device-signatures.yml` starts in `~/.claude/scripts/` so all projects share it. If it grows to need version control, move to `chris2ao-pihole-mcp/signatures/` and symlink. Start simple.
- **Drift baseline.** First run has no `last.json` so all drift flags are empty. Document this in the report header so it is not mistaken for "no drift detected".
- **Rate of re-run.** Not scheduled. User invokes on demand. If a cron is wanted later, add it via CronCreate — not in v1.

## What this is NOT

- Not a replacement for `homenet-document` — that one owns the full UniFi state dump. This skill owns only device-behavior analysis.
- Not a replacement for `homenet-review` — that one owns allowlist reconciliation. This skill may *inform* a review (low-DNS-volume allowlisted device = cleanup candidate) but never mutates.
- Not a SIEM. No alerting, no continuous monitoring. On-demand snapshot of current state + delta since last run.
