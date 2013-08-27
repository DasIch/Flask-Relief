# coding: utf-8
"""
    tests.test_init
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import relief
import pytest
from flask import request, render_template_string

import flask.ext.relief
from flask.ext.relief import Secret, WebForm


class TestModule(object):
    def test_has_all_attributes_mentioned_in__all__(self):
        for attribute in flask.ext.relief.__all__:
            assert hasattr(flask.ext.relief, attribute)

    def test_inherits_all_relief_attributes(self):
        for attribute in relief.__all__:
            assert hasattr(flask.ext.relief, attribute)


class TestSecret(object):
    def test_in__all__(self):
        assert 'Secret' in flask.ext.relief.__all__

    def test_serialization(self):
        element = Secret()
        element.set_from_native(u'foobar')
        assert element.value == u'foobar'
        assert element.raw_value != u'foobar'

        second_element = Secret(element.raw_value)
        assert second_element.raw_value == element.raw_value
        assert second_element.value == u'foobar'


class TestRelief(object):
    @pytest.fixture
    def csrf_app(self, app, extension):
        @app.route('/', methods=['GET', 'POST'])
        def index():
            if request.method == 'GET':
                return render_template_string(u'{{ csrf_token }}')
            return u'success'
        return app

    def test_in__all__(self):
        assert 'Relief' in flask.ext.relief.__all__

    def test_context_injection(self, csrf_app):
        with csrf_app.test_client() as client:
            with client.get('/') as response:
                assert response.status_code == 200
                assert response.data != u'success'

    def test_csrf_checking(self, csrf_app):
        with csrf_app.test_client() as client:
            csrf_token = client.get('/').data
            with client.post('/', data={'csrf_token': csrf_token}) as response:
                assert response.status_code == 200
                assert response.data == b'success'

            with client.post('/') as response:
                assert response.status_code == 400

            with client.post('/', data={'csrf_token': u'asd'}) as response:
                assert response.status_code == 400

            for _ in range(10):
                assert client.get('/').data != csrf_token

    def test_reset_csrf_token(self, extension, csrf_app):
        @csrf_app.route('/reset_token')
        def reset_token():
            extension.reset_csrf_token()
            return u''

        with csrf_app.test_client() as client:
            csrf_token = client.get('/').data
            client.get('/reset_token')
            with client.post('/', data={'csrf_token': csrf_token}) as response:
                assert response.status_code == 400


class TestWebForm(object):
    def test_in__all__(self):
        assert 'WebForm' in flask.ext.relief.__all__

    def test(self, app):
        class SomeForm(WebForm):
            foo = relief.Unicode

        @app.route('/', methods=['GET', 'POST'])
        def index():
            return str(SomeForm().set_and_validate_on_submit())

        with app.test_client() as client:
            with client.get('/') as response:
                assert response.status_code == 200
                assert response.data == b'False'

            with client.post('/') as response:
                assert response.status_code == 200
                assert response.data == b'False'

            with client.post('/', data={'foo': u'foo'}) as response:
                assert response.status_code == 200
                assert response.data == b'True'
