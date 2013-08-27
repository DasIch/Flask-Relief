# coding: utf-8
"""
    tests.test_crypto
    ~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest

from flask.ext.relief.crypto import (
    mask_secret, unmask_secret, encrypt_once, decrypt_once, constant_time_equal
)
from flask.ext.relief._compat import text_type


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


class TestConstantTimeEqual(object):
    def test(self):
        assert constant_time_equal(b'foo', b'foo')
        assert not constant_time_equal(b'foo', b'bar')
        assert constant_time_equal(u'foo', u'foo')
        assert not constant_time_equal(u'foo', u'bar')

    @pytest.mark.skipif('sys.version_info < (3, 3)')
    def test_non_ascii(self):
        with pytest.raises(TypeError):
            constant_time_equal(u'ä', u'ä')
