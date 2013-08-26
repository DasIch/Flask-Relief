# coding: utf-8
"""
    flask.ext.relief.csrf
    ~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import division
from random import SystemRandom

from flask import session


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
