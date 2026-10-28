# INQ x5 — GameFace XP counter (experimental)

**Status: prototype; not working in-game yet.** Do not install or distribute as a finished mod. The original SkaajParadox Flash implementation was inspected only partially. Token aggregation is implemented, but there is no live Python-to-GameFace ViewModel bridge or verified hangar window registration.

## Structure (same convention as INQ Custom HPBar)

- `build.json` — package metadata and version.
- `build.py` — compile source to Python 2.7 `.pyc` and package `ZIP_STORED` `.wotmod`.
- `python/scripts/client/gui/mods/` — Python mod entry point and token counter.
- `resources/in/gui/gameface/mods/x5/X5Counter/` — GameFace HTML, JS and CSS.
- `resources/in/gui/gen_resources/tv.dictor.x5.json` — GameFace resource map.
- `.github/workflows/release.yml` — Windows GitHub Actions build, artifact, and experimental prerelease publication.

## Build

`python build.py --python27 C:/Python27/python.exe`

The GitHub workflow runs on a push of a `v*` tag or by manual `workflow_dispatch`. Release `v0.1.0-alpha.1` is explicitly experimental. **The workflow was committed but has not been run or verified.**

## Required before a usable release

1. Confirm lobby GameFace window class and registration against the game client.
2. Bind the Python token count to a real GameFace model and subscribe on JS side.
3. Update after token changes and on hangar entry; clean up subscriptions.
4. Verify full install, live display and return from battle on WoT 2.4.1.

Legacy reference: SkaajParadox x5 counter. No original binaries included.
