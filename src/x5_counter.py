# -*- coding: utf-8 -*-
"""Python 2.7-compatible x5 token aggregation."""
import time

PREFIX = 'battle_bonus_x5'

def _field(value, name, default=None):
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)

def count_tokens(tokens, now=None):
    """Sum non-expired x5 consumable quantities."""
    if now is None:
        now = time.time()
    try:
        pairs = tokens.iteritems()
    except AttributeError:
        pairs = tokens.items()
    result = 0
    for token_id, token in pairs:
        if not str(token_id).startswith(PREFIX):
            continue
        expiry = _field(token, 'expire', None)
        if expiry is None:
            expiry = _field(token, 'expires', None)
        if expiry:
            try:
                if float(expiry) <= now:
                    continue
            except (TypeError, ValueError):
                pass
        count = _field(token, 'count', None)
        if count is None:
            count = _field(token, 'value', 0)
        try:
            result += max(0, int(count))
        except (TypeError, ValueError):
            pass
    return result
