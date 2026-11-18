# Source-grounded forwarding audit

This supplementary audit inspects all 607 selected definitions carrying an old structural wrapper label: 581 in the entire Beast repository and 26 in Thumbnailator. It reads the pinned source and compiler-derived declaration records without executing either library. Frozen production files, inventories, documentation and study branches remain unchanged.

## Proven case

`VectorTile.Tile.GeomType.valueOf(int)` is an explicit deprecated alias for `forNumber(int)`. Both methods are static and belong to the same declaring owner. The wrapper returns the target call directly, forwards the unchanged primitive parameter, introduces no defaults or synchronization, and has the same declared return type. The source itself documents the replacement. The verifier binds both source spans and the full file hash, verifies signature text directly, and requires the exact target to survive selection.

Applying this one proof removes that declaration from the candidate implementations. The other `valueOf(EnumValueDescriptor)` overload then becomes the selected implementation for the same qualified API. Therefore the Beast API count remains 2,787; this is a corrected implementation choice, not a reduction of one API family. Thumbnailator remains at 225. The optional proof-applied selection is saved separately and is not the frozen study inventory.

## Why the other labels do not justify deletion

Of the other 580 Beast records, 319 require Scala receiver/implicit resolution, 245 do not have the narrowly accepted single unqualified static-call body, and 16 have receiver dispatch or modifier semantics outside the proof. Thumbnailator has 18 unsupported bodies, three unresolved dispatch/modifier cases and five constructors with distinct construction contracts. These counts describe the verifier's limits, not a finding that every retained definition is nonredundant.

Examples illustrate the distinction. `RasterMetadata.allMetadata` uses mapPartitions, distinct and collect; a root invocation does not make the whole computation redundant. Java/Scala bridges transform Java RDD arguments into Scala RDDs. `ThumbnailMaker.defaultResizer` forwards to another virtual method, so this audit does not assume a unique runtime dispatch target. Constructors can delegate after converting arguments while still establishing a distinct construction interface.

## Reuse

`source_forwarding_audit.py` implements the narrow verifier. Before placing its proof in a production inventory, the registry reader must invoke this verifier against the current pinned source and compare the resulting proof. Merely trusting an arbitrary JSON forwarding claim is insufficient. Nine focused tests pass, including changed source bytes, wrong spans, transformed arguments, overloaded or missing targets, virtual dispatch, changed defaults and self-consistent but incorrect ledger types. See TEST_RESULTS.json and SUMMARY.json for exact evidence and every disposition.
