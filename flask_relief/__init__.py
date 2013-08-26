# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys

import relief
from flask import request, abort, session

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


class Relief(object):
    # Methods that are defined by RFC 2616 to be safe and should not cause any
    # actions beside retrieval of information.
    CSRF_SAFE_METHODS = frozenset(['GET', 'HEAD'])

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.context_processor(self._inject_csrf_token)
        app.before_request(self._check_csrf_token)

    def reset_csrf_token(self):
        del session['_csrf_token']

    def _inject_csrf_token(self):
        return {'csrf_token': mask_secret(touch_csrf_token())}

    def _check_csrf_token(self):
        csrf_token = touch_csrf_token()
        if request.method in self.CSRF_SAFE_METHODS:
            return
        try:
            request_csrf_token = unmask_secret(request.form['csrf_token'])
        except TypeError:
            abort(400)
        if not constant_time_equal(request_csrf_token, csrf_token):
            abort(400)


class WebForm(relief.Form):
    def set_and_validate_on_submit(self, context=None):
        if request.method == 'POST':
            self.set_from_raw(request.form)
            return self.validate(context=context)
        return False


def _inherit_relief_exports():
    module = sys.modules[__name__]
    for attribute in relief.__all__:
        if not hasattr(module, attribute):
            setattr(module, attribute, getattr(relief, attribute))
            module.__all__.append(attribute)


__all__ = ['Secret', 'Relief', 'WebForm']
_inherit_relief_exports()
