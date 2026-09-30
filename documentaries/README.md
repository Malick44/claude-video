# Documentaries

Long-form documentaries (22–28 min, 16:9) about real stories, told as faceless narration over archival footage. There is one folder per documentary. This folder is independent of the `watch` skill and of `shows/`.

Status: workspaces only. The footage search pipeline, the manifest validator and any build scripts don't exist yet. Until they do, the JSON files are filled in by hand or by an agent.

Footage search is the main loop. Each beat's visual need becomes a source request. The search returns candidate moments, an approved candidate becomes a clip with a provenance sidecar, and the clip needs a clearance record before a render can use it. Source metadata, transcripts and search indexes will live in a footage library shared across documentaries (not built yet). Decisions about *using* a clip are per documentary and live in that documentary's `09_clearance/`.

## Layout

```
documentaries/<slug>/
  manifest.json            project settings and the chapter → beat spine
  00_research/
    claims.json            every factual assertion the narration makes, with its type and evidence
    timeline.json          dated events, linked to claims and evidence
    evidence.json          registry of source documents and files (IDs, URLs, hashes, tier)
    source_requests.json   footage needed per beat: queries, candidates, status, fallback
  01_legal_docs/           court and case records (indictments, opinions, docket exports)
  02_audio_source/         third-party source audio: hearings, calls, interviews
  03_video/
    raw/                   downloaded originals, never modified
    clips/                 extracted moments, each with a .meta.json provenance sidecar
    proxies/               review and editing proxies
  04_stills/
    photos/  documents/  maps/
    restricted/            never enters git or a cloud session (see its README)
  05_graphics/
    overlays/              maps, titles and document call-outs we make
    synthetic/             anything AI-generated; each file needs a disclosure note
  06_script/               script drafts (Markdown)
  07_audio_produced/
    vo/  sfx/  music/  mix/
  08_edit/                 chapter assemblies and editor project notes
  09_clearance/
    clearance_log.json     one record per use of third-party material in this documentary
  10_output/               renders
  .cache/                  search index and embeddings (rebuildable, not committed)
```

## What goes in git

Commit only what we write: JSON and Markdown files in any numbered folder, including `.meta.json` sidecars. Media, court PDFs, license agreements, yt-dlp `.info.json` dumps and everything under `04_stills/restricted/` stay out (see [`.gitignore`](.gitignore)). Keep media on the Mac or in object storage, and point to it from `evidence.json` by path and sha256.

## How the records link

```
manifest beat ── claim_ids ──► claims.json ── evidence_ids ──► evidence.json
      │
      └── visual.request_ids ──► source_requests.json ── selected_clip_ids ──► 03_video/clips/<clip>.meta.json
                                                                        └──► 09_clearance/clearance_log.json
```

Records refer to each other by ID and never copy each other's fields. A validator (not written yet) will fail a render in any of these cases:

- A narrated claim has no `verified` entry.
- An ID points nowhere.
- A clip has no clearance record that permits delivery.
- A restricted asset is used.

## IDs

| Record | Format | Example |
|---|---|---|
| Chapter | `cNN` | `c01` |
| Beat | `cNN-bNN` | `c01-b03` |
| Claim | `CL-NNNN` | `CL-0012` |
| Evidence | `EV-NNNN` | `EV-0004` |
| Timeline event | `TL-NNNN` | `TL-0007` |
| Source request | `SR-NNNN` | `SR-0021` |
| Clearance record | `CU-NNNN` | `CU-0003` |
| Clip | set by the footage pipeline | |

## Record shapes (v0.1)

Each file holds one array, which is empty in a new workspace. Fields may change until a validator pins them.

**Chapter** (`manifest.json` → `chapters[]`):

```json
{"id": "c01", "title": "", "target_minutes": 4, "beats": []}
```

**Beat** (a chapter's `beats[]`):

```json
{
  "id": "c01-b01",
  "narration": "Text as it will be spoken.",
  "claim_ids": ["CL-0001"],
  "visual": {"kind": "archival", "request_ids": ["SR-0001"], "clip_ids": []},
  "timing": {"start_s": null, "end_s": null},
  "sfx": [],
  "notes": ""
}
```

`visual.kind` is `archival`, `still`, `document`, `map`, `graphic` or `recreation`. `timing` stays null until the final voiceover is aligned.

**Claim** (`00_research/claims.json` → `claims[]`):

```json
{
  "id": "CL-0001",
  "text": "The assertion, worded as narrated.",
  "type": "court_finding",
  "attribution": "according to court records",
  "evidence_ids": ["EV-0001", "EV-0002"],
  "status": "draft",
  "reviewed_by": null,
  "reviewed_at": null,
  "beat_ids": [],
  "notes": ""
}
```

- `type` is `court_finding`, `official_statement`, `reporting` or `allegation`.
- `status` is `draft`, `verified`, `disputed` or `cut`.
- A claim the story depends on needs two independent sources, one of them primary, before it is `verified`.
- An `allegation` is always narrated with its attribution, never as fact.

**Timeline event** (`00_research/timeline.json` → `events[]`):

```json
{"id": "TL-0001", "date": "YYYY-MM-DD", "date_precision": "day", "event": "", "claim_ids": [], "evidence_ids": [], "disputed": false}
```

`date_precision` is `day`, `month`, `year` or `approximate`.

**Evidence** (`00_research/evidence.json` → `evidence[]`):

```json
{
  "id": "EV-0001",
  "kind": "court_record",
  "title": "",
  "publisher": "",
  "url": "",
  "retrieved_at": null,
  "tier": "primary",
  "path": null,
  "sha256": null,
  "license_claim": null,
  "restricted": false,
  "notes": ""
}
```

- `kind` is `court_record`, `press_release`, `news_report`, `book`, `video`, `audio`, `photo`, `document` or `dataset`.
- `tier` is `primary` or `secondary`.
- `path` is relative to the workspace, and usually points at an uncommitted file.

**Source request** (`00_research/source_requests.json` → `requests[]`), the footage search queue:

```json
{
  "id": "SR-0001",
  "beat_ids": ["c01-b01"],
  "need": "What the shot must show.",
  "queries": [],
  "modalities": ["transcript", "visual"],
  "status": "open",
  "candidates": [],
  "selected_clip_ids": [],
  "fallback": "graphic",
  "notes": ""
}
```

- `status` is `open`, `candidates`, `approved`, `downloaded`, `cleared` or `unavailable`.
- `modalities` lists any of `metadata`, `transcript`, `visual` and `ocr`.
- `fallback` is `still`, `graphic`, `recreation` or `cut`.
- A candidate is `{"source_url", "start_ms", "end_ms", "evidence", "scores", "rights_status"}`.

**Clearance record** (`09_clearance/clearance_log.json` → `uses[]`):

```json
{
  "id": "CU-0001",
  "clip_id": "",
  "beat_ids": [],
  "source_url": "",
  "license_claim": null,
  "basis": "public_domain",
  "rights_status": "review_required",
  "permitted_use": "editorial_proxy",
  "attribution_text": null,
  "license_ref": null,
  "reviewed_by": null,
  "reviewed_at": null,
  "expires_at": null,
  "notes": ""
}
```

- `basis` is `owned`, `licensed`, `public_domain`, `creative_commons`, `fair_use_assessment` or `generated`.
- `rights_status` is `unknown`, `allowed_internal`, `allowed_export`, `review_required`, `blocked` or `expired`.
- `permitted_use` is `discovery`, `internal_analysis`, `editorial_proxy`, `delivery` or `archival`.
- A published render may only use clips whose record is `allowed_export` with `delivery`.
- A `fair_use_assessment` is a judgment about this use in this film, written out in `notes`. It does not carry over to another documentary.
