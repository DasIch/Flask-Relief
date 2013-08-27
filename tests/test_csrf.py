# coding: utf-8
"""
    tests.test_csrf
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest
from flask import session

from flask.ext.relief.csrf import generate_csrf_token, touch_csrf_token


def test_generate_csrf_token():
    token = generate_csrf_token()
    assert len(token) == 20
    assert len(generate_csrf_token(length=1)) == 1
    assert generate_csrf_token(alphabet=u'1') == u'1' * 20


@pytest.mark.usefixtures('request_context')
def test_touch_csrf_token(app):
    assert '_csrf_token' not in session
    token = touch_csrf_token()
    assert session['_csrf_token'] == token
    touch_csrf_token()
    assert session['_csrf_token'] == token
