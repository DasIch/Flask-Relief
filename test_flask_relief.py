# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from itertools import permutations

import relief
import pytest
from flask import Flask, session, request

import flask.ext.relief
from flask.ext.relief import CSRFToken
from flask.ext.relief.csrf import (
    generate_csrf_token, touch_csrf_token, randomize_csrf_token,
    unrandomize_csrf_token
)
from flask.ext.relief.crypto import encrypt_once, decrypt_once


@pytest.fixture
def app(request):
    # XXX: __name__ doesn't work due to a bug in Flask / an optional method not
    # implemented by a py.test meta path loader. py.test has the method in the
    # trunk version, so let's change this to __name__ when that version comes
    # out, currently we are at pytest 2.3.5
    app = Flask('__main__')
    app.config['SECRET_KEY'] = b'secret'
    app.testing = True
    return app


@pytest.fixture
def request_context(request, app):
    request_context = app.test_request_context()
    request_context.push()
    request.addfinalizer(request_context.pop)
    return request_context


with_request_context = pytest.mark.usefixtures("request_context")


@pytest.fixture
def csrf_token():
    return generate_csrf_token()


@pytest.fixture
def randomized_csrf_token(csrf_token):
    return randomize_csrf_token(csrf_token)


def test_has_all_attributes_mentioned_in_all():
    for attribute in flask.ext.relief.__all__:
        assert hasattr(flask.ext.relief, attribute)


def test_inherits_all_relief_attributes():
    for attribute in relief.__all__:
        assert hasattr(flask.ext.relief, attribute)


class TestCSRFToken(object):
    def test_default_token(self, app):
        with app.test_request_context(method='GET'):
            element = CSRFToken()
            assert element.value != session['_csrf_token']
            unrandomized_value = unrandomize_csrf_token(element.value)
            assert unrandomized_value == session['_csrf_token']
        with app.test_request_context(method='POST'):
            element = CSRFToken()
            assert element.value is relief.Unspecified

    def test_validate(self, app):
        @app.route('/', methods=['GET', 'POST'])
        def foo():
            if request.method == 'GET':
                return CSRFToken().value
            else:
                assert CSRFToken(request.form['csrf_token']).validate()
                return u'Success'

        with app.test_client() as client:
            with client.get('/') as response:
                randomized_csrf_token = response.data
            client.post('/', data={'csrf_token': randomized_csrf_token})
            with pytest.raises(AssertionError):
                client.post('/', data={'csrf_token': u'bad_csrf_token'})


def test_generate_csrf_token():
    token = generate_csrf_token()
    assert len(token) == 20
    assert len(generate_csrf_token(length=1)) == 1
    assert generate_csrf_token(alphabet=u'1') == u'1' * 20


@with_request_context
def test_touch_csrf_token(app):
    token = touch_csrf_token()
    assert session['_csrf_token'] == token
    touch_csrf_token()
    assert session['_csrf_token'] == token


def test_randomize_csrf_token(csrf_token):
    randomized = [randomize_csrf_token(csrf_token) for _ in range(10)]
    for randomized_token in randomized:
        assert randomized_token != csrf_token
    for a, b in permutations(randomized, 2):
        assert a != b


def test_unrandomize_csrf_token(csrf_token, randomized_csrf_token):
    unrandomized_csrf_token = unrandomize_csrf_token(randomized_csrf_token)
    assert unrandomized_csrf_token == csrf_token


def test_encrypt_once():
    plaintext = b'foobar'
    key, ciphertext = encrypt_once(plaintext)
    assert len(key) == len(ciphertext)
    assert ciphertext != plaintext


def test_decrypt_once():
    plaintext = b'foobar'
    key, ciphertext = encrypt_once(plaintext)
    unencrypted_ciphertext = decrypt_once(key, ciphertext)
    assert unencrypted_ciphertext == plaintext
