# -*- coding: utf-8 -*-
"""INQ x5: single-module, WoT 2.4.x GameFace garage counter."""
import logging
import time
from functools import wraps

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowImpl, WindowFlags, WindowLayer, WindowStatus
from gui.impl.pub import ViewImpl
from gui.impl.gen import R
from helpers import dependency
from skeletons.gui.impl import IGuiLoader
from skeletons.gui.shared import IItemsCache

LOG = logging.getLogger('INQ.x5')
_window = None
_wait_manager = None
_hangar = None
_previous_populate = None
_previous_dispose = None

def _count_tokens(tokens):
    total = 0
    now = time.time()
    try:
        iterator = tokens.iteritems()
    except AttributeError:
        iterator = tokens.items()
    for key, item in iterator:
        if not str(key).startswith('battle_bonus_x5'):
            continue
        if isinstance(item, dict):
            count = item.get('count', item.get('value', 0))
            expiry = item.get('expire', item.get('expires', None))
        else:
            count = getattr(item, 'count', getattr(item, 'value', 0))
            expiry = getattr(item, 'expire', getattr(item, 'expires', None))
        try:
            if expiry and float(expiry) <= now:
                continue
            total += max(0, int(count))
        except (ValueError, TypeError):
            continue
    return total

def _count():
    cache = dependency.instance(IItemsCache)
    return _count_tokens(cache.items.tokens.getTokens())

class X5Model(ViewModel):
    def __init__(self, properties=1, commands=0):
        super(X5Model, self).__init__(properties=properties, commands=commands)

    def _initialize(self):
        super(X5Model, self)._initialize()
        self._addStringProperty('count', '-')

    def setCount(self, value):
        self._setString(0, str(value))

class X5View(ViewImpl):
    viewLayoutID = R.mods.dictor.x5.X5Counter

    def __init__(self):
        super(X5View, self).__init__(ViewSettings(
            self.viewLayoutID(), flags=ViewFlags.VIEW, model=X5Model()))

    def refresh(self):
        try:
            value = _count()
        except Exception:
            LOG.exception('Failed to read x5 tokens')
            value = '-'
        with self.getViewModel().transaction() as model:
            model.setCount(value)

class X5Window(WindowImpl):
    def __init__(self, parent):
        WindowImpl.__init__(self, WindowFlags.SERVICE_WINDOW,
                            content=X5View(), layer=WindowLayer.VIEW,
                            name='INQx5', parent=parent)

    def _onReady(self):
        self.show(focus=False)
        self.content.refresh()

def _manager():
    try:
        return dependency.instance(IGuiLoader).windowsManager
    except Exception:
        return None

def _unsubscribe():
    global _wait_manager
    if _wait_manager is not None:
        try:
            _wait_manager.onWindowStatusChanged -= _on_window_change
        except Exception:
            pass
        _wait_manager = None

def _on_window_change(*args):
    _show()

def _show():
    global _window, _wait_manager
    if _hangar is None or _window is not None:
        return
    manager = _manager()
    if manager is None:
        return
    parent = manager.getMainWindow()
    if parent is None or getattr(parent, 'proxy', None) is None or getattr(parent, 'windowStatus', None) != WindowStatus.LOADED:
        if _wait_manager is not manager:
            _unsubscribe()
            try:
                manager.onWindowStatusChanged += _on_window_change
                _wait_manager = manager
            except Exception:
                LOG.exception('Cannot subscribe to window readiness')
        return
    _unsubscribe()
    try:
        _window = X5Window(parent)
        _window.load()
    except Exception:
        LOG.exception('Cannot create x5 GameFace window')
        _window = None

def _close():
    global _window
    _unsubscribe()
    if _window is not None:
        try:
            _window.destroy()
        except Exception:
            pass
        _window = None

def _populate(self, *args, **kwargs):
    global _hangar
    result = _previous_populate(self, *args, **kwargs)
    _hangar = self
    _show()
    return result

def _dispose(self, *args, **kwargs):
    global _hangar
    if _hangar is self:
        _hangar = None
        _close()
    return _previous_dispose(self, *args, **kwargs)

def init():
    global _previous_populate, _previous_dispose
    if _previous_populate is not None:
        return
    try:
        from gui.Scaleform.daapi.view.lobby.hangar import Hangar
        _previous_populate = Hangar._populate
        _previous_dispose = Hangar._dispose
        Hangar._populate = _populate
        Hangar._dispose = _dispose
    except Exception:
        LOG.exception('Unable to install hangar hooks')

def fini():
    global _previous_populate, _previous_dispose, _hangar
    _hangar = None
    _close()
    if _previous_populate is not None:
        from gui.Scaleform.daapi.view.lobby.hangar import Hangar
        Hangar._populate = _previous_populate
        Hangar._dispose = _previous_dispose
        _previous_populate = None
        _previous_dispose = None

def onDisconnected():
    _close()

def onAccountBecomeNonPlayer():
    _close()
