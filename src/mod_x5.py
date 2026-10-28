# -*- coding: utf-8 -*-
"""GameFace integration PROTOTYPE, not currently installable/verified."""
from gui.impl.lobby.hangar.random.random_hangar import RandomHangar
from gui.shared.personality import ServicesLocator
from openwg_gameface import gf_mod_inject
from x5_counter import count_tokens

_ORIGINAL = None

def _read_tokens():
    cache = ServicesLocator.itemsCache
    tokens = cache.items.tokens.getTokens()
    return count_tokens(tokens)

def _inject(self, *args, **kwargs):
    _ORIGINAL(self, *args, **kwargs)
    # TODO: bind live count to a real GameFace ViewModel property.
    # Hook signature and path must be verified against the actual WoT client.
    try:
        gf_mod_inject(self.getViewModel(), 'x5Counter',
                      styles=['coui://gui/gameface/mods/x5/x5.css'],
                      scripts=['coui://gui/gameface/mods/x5/x5.js'])
    except Exception as exc:
        print('[x5] GameFace injection failed: %s' % exc)

def init():
    global _ORIGINAL
    if _ORIGINAL is not None:
        return
    _ORIGINAL = RandomHangar._initialize
    RandomHangar._initialize = _inject

def fini():
    global _ORIGINAL
    if _ORIGINAL is not None:
        RandomHangar._initialize = _ORIGINAL
        _ORIGINAL = None
