# -*- coding: utf-8 -*-
"""INQ x5 counter: garage document injection (not a Wulf floating window).
Based on verified OpenWG Gameface sub-view injection used by 14th_ua MoE.
"""
import json
import logging
import os
import time

from frameworks.wulf import ViewModel
from gui.impl.pub import ViewImpl
from gui.impl.pub.view_component import ViewComponent
from gui.impl.gen import R
from gui.impl.lobby.hangar.states import DefaultHangarState
from gui.Scaleform.lobby_entry import getLobbyStateMachine
from openwg_gameface import gf_mod_inject
from helpers import dependency
from skeletons.gui.shared import IItemsCache

LOG = logging.getLogger('INQ.x5')
CONFIG = os.path.join('mods', 'configs', 'inq', 'x5.json')
COUI = 'coui://gui/gameface/mods/x5/X5Counter'
LAYOUT_ID = 'X5CounterView'
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
        x = int(data.get('x'))
        y = int(data.get('y'))
        w = int(data.get('w'))
        h = int(data.get('h'))
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



class X5HostModel(ViewModel):
    __slots__ = ('x5Data',)

    def __init__(self):
        self.x5Data = None
        super(X5HostModel, self).__init__(properties=2, commands=0)

    def _initialize(self):
        super(X5HostModel, self)._initialize()
        self.x5Data = X5Data()
        self._addViewModelProperty('x5Data', self.x5Data)
        gf_mod_inject(self, 'X5Counter',
                      styles=[COUI + '/X5Counter.css'],
                      modules=[COUI + '/X5Counter.js'])


class X5GarageView(ViewComponent):
    viewLayoutID = R.mods.dictor.x5.X5CounterView

    def __init__(self):
        super(X5GarageView, self).__init__(layoutID=self.viewLayoutID(),
                                           model=X5HostModel)


_original_on_loaded = None


def _in_garage():
    try:
        machine = getLobbyStateMachine()
        state = machine.visibleState if machine is not None else None
        return isinstance(state, DefaultHangarState)
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
    try:
        if not _subscribed:
            dependency.instance(IItemsCache).onSyncCompleted += _on_sync
            _subscribed = True
        machine = getLobbyStateMachine()
        if machine is not _lobby_machine:
            if _lobby_machine is not None:
                try:
                    _lobby_machine.onVisibleRouteChanged -= _refresh
                except Exception:
                    pass
            _lobby_machine = machine
            if machine is not None:
                machine.onVisibleRouteChanged += _refresh
    except Exception:
        LOG.exception('Unable to subscribe x5 updates')


def _mount(root):
    global _active
    try:
        layout = X5GarageView.viewLayoutID()
        child = root.getChildView(layout)
        if child is None:
            child = X5GarageView()
            root.setChildView(layout, child)
        host = child.getViewModel()
        if _active is None or _active[0] is not host:
            _active = (host, host.x5Data)
            host.x5Data.setPosition += _on_position
        _subscribe()
        _refresh()
    except Exception:
        LOG.exception('Unable to mount x5 garage component')


def _on_loaded(instance, *args, **kwargs):
    result = _original_on_loaded(instance, *args, **kwargs)
    try:
        if instance.layoutID == R.views.mono.hangar.main():
            _mount(instance)
    except Exception:
        LOG.exception('X5 hangar root detection failed')
    return result


def init():
    global _original_on_loaded
    _read_position()
    if _original_on_loaded is None:
        _original_on_loaded = ViewImpl._onLoaded
        ViewImpl._onLoaded = _on_loaded


def fini():
    global _active, _subscribed, _lobby_machine, _original_on_loaded
    if _original_on_loaded is not None:
        if ViewImpl._onLoaded is _on_loaded:
            ViewImpl._onLoaded = _original_on_loaded
        _original_on_loaded = None
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
