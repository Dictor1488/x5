"""Static safety contract for the injected garage widget (no game runtime required)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / 'python/scripts/client/gui/mods/mod_inq_x5.py'
JS = ROOT / 'resources/in/gui/gameface/mods/x5/X5Counter/X5Counter.js'
CSS = ROOT / 'resources/in/gui/gameface/mods/x5/X5Counter/X5Counter.css'


class InjectionContract(unittest.TestCase):
    def test_no_standalone_wulf_window(self):
        code = PY.read_text(encoding='utf-8')
        self.assertIn('gf_mod_inject', code)
        self.assertNotIn('WindowImpl', code)
        self.assertNotIn('WindowFlags', code)
        self.assertNotIn('RandomHangar', code)

    def test_dom_drag_is_viewport_bound_and_owned(self):
        code = JS.read_text(encoding='utf-8')
        for needle in ('ModelObserver(', 'observer.onUpdate(render)',
                       'root.contains(e.target)', 'e.clientX',
                       'ev.clientX', 'getBoundingClientRect()',
                       'setPosition', 'w - boxW', 'h - boxH'):
            self.assertIn(needle, code)
        self.assertNotIn('screenX', code)
        self.assertNotIn('event.button', code)

    def test_css_does_not_affect_hangar_globals(self):
        code = CSS.read_text(encoding='utf-8')
        self.assertIn('#inq-x5-root', code)
        self.assertNotIn('html,body{', code)
        self.assertNotIn('position: absolute', code)

    def test_no_standalone_view_registration(self):
        self.assertFalse((ROOT / 'resources/in/gui/gen_resources/tv.dictor.x5.json').exists())
        self.assertFalse((ROOT / 'resources/in/gui/gameface/mods/x5/X5Counter/X5Counter.html').exists())


if __name__ == '__main__':
    unittest.main()
