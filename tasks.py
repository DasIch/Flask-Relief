# coding: utf-8
from invoke import task, run


@task
def dev():
    run('pip install -e .')
    run('pip install pytest-cov')


@task
def test():
    run('python setup.py test')


@task
def test_all():
    run('tox')


@task
def coverage():
    run('py.test --cov=flask_relief --cov=tests')
    run('coverage html')


@task('coverage')
def view_coverage():
    run('open htmlcov/index.html')


@task
def docs():
    run('make -C docs html')


@task('docs')
def view_docs():
    run('open docs/_build/html/index.html')
