# INQ x5 — WoT garage XP bonus counter

Single-Python-file garage widget for World of Tanks 2.4.x. Requires **net.openwg.gameface**.

## Architecture (rewritten)

The old floating Wulf WINDOW implementation was removed. The current implementation follows the public 14th_ua MoE Calculator garage widget:

1. Patch a hangar sub-view presenter's `_onLoading` (not `RandomHangar`).
2. Attach `openwg_gameface.gf_mod_inject` to the sub-view ViewModel; never overwrite another mod's `ModInjectModel`.
3. Add nested `x5Data` Wulf ViewModel with the token count and placement.
4. Render the widget inside the **existing garage GameFace document**, so it has no independent Wulf focus/stacking/window-position semantics.
5. Drag the widget with the **left mouse button**. Mouse handling uses document capture, client viewport coordinates and root-owned hit testing. The DOM moves during the gesture; only the final x/y + viewport dimensions are sent to Python.
6. The widget is hidden on routes other than the plain garage, using the client's lobby state machine.
7. Store the viewport-relative pinned coordinates in `mods/configs/inq/x5.json`. On resolution changes the JS rescales and clamps them.

The original standalone HTML and `gen_resources` JSON registration were deliberately removed; they are **not required** for injection into an already-registered native hangar document.

## Structure

- `python/scripts/client/gui/mods/mod_inq_x5.py` — **one Python file**
- `resources/in/gui/gameface/mods/x5/X5Counter/X5Counter.js` — OpenWG ModelObserver, DOM widget, Ctrl+drag
- `resources/in/gui/gameface/mods/x5/X5Counter/X5Counter.css` — scoped widget styling only
- `build.json`, `build.py` — package metadata and Python 2.7 .wotmod builder
- `.github/workflows/release.yml` — build and GitHub Release workflow

## Sources inspected

- [MoE Calculator garage feature notes](https://github.com/drizzer14/moe-calculator/blob/main/.claude/skills/moe-garage/SKILL.md)
- [MoE Calculator entry point](https://github.com/drizzer14/moe-calculator/blob/main/src/res/scripts/client/gui/mods/mod_moe_calculator.py)
- [MoE Calculator OpenWG bridge](https://github.com/drizzer14/moe-calculator/blob/main/src/res/scripts/client/moe_calculator/bridge/gameface_bridge.py)
- [MoE Calculator garage JS](https://github.com/drizzer14/moe-calculator/blob/main/src/res/gui/gameface/mods/14th_ua/MoECalculator/MoECalculator.js)
- Own projects: `ArmorCalculator`, `weather`, `HPBARCustom`.

## Build

`python build.py --python27 C:/Python27/python.exe`, or run the GitHub Actions workflow.

## Verification status

**Source/API implementation is grounded in working reference code, but not yet validated in an actual WoT client for this mod.** No claim of successful in-game integration is made.

If a sub-view's OpenWG injection slot is occupied by another mod, x5 yields rather than clobbering it. This may hide x5 when all candidate sub-view slots are occupied.
