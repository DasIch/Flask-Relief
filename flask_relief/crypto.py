# coding: utf-8
"""
    flask.ext.relief.crypto
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os

from flask.ext.relief._compat import int_to_byte


def xor_bytes(a, b):
    return b''.join(
        int_to_byte(x ^ y) for x, y in zip(bytearray(a), bytearray(b))
    )


def encrypt_once(plaintext):
    key = os.urandom(len(plaintext))
    return key, xor_bytes(key, plaintext)


def decrypt_once(key, ciphertext):
    return xor_bytes(key, ciphertext)
