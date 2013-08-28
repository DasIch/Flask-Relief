# coding: utf-8
import os

from invoke import task, run


@task
def dev():
    run('pip install -r test-requirements.txt')
    run('pip install -r dev-requirements.txt')
    run('pip install -e .')


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


@task
def travis():
    test()
    environments = []
    if 'STYLE' in os.environ:
        environments.append('style')
    if 'DOCUMENTATION' in os.environ:
        environments.extend(['docs', 'docs3', 'docs-linkcheck'])
    if 'PACKAGING' in os.environ:
        environments.append('packaging')
    run('tox -e %s' % ','.join(environments))
