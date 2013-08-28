# coding: utf-8
import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


def get_test_requirements():
    with open(os.path.join(PROJECT_PATH, 'test-requirements.txt')) as f:
        return f.readlines()


setup(
    name='Flask-Relief',
    version='0.1.0-dev',
    license='BSD',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    url='https://github.com/DasIch/Flask-Relief',
    install_requires=['Flask>=0.10', 'Relief>=2.0.0'],
    tests_require=get_test_requirements(),
    cmdclass={'test': PyTest},
    packages=['flask_relief'],
    zip_safe=False,
    include_package_data=True
)
