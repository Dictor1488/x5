# -*- coding: utf-8 -*-
import time

def count_tokens(tokens, now=None):
    if now is None: now = time.time()
    try: pairs = tokens.iteritems()
    except AttributeError: pairs = tokens.items()
    total = 0
    for name, token in pairs:
        if not str(name).startswith('battle_bonus_x5'): continue
        if isinstance(token, dict):
            expiry = token.get('expire', token.get('expires', None))
            quantity = token.get('count', token.get('value', 0))
        else:
            expiry = getattr(token, 'expire', getattr(token, 'expires', None))
            quantity = getattr(token, 'count', getattr(token, 'value', 0))
        try:
            if expiry and float(expiry) <= now: continue
            total += max(0, int(quantity))
        except (TypeError, ValueError): pass
    return total
