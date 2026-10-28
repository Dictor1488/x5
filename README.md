# x5 — World of Tanks ×5 XP counter (GameFace prototype)

Work-in-progress rewrite of the legacy SkaajParadox `me.sky.x5counter_1.0.2.wotmod` using a GameFace UI instead of Flash/SWF.

## Status: NOT installable yet

The token aggregation code is implemented, and a basic GameFace overlay is authored, **but the Python → GameFace live ViewModel data bridge is not implemented**. The widget therefore displays `—` instead of a number. The hook and injection API have not been validated in WoT 2.4.1. Do not distribute this as a working `.wotmod`.

## Source investigation

The supplied original archive contains Python 2.7 bytecode and a legacy SWF. The bytecode references `battle_bonus_x5`, `IItemsCache`, `getTokens`, `count`, and `expire`. Complete original source was not recovered. This repository is a new implementation based on those limited observations.

## Structure

- `src/x5_counter.py` — sums active, non-expired x5 token quantities; Python 2.7-compatible.
- `src/mod_x5.py` — initial RandomHangar hook and GameFace injection concept. **Unverified**.
- `res/gui/gameface/mods/x5/x5.js` and `x5.css` — small ×5 widget, waiting for a live data bridge.
- `tests/test_counter.py` — token counting unit tests.

## Outstanding

1. Confirm target client API, lobby/hangar lifecycle and OpenWG `gf_mod_inject` integration.
2. Create an actual GameFace model field for the count and subscribe to it in JS.
3. Trigger refresh on inventory updates, hangar entry and post-battle return.
4. Handle teardown and error recovery.
5. Compile for the WoT Python runtime and build/test a real `.wotmod`.

## Tests

```bash
python -m unittest discover -s tests -v
```

Legacy reference: SkaajParadox. No original SWF or binary redistribution.
