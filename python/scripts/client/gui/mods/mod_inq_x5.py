# -*- coding: utf-8 -*-
"""INQ x5: single-module, WoT 2.4.x GameFace garage counter."""
import logging
import time
import GUI
import BigWorld
import json
import os

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer, WindowStatus
from gui.impl.pub import ViewImpl, WindowImpl
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
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            expiry, count = item[0], item[1]
        elif isinstance(item, dict):
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

_position = [425, 165]
_drag_start_position = None
_drag_start_cursor = None
_CONFIG_PATH = os.path.join('mods', 'configs', 'inq', 'x5.json')

def _load_position():
    try:
        with open(_CONFIG_PATH, 'r') as file_handle:
            data = json.load(file_handle)
        _position[:] = [max(0, int(data['x'])), max(0, int(data['y']))]
    except (IOError, KeyError, TypeError, ValueError):
        pass

def _save_position():
    try:
        directory = os.path.dirname(_CONFIG_PATH)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with open(_CONFIG_PATH, 'w') as file_handle:
            json.dump({'x': _position[0], 'y': _position[1]}, file_handle)
    except Exception:
        LOG.exception('Unable to save x5 position')


class X5Model(ViewModel):
    def __init__(self, properties=1, commands=4):
        super(X5Model, self).__init__(properties=properties, commands=commands)

    def _initialize(self):
        super(X5Model, self)._initialize()
        self._addStringProperty('count', '-')
        self.onReady = self._addCommand('onReady')
        self.onReady += self._ready
        self.onDrag = self._addCommand('onDrag')
        self.onDrag += self._drag
        self.onDragStart = self._addCommand('onDragStart')
        self.onDragStart += self._start_drag
        self.onDragEnd = self._addCommand('onDragEnd')
        self.onDragEnd += self._end_drag

    def _ready(self, *args):
        if _window is not None:
            _window.move(_position[0], _position[1])

    def _start_drag(self, payload=None, *args):
        global _drag_start_position, _drag_start_cursor
        try:
            _drag_start_position = tuple(_position)
            _drag_start_cursor = (float(payload['x']), float(payload['y']))
            LOG.warning('Drag started: %s', _drag_start_cursor)
        except (KeyError, TypeError, ValueError):
            _drag_start_position = _drag_start_cursor = None

    def _drag(self, payload=None, *args):
        if _window is None or _drag_start_cursor is None:
            return
        try:
            dx = float(payload['x']) - _drag_start_cursor[0]
            dy = float(payload['y']) - _drag_start_cursor[1]
            scale = max(0.25, min(3.0, float(payload.get('scale', 1.0))))
            sw, sh = GUI.screenResolution()
            _position[0] = max(0, min(int(sw / scale) - 136, int(round(_drag_start_position[0] + dx / scale))))
            _position[1] = max(0, min(int(sh / scale) - 54, int(round(_drag_start_position[1] + dy / scale))))
            _window.move(*_position)
        except Exception:
            LOG.exception('Unable to drag x5')

    def _end_drag(self, *args):
        global _drag_start_position, _drag_start_cursor
        if _drag_start_cursor is not None:
            LOG.warning('Drag ended: %s', _position)
            _save_position()
        _drag_start_position = _drag_start_cursor = None

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
        WindowImpl.__init__(self, WindowFlags.WINDOW,
                            content=X5View(), layer=WindowLayer.VIEW,
                            name='INQx5', parent=parent)

    def _onReady(self):
        self.show(focus=False)
        self.content.refresh()
        try:
            self.move(*_position)
        except Exception:
            LOG.exception('Cannot position x5 window')

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
    if _hangar is None:
        return
    manager = _manager()
    if manager is None:
        return
    parent = manager.getMainWindow()
    if parent is None or getattr(parent, 'proxy', None) is None or getattr(parent, 'windowStatus', None) != WindowStatus.LOADED:
        if _wait_manager is not manager:
            _unsubscribe()
            manager.onWindowStatusChanged += _on_window_change
            _wait_manager = manager
        return
    # Keep one window per live main lobby root, never recursively create it.
    if _window is not None:
        if getattr(_window, '_x5_parent', None) is parent:
            return
        try:
            _window.destroy()
        except Exception:
            pass
        _window = None
    _unsubscribe()
    try:
        candidate = X5Window(parent)
        candidate._x5_parent = parent
        _window = candidate
        candidate.load()
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
    # Page navigation is not logout: do not destroy the lobby window here.
    # It survives RandomHangar disposal and is cleaned on disconnect/battle.
    return _previous_dispose(self, *args, **kwargs)

def init():
    global _previous_populate, _previous_dispose
    _load_position()
    if _previous_populate is not None:
        return
    try:
        from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
        _previous_populate = RandomHangar._initialize
        _previous_dispose = getattr(RandomHangar, '_finalize', None)
        RandomHangar._initialize = _populate
        if _previous_dispose is not None:
            RandomHangar._finalize = _dispose
    except Exception:
        LOG.exception('Unable to install hangar hooks')

def fini():
    global _previous_populate, _previous_dispose, _hangar
    _hangar = None
    _close()
    if _previous_populate is not None:
        from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
        RandomHangar._initialize = _previous_populate
        if _previous_dispose is not None:
            RandomHangar._finalize = _previous_dispose
        _previous_populate = None
        _previous_dispose = None

def onDisconnected():
    global _hangar
    _hangar = None
    _close()

def onAccountBecomeNonPlayer():
    global _hangar
    _hangar = None
    _close()
