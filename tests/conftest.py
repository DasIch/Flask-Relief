# coding: utf-8
"""
    tests.conftest
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import time
from multiprocessing import Process

import pytest
import selenium.webdriver
from flask import Flask

from flask.ext.relief import Relief


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


@pytest.fixture
def extension(app):
    return Relief(app)


@pytest.fixture(scope='session')
def browser(request):
    browser = selenium.webdriver.Firefox()
    request.addfinalizer(browser.quit)
    return browser


@pytest.fixture
def serve(request):
    def serve(app):
        process = Process(target=app.run)
        request.addfinalizer(process.terminate)
        process.start()
        time.sleep(0.1)
        assert process.is_alive()
    return serve
