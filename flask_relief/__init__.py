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

from flask.ext.relief.csrf import touch_csrf_token
from flask.ext.relief.crypto import (
    constant_time_equal, mask_secret, unmask_secret
)


class Secret(relief.Unicode):
    """
    Represents a secret string that should not be exposed to attackers.

    Ensures security by masking the string, preventing compression oracle
    attacks.

    .. warning:: This does not prevent anyone from seeing the secret, if the
                 connection to the client is unencrypted.
    """
    def serialize(self, value):
        return mask_secret(value)

    def unserialize(self, value):
        try:
            return unmask_secret(value)
        except TypeError:
            return relief.NotUnserializable


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
            return mask_secret(touch_csrf_token())
        return relief.Unspecified

    def validate(self, context=None):
        super(CSRFToken, self).validate(context)
        if request.method == 'POST' and '_csrf_token' in session:
            try:
                unmasked_value = unmask_secret(self.value)
            except TypeError:
                self.is_valid = False
            else:
                self.is_valid = constant_time_equal(
                    unmasked_value, session['_csrf_token']
                )
        else:
            self.is_valid = False
        return self.is_valid


def _inherit_relief_exports():
    module = sys.modules[__name__]
    for attribute in relief.__all__:
        if not hasattr(module, attribute):
            setattr(module, attribute, getattr(relief, attribute))
            module.__all__.append(attribute)


__all__ = ['Secret', 'CSRFToken']
_inherit_relief_exports()
