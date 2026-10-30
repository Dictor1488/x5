# INQ x5

Lightweight ×5 XP token counter for the default World of Tanks hangar. Requires OpenWG Gameface.

## Runtime

- `mod_inq_x5.py` mounts one Gameface `ViewComponent` in the main hangar view, following the native view lifecycle.
- `X5Counter.js` uses the OpenWG `ModelObserver` and the MARKS-style document-capture drag gesture.
- `X5Counter.css` supplies an explicit mouse hit zone and rem-based positioning.
- `tv.dictor.x5.garage.json` registers the subview. Its HTML intentionally contains no second script: the OpenWG injector loads the JS and CSS.
- Bonus count uses unexpired inventory tokens whose key begins `battle_bonus_x5`. This preserves the previously observed count behavior; the exact EU-client token schema is not independently verified.

## Build

Run `python build.py --python27 C:/Python27/python.exe`, or the GitHub Actions workflow.

## Validation

Dragging was confirmed working by the mod author in WoT 2.4.1. Return-from-battle behavior and token parity still require separate verification.
