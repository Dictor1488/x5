# -*- coding: utf-8 -*-
# INCOMPLETE prototype: does not register a GameFace view until validated.
from gui.mods.x5_counter import count_tokens

def get_x5_count(items_cache):
    return count_tokens(items_cache.items.tokens.getTokens())
