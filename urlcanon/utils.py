from __future__ import unicode_literals
from six import text_type
from six.moves.urllib.parse import unquote, quote, quote_plus
from six.moves.urllib.parse import unquote_to_bytes

from urlcanon.constants import SAFE_CHARS

_enc = 'utf-8'


def _noop(obj):
    return obj


def _encode_result(obj):
    return obj.encode(_enc)


def _decode_args(args):
    return tuple(x.decode(_enc) if x else '' for x in args)


def _coerce_args(*args):
    # Invokes decode if necessary to create str args
    # and returns the coerced inputs along with
    # an appropriate result coercion function
    #   - noop for str inputs
    #   - encoding function otherwise
    str_input = isinstance(args[0], text_type)
    for arg in args[1:]:
        # We special-case the empty string to support the
        # "scheme=''" default argument to some functions
        if arg and isinstance(arg, text_type) != str_input:
            raise TypeError("Cannot mix str and non-str arguments")
    if str_input:
        return args + (_noop,)
    return _decode_args(args) + (_encode_result,)


def _parse_qsl(qs, keep_blank_values=False, strict_parsing=False):
    """Modify `urllib.parse.parse_qsl` to handle percent-encoded characters
    properly. `parse_qsl` replaces percent-encoded characters with
    replacement character (U+FFFD) (if errors = "replace") or drops them (if 
    errors = "ignore") (See https://docs.python.org/3/howto/unicode.html#the-string-type).
    Instead we want to keep the raw bytes. And later we can percent-encode them
    directly when we need to.

    Code from https://github.com/python/cpython/blob/73c4708630f99b94c35476529748629fff1fc63e/Lib/urllib/parse.py#L658
    with `unquote` replaced with `unquote_to_bytes`
    """
    qs, _coerce_result = _coerce_args(qs)
    pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = nv[0].replace('+', ' ')
            name = unquote_to_bytes(name)
            name = _coerce_result(name)
            value = nv[1].replace('+', ' ')
            value = unquote_to_bytes(value)
            value = _coerce_result(value)
            r.append((name, value))
    return r


def _quote(text):
    if isinstance(text, text_type):
        text = text.encode(_enc)
    return quote(text, safe=SAFE_CHARS)


def _quote_plus(text):
    if isinstance(text, text_type):
        text = text.encode(_enc)
    return quote_plus(text, safe=SAFE_CHARS)


def _unquote(text):
    text = unquote(text)
    if not isinstance(text, text_type):
        text = text.decode(_enc)
    return text


def _urlencode(queries):
    parts = []
    for k, v in sorted(set(queries)):
        part = _quote_plus(k), _quote_plus(v)
        parts.append('='.join(part))
    return '&'.join(parts)