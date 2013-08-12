# coding: utf-8
"""
    flask.ext.relief._compat
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys
from operator import methodcaller


PY2 = sys.version_info[0] == 2


if PY2:
    int_to_byte = chr
else:
    int_to_byte = methodcaller('to_bytes', 1, 'big')
