# coding: utf-8
"""
    flask.ext.relief.crypto
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
from binascii import b2a_hex, a2b_hex, Error as BinASCIIError
try:
    from hmac import compare_digest as _constant_time_equal
except ImportError:
    _constant_time_equal = None

from flask.ext.relief._compat import int_to_byte, PY2, text_type


def xor_bytes(a, b):
    """
    XORs each byte in `a` and `b` together and returns the concatenated result.
    """
    return b''.join(
        int_to_byte(x ^ y) for x, y in zip(bytearray(a), bytearray(b))
    )


def encrypt_once(plaintext):
    """
    Returns a random key and the ciphertext of a one-time pad, generated using
    the returned key and the given `plaintext`. Expects everything to be bytes.
    """
    key = os.urandom(len(plaintext))
    return key, xor_bytes(key, plaintext)


def decrypt_once(key, ciphertext):
    """
    Decrypts a one-time pad as generated by :func:`encrypt_once` and returns
    the plaintext.
    """
    return xor_bytes(key, ciphertext)


def constant_time_equal(a, b):
    """
    Returns `True` if the strings `a` and `b` are equal. `a` and `b` are
    compared in constant time, short circuiting if they are of different
    length.

    *May* raise a :exc:`ValueError` if `a` or `b` is a non-ascii unicode
    string.

    This function exposes the length of the strings that are compared but does
    not expose upto which position the strings are equal. This makes it
    suitable for comparisions of untrusted with secret strings, if the length
    of the secret string is public knowledge.

    .. warning:: The constant time property of this function does not hold if
                 non-ascii unicode strings are compared.

    .. warning:: This function assumes that if the interpreter caches small
                 integers, it does cache all integers from 0 to 256 inclusive.
                 If this assumption does not hold, the comparison will not
                 occur in constant time.
    """
    # Checking whether `a` and `b` are non-ascii requires us to iterate over
    # them, which would leak timing information. `hmac.compare_digest` does
    # perform such a check -- presumably this is possible in C without leaking
    # timing information -- and raises a `ValueError`. This is why a
    # `ValueError` *may* be raised by this function, if the inputs are
    # non-ascii. This behaviour is undesirable but more desireable than leaking
    # timing information.
    if _constant_time_equal is not None:
        return _constant_time_equal(a, b)
    if len(a) != len(b):
        return False
    result = 0
    if isinstance(a, bytes) and isinstance(b, bytes) and not PY2:
        for x, y in zip(a, b):
            result |= x ^ y
    else:
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
    return result == 0


def mask_secret(secret):
    """
    Returns a randomized version the given `secret` by creating an OTP
    concatenated with the key used for the OTP. The returned string is
    guraanteed to be ASCII encodeable.
    """
    if isinstance(secret, text_type):
        tag = b'u'
        secret = secret.encode('latin1')
    else:
        tag = b'b'
    key, encrypted_secret = encrypt_once(tag + secret)
    return b2a_hex(key + encrypted_secret).decode('ascii')


def unmask_secret(masked_secret):
    """
    Unmasks a secret string that has been marked with :func:`mask_secret`.

    Raises a :exc:`TypeError`, if `masked_secret` is invalid.
    """
    try:
        key_encrypted_secret = a2b_hex(masked_secret)
    except (TypeError, BinASCIIError) as error:
        raise TypeError(*error.args)
    length_of_parts = len(key_encrypted_secret) // 2
    key = key_encrypted_secret[:length_of_parts]
    encrypted_secret = key_encrypted_secret[length_of_parts:]
    decrypted = decrypt_once(key, encrypted_secret)
    tag, secret = decrypted[0:1], decrypted[1:]
    if tag == b'u':
        return secret.decode('latin1')
    elif tag == b'b':
        return secret
    else:
        raise NotImplementedError('secret masked with bad version')
