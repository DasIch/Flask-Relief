# coding: utf-8
"""
    tests.conftest
    ~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import time
from multiprocessing import Process

import pytest
import selenium.webdriver
from flask import Flask, Blueprint
from werkzeug.urls import url_join

from flask.ext.relief import Relief


TESTS_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
JQUERY_DIR_PATH = os.path.join(TESTS_DIR_PATH, 'jquery')


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
        time.sleep(0.2)
        assert process.is_alive()
    return serve


@pytest.fixture(params=os.listdir(JQUERY_DIR_PATH))
def jquery_path(request):
    return os.path.join(JQUERY_DIR_PATH, request.param)


@pytest.fixture
def jquery_url(app, jquery_path):
    app.register_blueprint(Blueprint(
        'jquery', __name__, static_folder='jquery',
        static_url_path='/static/jquery'
    ))
    return url_join(
        'http://localhost:5000/static/jquery/', os.path.basename(jquery_path)
    )
