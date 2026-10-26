# Camera Media and Photos Verification

- For repeated MP4 playback failures, compare exact sizes against 2^32-1, declared
  atom ends against EOF and moov presence. An old transfer limit is a hypothesis,
  not proof of a current APFS fault. Preserve originals and compare source/proxy
  chapter, camera and capture metadata; filenames alone cannot identify a full
  replacement, and container repair cannot recreate missing source bytes.
- An unexpectedly empty cloud inventory needs an enumeration check before being
  accepted as source absence. Distinguish available full-resolution originals,
  capped copies and low-resolution proxies in recovery reports.
- Photos supported keyword edits, original embedded metadata, indexed camera
  fields, asset dates and filesystem timestamps are separate stores/contracts.
  Inspect original availability and supported writable fields first. Preserve
  inference provenance and per-item previous values privately.
- For authorized scoped album/keyword work, Photos Apple Events may remain usable
  while the GUI is locked. Verify the current scripting dictionary and a bounded
  read; append rather than replace existing keywords, confirm readback and use
  temporary exports for visual candidate review before additions. Keep originals
  and indexed camera fields unchanged unless a separate supported workflow is
  explicitly authorized.
- Downloading/editing an iCloud original does not prove indexed or cloud metadata
  changes. Field-level indexed readback and asset/file invariants are required
  evidence, separate from iCloud synchronization. A successful historical private
  refresh transaction that left indexed fields empty remains a failed experiment;
  do not repeat unsupported database writes from this reference.
