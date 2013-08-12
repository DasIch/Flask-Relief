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
    def default_factory(self):
        if request.method == 'GET':
            return randomize_csrf_token(touch_csrf_token())
        return relief.Unspecified

    def validate(self, context=None):
        super(CSRFToken, self).validate(context)
        if request.method != 'POST':
            self.is_valid = False
        elif '_csrf_token' not in session:
            self.is_valid = False
        elif self.value is relief.Unspecified:
            self.is_valid = False
        elif self.value is relief.NotUnserializable:
            self.is_valid = False
        else:
            try:
                unrandomized_value = unrandomize_csrf_token(self.value)
            except TypeError:
                self.is_valid = False
            else:
                self.is_valid = unrandomized_value == session['_csrf_token']
        return self.is_valid


def _inherit_relief_exports():
    module = sys.modules[__name__]
    for attribute in relief.__all__:
        if not hasattr(module, attribute):
            setattr(module, attribute, getattr(relief, attribute))
            module.__all__.append(attribute)


__all__ = []
_inherit_relief_exports()
