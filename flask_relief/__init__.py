# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys

import relief
from relief.validation import ProbablyAnEmailAddress
from flask import request, abort, session, Blueprint

from flask.ext.relief.csrf import touch_csrf_token
from flask.ext.relief.crypto import (
    constant_time_equal, mask_secret, unmask_secret
)


blueprint = Blueprint(
    'relief', __name__,
    static_folder='static',
    static_url_path='/static/relief'
)


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
        app.register_blueprint(blueprint)

    def reset_csrf_token(self):
        del session['_csrf_token']

    def _inject_csrf_token(self):
        return {'csrf_token': mask_secret(touch_csrf_token())}

    def _check_csrf_token(self):
        csrf_token = touch_csrf_token()
        if request.method in self.CSRF_SAFE_METHODS:
            return
        try:
            masked_csrf_token = request.form['csrf_token']
        except KeyError:
            try:
                masked_csrf_token = request.headers['X-RELIEF-CSRF-Token']
            except KeyError:
                abort(400)
        try:
            request_csrf_token = unmask_secret(masked_csrf_token)
        except TypeError:
            abort(400)
        if not constant_time_equal(request_csrf_token, csrf_token):
            abort(400)


class WebForm(relief.Form):
    def set_and_validate_on_submit(self, context=None):
        if request.method == 'POST':
            raw_value = {}
            for key in self:
                values = request.form.getlist(key)
                if len(values) > 1:
                    value = values
                elif values:
                    value = values[0]
                else:
                    value = relief.Unspecified
                raw_value[key] = value
            self.set_from_raw(raw_value)
            return self.validate(context=context)
        return False


class Text(relief.Unicode):
    pass


class Email(relief.Unicode):
    validators = [ProbablyAnEmailAddress()]

    def unserialize(self, value):
        if value == u'':
            return relief.Unspecified
        return value


class Password(relief.Unicode):
    pass


class Hidden(relief.Unicode):
    pass


class Secret(Hidden):
    """
    Represents a secret string that should not be exposed to attackers.

    Ensures security by masking the string, preventing compression oracle
    attacks.

    .. warning:: This does not prevent anyone from seeing the secret, if the
                 connection to the client is unencrypted.
    """
    def serialize(self, value):
        if value is relief.Unspecified:
            return value
        return mask_secret(value)

    def unserialize(self, value):
        try:
            return unmask_secret(value)
        except TypeError:
            return relief.NotUnserializable


class Checkbox(relief.Boolean):
    def unserialize(self, value):
        if value is relief.Unspecified:
            return False
        return True


class Choice(relief.Element):
    choices = None

    def __init__(self, value=relief.Unspecified):
        super(Choice, self).__init__(value=value)
        if self.choices is None:
            raise TypeError('choices are undefined')

    def unserialize(self, value):
        if value in self.choices:
            return value
        return relief.NotUnserializable


class MultipleChoice(Choice):
    def unserialize(self, values):
        if values is relief.Unspecified:
            values = []
        elif not isinstance(values, list):
            values = [values]
        if any(value not in self.choices for value in values):
            return relief.NotUnserializable
        return set(values)


class Option(object):
    def __init__(self, value, label=None, selected=False, disabled=False):
        self.value = value
        self.label = label
        self.selected = selected
        self.disabled = disabled

    @property
    def label(self):
        if self._label is None:
            return self.value
        return self._label

    @label.setter
    def label(self, new_label):
        self._label = new_label

    def __repr__(self):
        return '%s(%r, label=%r, selected=%r, disabled=%r)' % (
            self.__class__.__name__, self.value, self.label, self.selected,
            self.disabled
        )


class OptGroup(object):
    def __init__(self, label, options, disabled=False):
        self.label = label
        self.options = options
        self.disabled = disabled

    def __repr__(self):
        return '%s(%r, %r, disabled=%r)' % (
            self.__class__.__name__, self.label, self.options, self.disabled
        )


class Select(relief.Element):
    options = None

    def __init__(self, value=relief.Unspecified):
        super(Select, self).__init__(value=value)
        if self.options is None:
            raise TypeError('options are undefined')


class Submit(relief.Element):
    actions = []

    def __init__(self, value=relief.Unspecified):
        super(Submit, self).__init__(value=value)
        if self.actions is None:
            raise TypeError('actions are undefined')

    def unserialize(self, value):
        if value in self.actions:
            return value
        return relief.NotUnserializable


def _inherit_relief_exports():
    module = sys.modules[__name__]
    for attribute in relief.__all__:
        if not hasattr(module, attribute):
            setattr(module, attribute, getattr(relief, attribute))
            module.__all__.append(attribute)


__all__ = [
    'Secret', 'Relief', 'WebForm', 'Text', 'Email', 'Password', 'Hidden',
    'Checkbox', 'Choice', 'MultipleChoice', 'Submit', 'Option', 'OptGroup',
    'Select'
]
_inherit_relief_exports()
