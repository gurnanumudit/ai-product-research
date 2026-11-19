# Provenance, attribution and redistribution limits

This release was prepared from the completed frozen study on November 19, 2026. It does not run the canonical once-only reporter, grading, generators or model requests. The only new analysis is offline numerical reproduction from already saved derived outcomes. Original sources and results remain unchanged.

## Frozen commitments

The private canonical summary's SHA256 is `3d842e5b4e47266d5c7c7eeddd726bab30cc9ff957c2ab639d5eedb1dcb58cea`. The public `reference/summary.json` preserves selected fields exactly, but omits the private per-request evidence and custody map. Its bytes and hash necessarily differ. No sanitized file is represented as the original canonical file.

The pure computation core's SHA256 is `450f05468a03eb11763edbad4f3ba128737505c88522907bb57746807e3901e2`. Twelve functions are extracted verbatim into `computation.py`; constants and standard-library imports needed by those functions are retained. The wrapper and tests are new public-release code. Original study software and this release are by Mudit Gurnani.

Generic prompt bytes retain SHA256 `ffdacccc71543ede022c14b8f5180b6533f3d8a5cb82bac0e0539eca2c71afca`. The bank manifest commitment is `dc60091860cb3f0baeb8429ab62827635e1f1f77287764eed7ee9de39b865c2f`. Additional source commitments and exact byte counts appear in `reference/PROVENANCE.json`. They use descriptive labels rather than private filesystem paths. Hashes commit to archived evidence but cannot let a public reader inspect unreleased evidence.

## Export transformation

The export selects only typed outcome, status, cost, usage and time fields. It drops original task identifiers, request/receipt/provider IDs, answer hashes, freeform grading text, raw answers and all evidence paths. Family IDs are replaced with sequential labels after sorting original canonical IDs within each of the three strata. Thus bootstrap order and all 200 matched triples survive without distributing a source-identifying task map. The four scientific comparisons use all 600 endpoints.

The separate original unresolved physical attempt retains only accounting fields. The original full charge/duration remain null. The public aggregate accounting retains historical missing values, reserves and infrastructure commitment unchanged. No invoice certainty is inferred.

## Coding sources and rights

The coding source was [BAAI/TACO at the pinned revision](https://huggingface.co/datasets/BAAI/TACO/tree/d593ed0a2becbbc952230bb89be09189bf1056dc), revision `d593ed0a2becbbc952230bb89be09189bf1056dc`. The archived dataset card was fetched November 4, 2026; its SHA256 is `4d087f7330c80401684459d8b59626d88cdfc5cd36a34c9b39a5cc7241be9b34`.

The archived card identifies Apache-2.0 dataset metadata, MIT-licensed contributions and CC BY 4.0 web-crawled content, and records unresolved rights for some origins. These are archived source statements, not a new legal clearance for individual tasks. This package therefore **does not redistribute benchmark questions, inputs, expected outputs, reference programs or source solutions**, nor claim that one blanket license covers them. It does not download or execute benchmark code. Upstream attribution and origin-specific permissions would need review before a separate raw-task release.

Authored graph and Sokoban tasks were validated under finite certificate/checker rules. This package also omits their instance text, generator code and witnesses: reproducing task generation or regrading is outside this release's scope. No official TACO score, unseen-training claim or universal solver validation is implied.

## License and practical limits

The root MIT license covers original software and original documentation; original derived numerical records are offered under the same permission to the extent the author holds rights. Third-party source rights remain with their respective owners. No third-party benchmark content or code is sublicensed here.

No credentials, provider IDs, private filesystem paths, operational receipts, owner authorization records, raw model answers or live launchers are included. The release cannot reproduce the original provider state, model outputs, independent raw-data audit, source qualification or actual invoice. Prior source-study review is recorded as a source commitment; this public export still requires the publisher's independent review before publication.

The intended article route is `/research/when-does-asking-ai-to-revise-help`, with an article publication date of Monday, November 16, 2026. The repository link label should be **Research code**, pointing to `research/luna-revision` at the eventual publication commit. No publication commit or live-link claim is invented here.
