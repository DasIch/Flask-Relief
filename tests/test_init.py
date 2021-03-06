# coding: utf-8
"""
    tests.test_init
    ~~~~~~~~~~~~~~~

    :copyright: 2013 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from __future__ import print_function
from itertools import chain, combinations

import pytest
import flask
import relief
from relief.validation import IsFalse, IsTrue
from selenium.common.exceptions import ElementNotVisibleException

import flask.ext.relief
from flask.ext.relief import (
    Secret, WebForm, Text, Email, Password, Hidden, Checkbox, Choice,
    MultipleChoice, Submit, Option, OptGroup, Select
)


def submit_form(browser):
    forms = browser.find_elements_by_tag_name('form')
    if len(forms) == 1:
        forms[0].submit()
    else:
        if forms:
            print(u'found more than one form:')
        else:
            print(u'found no form:')
        print(browser.page_source)
        assert False


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

            with client.post('/', headers={'X-RELIEF-CSRF-TOKEN': csrf_token}) as response:
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

    def test_jquery_csrf_js(self, extension, app, serve, browser, jquery_url):
        @app.route('/', methods=['GET', 'POST'])
        def index():
            if flask.request.method == 'POST':
                json = flask.request.get_json()
                return flask.jsonify(result=json['a'] + json['b'])
            elif flask.request.method == 'GET':
                return flask.render_template_string(u"""
                    <!doctype html>
                    <meta name=csrf-token content="{{ csrf_token }}">
                    <script type=text/javascript src="{{ jquery }}"></script>
                    <script type=text/javascript
                            src="{{ url_for('relief.static', filename='jquery-csrf.js') }}">
                    </script>
                    <script type=text/javascript>
                        $.ajax({
                            type: 'POST',
                            url: '/',
                            data: '{"a": 1, "b": 1}',
                            contentType: 'application/json',
                            success: function(response) {
                                $('#result').text(response.result)
                            }
                        });
                    </script>
                    <p id=result></p>
                """, jquery=jquery_url)

        serve(app)

        browser.get('http://localhost:5000')
        result = browser.find_element_by_id('result')
        assert result.text == u'2'


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


class TestText(object):
    @pytest.fixture
    def make_text_app(self, app, extension):
        def make_text_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        <input type=text
                               name=foo
                               value="{{ form.foo.raw_value }}">
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_text_app

    def test_in__all__(self):
        assert 'Text' in flask.ext.relief.__all__

    def test_unchanged(self, make_text_app, serve, browser):
        class Form(WebForm):
            foo = Text

        text_app = make_text_app(Form)
        serve(text_app)

        browser.get('http://localhost:5000')
        submit_form(browser)
        assert u'success' in browser.page_source

    def test_changed(self, make_text_app, serve, browser):
        class Form(WebForm):
            foo = Text

            def validate_foo(self, element, context):
                return element.value == u'foo'

        text_app = make_text_app(Form)
        serve(text_app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'text':
                input.send_keys(u'foo')
        submit_form(browser)
        assert u'success' in browser.page_source


class TestEmail(object):
    @pytest.fixture
    def make_email_app(self, app, extension):
        def make_email_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        <input type=email
                               name=foo
                               value="{{ form.foo.raw_value }}">
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_email_app

    def test_in__all__(self):
        assert 'Email' in flask.ext.relief.__all__

    def test_validation(self):
        email = Email()
        email.set_from_raw(u'foo')
        assert not email.validate()
        email.set_from_raw(u'foo@bar.baz')
        assert email.validate()

    def test(self, make_email_app, serve, browser):
        class Form(WebForm):
            foo = Email

            def validate_foo(self, element, context):
                return element.value == u'foo@bar.baz'

        email_app = make_email_app(Form)
        serve(email_app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'email':
                input.send_keys(u'foo@bar.baz')
        submit_form(browser)
        assert u'success' in browser.page_source


class TestPassword(object):
    @pytest.fixture
    def make_password_app(self, app, extension):
        def make_password_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        <input type=password
                               name=foo
                               value="{{ form.foo.raw_value }}">
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_password_app

    def test_in__all__(self):
        assert 'Password' in flask.ext.relief.__all__

    def test_unchanged(self, make_password_app, serve, browser):
        class Form(WebForm):
            foo = Password

        password_app = make_password_app(Form)
        serve(password_app)

        browser.get('http://localhost:5000')
        submit_form(browser)
        assert u'success' in browser.page_source

    def test_changed(self, make_password_app, serve, browser):
        class Form(WebForm):
            foo = Password

            def validate_foo(self, element, context):
                return element.value == u'foo'

        password_app = make_password_app(Form)
        serve(password_app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'password':
                input.send_keys(u'foo')
        submit_form(browser)
        assert u'success' in browser.page_source


class TestHidden(object):
    @pytest.fixture
    def make_hidden_app(self, app, extension):
        def make_hidden_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form({'foo': u'foo'})
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        <input type=hidden
                               name=foo
                               value="{{ form.foo.raw_value }}">
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_hidden_app

    def test_in__all__(self):
        assert 'Hidden' in flask.ext.relief.__all__

    def test(self, make_hidden_app, serve, browser):
        class Form(WebForm):
            foo = Hidden

            def validate_foo(self, element, context):
                return element.value == u'foo'

        hidden_app = make_hidden_app(Form)
        serve(hidden_app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'hidden':
                with pytest.raises(ElementNotVisibleException):
                    input.send_keys(u'bar')
        submit_form(browser)
        assert u'success' in browser.page_source


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
        submit_form(browser)
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
        submit_form(browser)
        assert u'success' in browser.page_source


class TestChoice(object):
    @pytest.fixture
    def make_choice_app(self, app, extension):
        def make_choice_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        {% for choice in form.foo.choices %}
                            <input type=radio
                                   name=foo
                                   value="{{ choice }}">
                        {% endfor %}
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_choice_app

    def test_in__all__(self):
        assert 'Choice' in flask.ext.relief.__all__

    def test_init_without_choices(self):
        with pytest.raises(TypeError):
            Choice()

    def test_unserialize(self):
        choice = Choice.using(choices=[u'foo', u'bar'])()
        choice.set_from_raw(u'foo')
        assert choice.value == u'foo'
        choice.set_from_raw(u'bar')
        assert choice.value == u'bar'
        choice.set_from_raw(u'baz')
        assert choice.value is relief.NotUnserializable

    def test_unchanged(self, make_choice_app, serve, browser):
        class Form(WebForm):
            foo = Choice.using(choices=[u'foo', u'bar'])
        choice_app = make_choice_app(Form)
        serve(choice_app)

        browser.get('http://localhost:5000')
        submit_form(browser)
        assert u'success' not in browser.page_source

    @pytest.mark.parametrize('choice', [u'foo', u'bar'])
    def test_changed(self, make_choice_app, serve, browser, choice):
        class Form(WebForm):
            foo = Choice.using(choices=[u'foo', u'bar'])

            def validate_foo(self, element, context):
                return element.value == choice
        choice_app = make_choice_app(Form)
        serve(choice_app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'radio':
                if input.get_attribute('value') == choice:
                    input.click()
        submit_form(browser)
        assert u'success' in browser.page_source


class TestMultipleChoice(object):
    @pytest.fixture
    def make_multiple_choice_app(self, app, extension):
        def make_multiple_choice_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        {% for choice in form.foo.choices %}
                            <input type=checkbox
                                   name=foo
                                   value="{{ choice }}">
                        {% endfor %}
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_multiple_choice_app

    def test_in__all__(self):
        assert 'MultipleChoice' in flask.ext.relief.__all__

    def test_init_without_choices(self):
        with pytest.raises(TypeError):
            MultipleChoice()

    def test_unchanged(self, make_multiple_choice_app, serve, browser):
        class Form(WebForm):
            foo = MultipleChoice.using(choices=[u'foo', u'bar', u'baz'])

        multiple_choice_app = make_multiple_choice_app(Form)
        serve(multiple_choice_app)

        browser.get('http://localhost:5000')
        submit_form(browser)
        assert u'success' in browser.page_source

    @pytest.mark.parametrize('selection', [
        set(selection) for selection in chain.from_iterable(
            combinations([u'foo', u'bar', u'baz'], i) for i in range(1, 4)
        )
    ])
    def test_changed(self, make_multiple_choice_app, serve, browser,
                     selection):
        class Form(WebForm):
            foo = MultipleChoice.using(choices=[u'foo', u'bar', u'baz'])

            def validate_foo(self, element, context):
                return element.value == selection

        multiple_choice_app = make_multiple_choice_app(Form)
        serve(multiple_choice_app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('type') == 'checkbox':
                if input.get_attribute('value') in selection:
                    input.click()
        submit_form(browser)
        assert u'success' in browser.page_source


class TestOption(object):
    def test_in__all__(self):
        assert 'Option' in flask.ext.relief.__all__

    def test_label(self):
        option = Option(u'foo')
        assert option.value == option.label == u'foo'
        option.label = u'bar'
        assert option.value == u'foo'
        assert option.label == u'bar'
        option.label = None
        assert option.value == option.label == u'foo'

    def test_repr(self):
        assert (
            repr(Option('foo')) ==
            "Option('foo', label='foo', selected=False, disabled=False)"
        )


class TestOptGroup(object):
    def test_in__all__(self):
        assert 'OptGroup' in flask.ext.relief.__all__

    def test_repr(self):
        assert repr(OptGroup('foo', [Option('bar')])) == (
            "OptGroup('foo', ["
            "Option('bar', label='bar', selected=False, disabled=False)"
            "], disabled=False)"
        )


class TestSelect(object):
    @pytest.fixture
    def make_select_app(self, app, extension):
        def make_select_app(Form):
            @app.route('/', methods=['GET', 'POST'])
            def index():
                form = Form()
                if form.set_and_validate_on_submit():
                    return u'success'
                return flask.render_template_string(u"""
                    <!doctype html>
                    <form method=POST>
                        <select name=foo {% if form.foo.multiple %}multiple{% endif %}>
                            {% for option in form.foo.options %}
                                <option label="{{ option.label }}">{{ option.value }}</option>
                            {% endfor %}
                        </select>
                        <input type=hidden
                               name=csrf_token
                               value="{{ csrf_token }}">
                    </form>
                """, form=form)
            return app
        return make_select_app

    def test_in__all__(self):
        assert 'Select' in flask.ext.relief.__all__

    def test_init_without_options(self):
        with pytest.raises(TypeError):
            Select()

    def test_validate(self):
        element = Select.using(options=[Option(u'foo'), Option(u'bar')])()
        element.set_from_raw(u'foo')
        assert element.value == element.raw_value == u'foo'
        assert element.validate()
        element.set_from_raw(u'bar')
        assert element.value == element.raw_value == u'bar'
        assert element.validate()
        element.set_from_raw(u'baz')
        assert element.value is relief.NotUnserializable
        assert element.raw_value == u'baz'
        assert not element.validate()

    @pytest.mark.parametrize('selection', [u'foo', u'bar'])
    def test_single(self, make_select_app, serve, browser, selection):
        class Form(WebForm):
            foo = Select.using(options=[
                Option(u'foo'),
                Option(u'bar')
            ])

            def validate_foo(self, element, context):
                assert element.value == selection
                return element.value == selection

        select_app = make_select_app(Form)
        serve(select_app)

        browser.get('http://localhost:5000')
        for option in browser.find_elements_by_tag_name('option'):
            if option.get_attribute('value') == selection:
                option.click()
        submit_form(browser)
        assert u'success' in browser.page_source

    @pytest.mark.parametrize('selection', [
        set(selection) for selection in chain.from_iterable(
            combinations([u'foo', u'bar', u'baz'], i) for i in range(1, 4)
        )
    ])
    def test_multiple(self, make_select_app, serve, browser, selection):
        class Form(WebForm):
            foo = Select.using(multiple=True, options=[
                Option(u'foo'),
                Option(u'bar'),
                Option(u'baz')
            ])

            def validate_foo(self, element, context):
                return element.value == selection

        select_app = make_select_app(Form)
        serve(select_app)

        browser.get('http://localhost:5000')
        for option in browser.find_elements_by_tag_name('option'):
            if option.text in selection:
                option.click()
        submit_form(browser)
        assert u'success' in browser.page_source


class TestSubmit(object):
    def test_in__all__(self):
        assert 'Submit' in flask.ext.relief.__all__

    @pytest.mark.parametrize(('actions', 'selected'), [
        ([u'foo'], u'foo'),
        ([u'foo', u'bar'], u'foo'),
        ([u'foo', u'bar'], u'bar')
    ])
    def test(self, extension, app, serve, browser, actions, selected):
        class Form(WebForm):
            action = Submit.using(actions=actions)

            def validate_action(self, element, context):
                return element.value == selected

        @app.route('/', methods=['GET', 'POST'])
        def index():
            form = Form()
            if form.set_and_validate_on_submit():
                return u'success'
            return flask.render_template_string(u"""
                <!doctype html>
                <form method=POST>
                    {% for value in form.action.actions %}
                        <input type=submit name=action value="{{ value }}">
                    {% endfor %}
                    <input type=hidden name=csrf_token value="{{ csrf_token }}">
                </form>
            """, form=form)

        serve(app)

        browser.get('http://localhost:5000')
        for input in browser.find_elements_by_tag_name('input'):
            if input.get_attribute('value') == selected:
                input.click()
                break
        assert u'success' in browser.page_source
