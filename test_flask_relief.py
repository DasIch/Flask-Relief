# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import relief
import pytest
from flask import Flask, session, request

import flask.ext.relief
from flask.ext.relief import Secret, CSRFToken
from flask.ext.relief.csrf import generate_csrf_token, touch_csrf_token
from flask.ext.relief.crypto import (
    encrypt_once, decrypt_once, constant_time_equal, mask_secret, unmask_secret
)
from flask.ext.relief._compat import text_type


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


def test_has_all_attributes_mentioned_in_all():
    for attribute in flask.ext.relief.__all__:
        assert hasattr(flask.ext.relief, attribute)


def test_inherits_all_relief_attributes():
    for attribute in relief.__all__:
        assert hasattr(flask.ext.relief, attribute)


class TestSecret(object):
    def test_in__all__(self):
        assert 'Secret' in flask.ext.relief.__all__

    def test_masking(self):
        element = Secret()
        element.set_from_native(u'foobar')
        assert element.value == u'foobar'
        assert element.raw_value != u'foobar'

        second_element = Secret(element.raw_value)
        assert second_element.raw_value == element.raw_value
        assert second_element.value == u'foobar'


class TestCSRFToken(object):
    def test_in__all__(self):
        assert 'CSRFToken' in flask.ext.relief.__all__

    def test_default_token(self, app):
        with app.test_request_context(method='GET'):
            element = CSRFToken()
            assert element.value != session['_csrf_token']
            unmasked_value = unmask_secret(element.value)
            assert unmasked_value == session['_csrf_token']
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

        with app.test_client(use_cookies=False) as client:
            with client.get('/') as response:
                randomized_csrf_token = response.data
            with pytest.raises(AssertionError):
                client.post('/', data={'csrf_token': randomized_csrf_token})


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


@pytest.mark.parametrize('secret', [
    u'foo', b'foo'
])
def test_mask_secret(secret):
    masked = set(mask_secret(secret) for _ in range(10))
    assert len(masked) == 10
    for masked_secret in masked:
        assert isinstance(masked_secret, text_type)
        assert masked_secret != secret


@pytest.mark.parametrize('secret', [
    u'foo', b'foo'
])
def test_unmask_secret(secret):
    masked = mask_secret(secret)
    unmasked = unmask_secret(masked)
    assert unmasked == secret
    assert isinstance(unmasked, secret.__class__)


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


def test_constant_time_equal():
    # testing whether the constant time property holds is impractical, so we
    # don't
    assert constant_time_equal(b'foo', b'foo')
    assert not constant_time_equal(b'foo', b'bar')
    assert constant_time_equal(u'foo', u'foo')
    assert not constant_time_equal(u'foo', u'bar')


@pytest.mark.skipif('sys.version_info < (3, 3)')
def test_constant_time_equal_non_ascii():
    with pytest.raises(TypeError):
        constant_time_equal(u'ä', u'ä')
