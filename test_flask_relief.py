# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import relief

import flask.ext.relief


def test_has_all_attributes_mentioned_in_all():
    for attribute in flask.ext.relief.__all__:
        assert hasattr(flask.ext.relief, attribute)


def test_inherits_all_relief_attributes():
    for attribute in relief.__all__:
        assert hasattr(flask.ext.relief, attribute)
