# coding: utf-8
"""
    tests.test_init
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest
import flask
import relief
from relief.validation import IsFalse, IsTrue

import flask.ext.relief
from flask.ext.relief import Secret, WebForm, Checkbox


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
            if flask.request.method == 'GET':
                return flask.render_template_string(u'{{ csrf_token }}')
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


class TestCheckbox(object):
    @pytest.fixture
    def make_checkbox_app(self, app, extension):
        def make_checkbox_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        <input type=checkbox
                               name=foo
                               {% if form.foo.value %}checked{% endif %}>
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_checkbox_app

    def test_in__all__(self):
        assert 'Checkbox' in flask.ext.relief.__all__

    @pytest.mark.parametrize('form', [
        WebForm.of({'foo': Checkbox.validated_by([IsFalse()])}),
        WebForm.of({
            'foo': Checkbox.using(default=True).validated_by([IsTrue()])
        })
    ])
    def test_unchanged(self, make_checkbox_app, serve, browser, form):
        checkbox_app = make_checkbox_app(form)
        serve(checkbox_app)

        browser.get('http://localhost:5000')
        if form().foo.value:
            assert u'checked' in browser.page_source
        else:
            assert u'checked' not in browser.page_source
        browser.find_elements_by_tag_name('form')[0].submit()
        assert u'success' in browser.page_source

    @pytest.mark.parametrize('form', [
        WebForm.of({'foo': Checkbox.validated_by([IsTrue()])}),
        WebForm.of({
            'foo': Checkbox.using(default=True).validated_by([IsFalse()])
        })

    ])
    def test_changed(self, make_checkbox_app, serve, browser, form):
        checkbox_app = make_checkbox_app(form)
        serve(checkbox_app)
        browser.get('http://localhost:5000')
        if form().foo.value:
            assert u'checked' in browser.page_source
        else:
            assert u'checked' not in browser.page_source
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'checkbox':
                input.click()
        browser.find_elements_by_tag_name('form')[0].submit()
        assert u'success' in browser.page_source
