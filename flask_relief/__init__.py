# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys

import relief
from flask import request, session

from flask.ext.relief.csrf import (
    touch_csrf_token, randomize_csrf_token, unrandomize_csrf_token
)


class CSRFToken(relief.Unicode):
    """
    Represents a CSRF token. A token itself is generated in GET requests by
    default and stored in the session under the key `'_csrf_token'`.

    Whenever a :class:`CSRFToken` is created during a GET request it checks
    whether a CSRF token is already in a session. If a token is already in the
    session, it uses that token and randomizes it (more on that later),
    otherwise it generates a new token, puts that into the session, and uses
    the randomized version as a value.

    This means that each user gets exactly one CSRF token, that lives as long
    as the session.

    For validation the given CSRF token is unrandomized and compared against
    the token stored in the session, if both are equal everything is fine. If
    they are different or a CSRF token hasn't even been given validation fails.

    The randomization works by creating a `one-time pad (OTP)`_ of the CSRF
    token, that is concatenated to the key of the OTP::

        KEY || KEY ^ CSRF-TOKEN

    What this means is that even though the CSRF token never changes, the CSRF
    token as exposed through :class:`CSRFToken` is different and unpredictable
    for every instance, which allows using the randomized CSRF token in
    compressed encrypted communication without being vulnerable to compression
    oracle attacks such as BREACH_.

    .. _one-time pad (OTP): http://en.wikipedia.org/wiki/One-time_pad
    .. _BREACH: http://breachattack.com/
    """
    def default_factory(self):
        if request.method == 'GET':
            return randomize_csrf_token(touch_csrf_token())
        return relief.Unspecified

    def validate(self, context=None):
        super(CSRFToken, self).validate(context)
        if request.method == 'POST' and '_csrf_token' in session:
            try:
                unrandomized_value = unrandomize_csrf_token(self.value)
            except TypeError:
                self.is_valid = False
            else:
                self.is_valid = unrandomized_value == session['_csrf_token']
        else:
            self.is_valid = False
        return self.is_valid


def _inherit_relief_exports():
    module = sys.modules[__name__]
    for attribute in relief.__all__:
        if not hasattr(module, attribute):
            setattr(module, attribute, getattr(relief, attribute))
            module.__all__.append(attribute)


__all__ = ['CSRFToken']
_inherit_relief_exports()
