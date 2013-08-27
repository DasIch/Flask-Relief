# coding: utf-8
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.test_args))


setup(
    name='Flask-Relief',
    version='0.1.0-dev',
    license='BSD',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    url='https://github.com/DasIch/Flask-Relief',
    install_requires=['Flask>=0.10', 'Relief>=2.0.0'],
    tests_require=['pytest>=2.3.5', 'selenium>=2.35.0'],
    cmdclass={'test': PyTest},
    packages=['flask_relief'],
    zip_safe=False
)
