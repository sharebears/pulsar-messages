#!/usr/bin/env python3
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='pulsar-messages',
    version='0.0.1',
    description='Messages plugin for the pulsar project',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    author='sharebears',
    author_email='sharebears@tutanota.de',
    url='https://github.com/sharebears',
    packages=[
        'messages',
    ],
    python_requires='==3.7',
    tests_require=[
        'pytest',
        'mock',
    ],
    cmdclass={'test': PyTest},
)
