# coding: utf-8
"""
    flask.ext.relief.csrf
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import division
from random import SystemRandom
from binascii import b2a_hex, a2b_hex, Error as BinASCIIError

from flask import session

from flask.ext.relief.crypto import encrypt_once, decrypt_once


random = SystemRandom()


#: The default characters used for csrf tokens.
CSRF_TOKEN_CHARACTERS = (
    u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    u'abcdefghijklmnopqrstuvwxyz'
    u'0123456789'
)


def generate_csrf_token(length=20, alphabet=CSRF_TOKEN_CHARACTERS):
    """
    Generates a random string of characters `length` long from the given
    `alphabet`.
    """
    return u''.join(random.choice(alphabet) for _ in range(length))


def touch_csrf_token():
    """
    Generates CSRF token and puts it into the session, if not present. Always
    returns the CSRF token.
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_csrf_token()
    return session['_csrf_token']


def randomize_csrf_token(csrf_token):
    """
    Returns a randomized version the given `csrf_token` by creating an OTP
    concatenated with the key used for the OTP. The returned string is
    guraanteed to be ASCII encodeable.
    """
    csrf_token = csrf_token.encode('ascii')
    key, encrypted_csrf_token = encrypt_once(csrf_token)
    return b2a_hex(key + encrypted_csrf_token)


def unrandomize_csrf_token(randomized_csrf_token):
    """
    Returns a CSRF token from a CSRF token randomized with
    :func:`randomize_csrf_token`.

    Raises a :exc:`TypeError` if the `randomized_csrf_token` is not randomized.
    """
    try:
        randomized_csrf_token = a2b_hex(randomized_csrf_token)
    except (TypeError, BinASCIIError) as error:
        raise TypeError(*error.args)
    length_of_parts = len(randomized_csrf_token) // 2
    key = randomized_csrf_token[:length_of_parts]
    encrypted_csrf_token = randomized_csrf_token[length_of_parts:]
    return decrypt_once(key, encrypted_csrf_token).decode('ascii')
