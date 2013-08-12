# coding: utf-8
"""
    flask.ext.relief
    ~~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import sys

import relief


def inherit_relief_exports():
    module = sys.modules[__name__]
    if hasattr(module, '__all__'):
        __all__ = module.__all__
    else:
        __all__ = []
        setattr(module, '__all__', __all__)
    for attribute in relief.__all__:
        if not hasattr(module, attribute):
            setattr(module, attribute, getattr(relief, attribute))
            __all__.append(attribute)


inherit_relief_exports()
