# Retrom Web embedding

The fork maintains upstream `master` separately from `retrom/ge46d1642fb67`.
Work on `feat/*`, `fix/*`, or `build/*` branches derived from that maintenance baseline.
No core or runtime release is implied by a local candidate build.

The `ruffle-host-v1` ABI adds `hostStorage` to load options. This synchronous,
instance-owned backend receives SharedObject binary data through `get`, `put`,
and `remove`. It replaces browser localStorage entirely for that instance. The
host must enforce limits and provide stable SWF identity across restore sessions.
`put` returns false on quota failure. Stored bytes represent native game saves,
not emulator save states. A fresh session receives an empty backend; restore
bytes must be installed before loading the SWF.

`player.ruffle().hostAbi` identifies the ABI and `getCanvas()` exposes the current
render surface for host layout. `captureFrame()` re-renders without advancing the
movie, then captures PNG bytes before GPU presentation invalidates the surface.
`destroy()` explicitly disposes a late load after cancellation. `hostMovieUrl`
on data load options sets an absolute HTTP(S), credential/query/fragment-free movie
identity; it is never fetched. Script access remains disabled
for Retrom content. The host controls teardown by removing the player element.

Build explicitly with `.github/rpg-runtime/build-candidate.sh /absolute/empty/output`.
The recipe pins Rust, Node and wasm-bindgen; compilation runs as the invoking user.
Only the Web core and selfhosted package are built. Artifacts and dependencies
stay in the worktree; the output contains a strict inventory and SHA-256 hashes.
The fixed runtime file names are `ruffle.js`, `core.ruffle.js`, and `ruffle.wasm`.
Upstream license documents accompany the candidate.

## Maintenance releases

PRs target `retrom/ge46d1642fb67`, never the upstream mirror. The Retrom Web
Quality workflow builds the same candidate recipe and checks the Web types,
core unit tests, changed TypeScript lint and changed Rust formatting. It does
not replace the host application's controller/save/restore acceptance tests.

After a verified PR is merged, create an annotated tag
`retrom-core-ge46d1642fb67-r<N>` (or `-rc.<N>`). The release workflow rejects
lightweight tags, commits outside the maintenance lineage, dirty candidates,
unexpected files and hash mismatches. It publishes exactly the three Web
assets, three licenses and `rpg-runtime-release.json`; candidates are never
published as runtime Provider archives. Existing tags/assets must not be moved.
Runtime consumers lock the repository, tag, commit and `ruffle-host-v1` ABI.

The fork build sets `SOURCE_DATE_EPOCH` to the source commit timestamp so the
embedded build date does not change between local and CI builds of that commit.
Upstream builds without this environment variable keep their original behavior.
Rust source paths (including the fork-owned Cargo cache) are remapped to `/ruffle`
to avoid embedding the builder's checkout path in published Wasm panic locations.
