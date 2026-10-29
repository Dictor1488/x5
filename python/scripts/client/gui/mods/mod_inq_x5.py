# -*- coding: utf-8 -*-
"""INQ x5 counter: garage document injection (not a Wulf floating window).
Based on verified OpenWG Gameface sub-view injection used by 14th_ua MoE.
"""
import json
import logging
import os
import time

from frameworks.wulf import ViewModel
from helpers import dependency
from skeletons.gui.shared import IItemsCache

LOG = logging.getLogger('INQ.x5')
CONFIG = os.path.join('mods', 'configs', 'inq', 'x5.json')
COUI = 'coui://gui/gameface/mods/x5/X5Counter'
_active = None
_selected_host = None
_patched = []
_subscribed = False
_lobby_machine = None
_revision = 0
_position = {'x': 0, 'y': 0, 'w': 0, 'h': 0}
_candidates = (
    ('gui.impl.lobby.hangar.presenters.vehicle_statistics_presenter',
     'VehiclesStatisticsPresenter'),
    ('gui.impl.lobby.hangar.presenters.hangar_vehicle_params_presenter',
     'HangarVehicleParamsPresenter'),
)


def _read_position():
    try:
        with open(CONFIG, 'r') as stream:
            data = json.load(stream)
        for key in _position:
            _position[key] = max(0, int(data.get(key, 0)))
    except (IOError, ValueError, TypeError):
        pass


def _save_position():
    try:
        directory = os.path.dirname(CONFIG)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with open(CONFIG, 'w') as stream:
            json.dump(_position, stream, sort_keys=True)
    except Exception:
        LOG.exception('Could not persist x5 coordinates')


def _number(item, now):
    if isinstance(item, (tuple, list)) and len(item) >= 2:
        expiry, count = item[0], item[1]
    elif isinstance(item, dict):
        expiry, count = item.get('expire', item.get('expires')), item.get('count', 0)
    else:
        expiry, count = getattr(item, 'expire', None), getattr(item, 'count', 0)
    try:
        if expiry and float(expiry) <= now:
            return 0
        return max(0, int(count))
    except (ValueError, TypeError):
        return 0


def _count():
    tokens = dependency.instance(IItemsCache).items.tokens.getTokens()
    total = 0
    now = time.time()
    for key, value in getattr(tokens, 'iteritems', tokens.items)():
        if str(key).startswith('battle_bonus_x5'):
            total += _number(value, now)
    return total


class X5Data(ViewModel):
    def __init__(self):
        super(X5Data, self).__init__(properties=7, commands=1)

    def _initialize(self):
        super(X5Data, self)._initialize()
        self._addStringProperty('count', '-')
        self._addNumberProperty('posX', 0)
        self._addNumberProperty('posY', 0)
        self._addNumberProperty('posW', 0)
        self._addNumberProperty('posH', 0)
        self._addNumberProperty('rev', 0)
        self._addBoolProperty('visible', False)
        self.setPosition = self._addCommand('setPosition')
        self.setPosition += _on_position

    def setData(self, count, pos, rev, visible):
        self._setString(0, str(count))
        self._setNumber(1, pos['x'])
        self._setNumber(2, pos['y'])
        self._setNumber(3, pos['w'])
        self._setNumber(4, pos['h'])
        self._setNumber(5, rev)
        self._setBool(6, bool(visible))


def _on_position(arg=None, *unused):
    try:
        data = arg or {}
        x = int(data['x'])
        y = int(data['y'])
        w = int(data['w'])
        h = int(data['h'])
        if w <= 0 or h <= 0:
            return
        # Keep the complete widget within the viewport and save viewport dimensions
        # for proportional recovery after resolution or UI-scale changes.
        _position.update(x=max(0, min(x, w - 124)),
                         y=max(0, min(y, h - 48)), w=w, h=h)
        _save_position()
        _refresh()
    except (KeyError, TypeError, ValueError):
        LOG.exception('Invalid x5 position command')


def _in_garage():
    try:
        from gui.Scaleform.lobby_entry import getLobbyStateMachine
        machine = getLobbyStateMachine()
        state = machine.visibleState if machine is not None else None
        return state is not None and (state.getStateID() or '').endswith('hangar/{root}')
    except Exception:
        return False


def _refresh(*args, **kwargs):
    global _revision
    if _active is None:
        return
    try:
        visible = _in_garage()
        data = _count() if visible else 0
        model = _active[1]
        _revision = (_revision + 1) % 2147483647
        with model.transaction() as tx:
            tx.setData(data, _position, _revision, visible)
    except Exception:
        LOG.exception('Unable to refresh x5 tokens')


def _on_sync(*args, **kwargs):
    _refresh()


def _subscribe():
    global _subscribed, _lobby_machine
    if _subscribed:
        return
    try:
        cache = dependency.instance(IItemsCache)
        cache.onSyncCompleted += _on_sync
        _subscribed = True
        from gui.Scaleform.lobby_entry import getLobbyStateMachine
        machine = getLobbyStateMachine()
        if machine is not None and machine is not _lobby_machine:
            machine.onVisibleRouteChanged += _refresh
            _lobby_machine = machine
    except Exception:
        LOG.exception('Unable to subscribe to item cache')


def _mount(presenter, name):
    global _active, _selected_host
    host = presenter.getViewModel()
    if host is None:
        return
    if _active is not None:
        if _active[0] is host:
            _refresh()
            return
        # One injected host per garage mount. The same presenter may remount
        # after a battle with a new VM; other presenters must not duplicate it.
        if _selected_host != name:
            return
    # OpenWG's ModInjectModel is single-owner per subview. Never replace another mod.
    try:
        if '"ModInjectModel"' in host.proxy.toString():
            return
    except Exception:
        LOG.exception('Unable to check Gameface subview injection occupancy')
        return
    try:
        import openwg_gameface
        openwg_gameface.gf_mod_inject(
            host, 'X5Counter',
            styles=[COUI + '/X5Counter.css'],
            modules=[COUI + '/X5Counter.js'])
        model = X5Data()
        host._addViewModelProperty('x5Data', model)
        _active = (host, model)
        _selected_host = name
        _subscribe()
        _refresh()
    except Exception:
        LOG.exception('X5 Gameface injection failed')


def _install():
    _read_position()
    for module_path, class_name in _candidates:
        try:
            module = __import__(module_path, fromlist=[class_name])
            presenter = getattr(module, class_name)
            if getattr(presenter, '_inq_x5_hooked', False):
                continue
            original = presenter._onLoading
            # Keep original bound to each wrapper, not last value of loop.
            def make_wrapper(fn, presenter_name):
                def wrapped(self, *args, **kwargs):
                    result = fn(self, *args, **kwargs)
                    _mount(self, presenter_name)
                    return result
                return wrapped
            presenter._onLoading = make_wrapper(original, class_name)
            presenter._inq_x5_hooked = True
            _patched.append((presenter, original))
        except Exception:
            LOG.exception('Cannot hook garage presenter: %s', class_name)


def init():
    _install()


def fini():
    global _active, _subscribed, _selected_host, _lobby_machine
    for presenter, original in _patched:
        presenter._onLoading = original
        presenter._inq_x5_hooked = False
    del _patched[:]
    if _subscribed:
        try:
            dependency.instance(IItemsCache).onSyncCompleted -= _on_sync
        except Exception:
            pass
        _subscribed = False
    if _lobby_machine is not None:
        try:
            _lobby_machine.onVisibleRouteChanged -= _refresh
        except Exception:
            pass
        _lobby_machine = None
    _active = None
    _selected_host = None
