# -*- coding: utf-8 -*-
"""INQ x5 bonus counter. One native hangar Gameface subview."""
import json
import logging
import os
import time

from frameworks.wulf import ViewModel
from gui.impl.gen import R
from gui.impl.lobby.hangar.states import DefaultHangarState
from gui.impl.pub import ViewImpl
from gui.impl.pub.view_component import ViewComponent
from gui.Scaleform.lobby_entry import getLobbyStateMachine
from helpers import dependency
from openwg_gameface import gf_mod_inject
from skeletons.gui.shared import IItemsCache

LOG = logging.getLogger('INQ.x5')
CONFIG = os.path.join('mods', 'configs', 'inq', 'x5.json')
ASSETS = 'coui://gui/gameface/mods/x5/X5Counter'
_position = {'x': 0, 'y': 0, 'w': 0, 'h': 0}
_active = None
_machine = None
_synced = False
_original_loaded = None


def _load():
    try:
        with open(CONFIG, 'r') as stream:
            saved = json.load(stream)
        for name in _position:
            _position[name] = max(0, int(saved.get(name, 0)))
    except (IOError, ValueError, TypeError, AttributeError):
        pass


def _save():
    try:
        directory = os.path.dirname(CONFIG)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with open(CONFIG, 'w') as stream:
            json.dump(_position, stream, sort_keys=True)
    except Exception:
        LOG.exception('Unable to save x5 position')


def _token_count(value, now):
    # WoT token values commonly expose (expiration, count).
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        expiry, amount = value[0], value[1]
    elif isinstance(value, dict):
        expiry = value.get('expire', value.get('expires'))
        amount = value.get('count', 0)
    else:
        expiry = getattr(value, 'expire', None)
        amount = getattr(value, 'count', 0)
    try:
        if expiry and float(expiry) <= now:
            return 0
        return max(0, int(amount))
    except (TypeError, ValueError):
        return 0


def _count():
    tokens = dependency.instance(IItemsCache).items.tokens.getTokens()
    now = time.time()
    return sum(_token_count(value, now) for key, value in
               getattr(tokens, 'iteritems', tokens.items)()
               if str(key).startswith('battle_bonus_x5'))


def _is_hangar():
    try:
        machine = getLobbyStateMachine()
        return machine is not None and isinstance(machine.visibleState, DefaultHangarState)
    except Exception:
        return False


class CounterVM(ViewModel):
    __slots__ = ('onPositionChanged',)

    def __init__(self):
        super(CounterVM, self).__init__(properties=4, commands=1)

    def _initialize(self):
        super(CounterVM, self)._initialize()
        self._addBoolProperty('visible', False)
        self._addStringProperty('count', '0')
        self._addNumberProperty('posX', 0)
        self._addNumberProperty('posY', 0)
        self.onPositionChanged = self._addCommand('onPositionChanged')

    def setState(self, visible, count, pos):
        self._setBool(0, visible)
        self._setString(1, str(count))
        self._setNumber(2, pos['x'])
        self._setNumber(3, pos['y'])


class HostVM(ViewModel):
    __slots__ = ('x5Data',)

    def __init__(self):
        self.x5Data = None
        super(HostVM, self).__init__(properties=2, commands=0)

    def _initialize(self):
        super(HostVM, self)._initialize()
        self.x5Data = CounterVM()
        self._addViewModelProperty('x5Data', self.x5Data)
        gf_mod_inject(self, 'X5Counter',
                      styles=[ASSETS + '/X5Counter.css'],
                      modules=[ASSETS + '/X5Counter.js'])


class GarageView(ViewComponent):
    viewLayoutID = R.mods.dictor.x5.X5CounterView

    def __init__(self):
        super(GarageView, self).__init__(layoutID=self.viewLayoutID(), model=HostVM)


def _refresh(*args, **kwargs):
    if _active is None:
        return
    visible = _is_hangar()
    try:
        count = _count() if visible else 0
        with _active.transaction() as model:
            model.setState(visible, count, _position)
    except Exception:
        LOG.exception('Unable to refresh x5')


def _position_changed(arg=None, *unused):
    try:
        data = arg or {}
        x = int(data['x'])
        y = int(data['y'])
        if x < 0 or y < 0:
            return
        _position['x'], _position['y'] = x, y
        _position['w'] = max(0, int(data.get('w', 0)))
        _position['h'] = max(0, int(data.get('h', 0)))
        _save()
        _refresh()
    except (KeyError, TypeError, ValueError):
        LOG.exception('Invalid x5 position')


def _subscribe():
    global _synced, _machine
    if not _synced:
        try:
            dependency.instance(IItemsCache).onSyncCompleted += _refresh
            _synced = True
        except Exception:
            LOG.exception('Cannot subscribe x5 item cache')
    machine = getLobbyStateMachine()
    if machine is not _machine:
        if _machine is not None:
            try:
                _machine.onVisibleRouteChanged -= _refresh
            except Exception:
                pass
        _machine = machine
        if machine is not None:
            machine.onVisibleRouteChanged += _refresh


def _mount(root):
    global _active
    layout = GarageView.viewLayoutID()
    child = root.getChildView(layout)
    if child is None:
        child = GarageView()
        root.setChildView(layout, child)
    host = child.getViewModel()
    vm = host.x5Data
    if vm is not _active:
        _active = vm
        vm.onPositionChanged += _position_changed
    _subscribe()
    _refresh()


def _loaded(instance, *args, **kwargs):
    result = _original_loaded(instance, *args, **kwargs)
    try:
        if instance.layoutID == R.views.mono.hangar.main():
            _mount(instance)
    except Exception:
        LOG.exception('Unable to attach x5 to hangar')
    return result


def init():
    global _original_loaded
    _load()
    if _original_loaded is None:
        _original_loaded = ViewImpl._onLoaded
        ViewImpl._onLoaded = _loaded


def fini():
    global _active, _machine, _synced, _original_loaded
    if _original_loaded is not None:
        if ViewImpl._onLoaded is _loaded:
            ViewImpl._onLoaded = _original_loaded
        _original_loaded = None
    if _machine is not None:
        try:
            _machine.onVisibleRouteChanged -= _refresh
        except Exception:
            pass
        _machine = None
    if _synced:
        try:
            dependency.instance(IItemsCache).onSyncCompleted -= _refresh
        except Exception:
            pass
        _synced = False
    _active = None
