# INQ x5 Counter — GameFace garage mod

Experimental World of Tanks 2.4.x mod, based on x5-token identifiers identified in the SkaajParadox legacy archive.

## Layout

- `python/scripts/client/gui/mods/mod_inq_x5.py` — the **only Python file**; token counting, hangar lifecycle, GameFace ViewModel and window management.
- `resources/in/gui/gameface/mods/x5/X5Counter/` — HTML/CSS/JS UI.
- `resources/in/gui/gen_resources/tv.dictor.x5.json` — **required** OpenWG GameFace layout registration (not user settings).
- `build.json` — **build-only** metadata (id, name, version). It is not needed at runtime and is not bundled inside the .wotmod.
- `build.py` — Python 2.7 bytecode compilation and uncompressed .wotmod packaging.
- `.github/workflows/release.yml` — experimental prerelease build workflow.

## Building

Run **GitHub → Actions → Build and prerelease INQ x5 → Run workflow**; it compiles the one Python file using Python 2.7 and publishes `me.inq.x5.wotmod` as an experimental prerelease.

For local builds: `python build.py --python27 C:/Python27/python.exe`.

## Testing

Requires compatible WoT client **and OpenWG.Gameface** to register the resource map.

1. Install the resulting `me.inq.x5.wotmod` in `mods/<game-version>/`.
2. Enter garage. Look for a small GameFace overlay showing `×5 XP` and current token count.
3. If absent, inspect `python.log` for `INQ.x5`, `Unable to install hangar hooks`, `Cannot create x5 GameFace window`, or resource registration issues.
4. Compare count with actual x5 reserves; test after return from battle.

**Unverified:** No actual client-side test has been run. The hangar class path, OpenWG availability, and token payload layout require checking against the installed client. Live refresh currently happens on creating the garage view; event-driven token changes during an already-open hangar are not implemented. The GitHub release workflow has not yet been run.

No Flash/SWF, no settings JSON, no original binary redistribution.
