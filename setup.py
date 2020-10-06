"""Setup for the actarius package."""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
import versioneer


INSTALL_REQUIRES = [
    'mlflow>=1.8.0',
    'gitpython',
    'birch>=0.0.31',
]
TEST_REQUIRES = [
    'pandas', 'databricks-cli',
    # testing and coverage
    'pytest>=4.6', 'coverage', 'pytest-cov==2.5.1',
    'boto3',  # to upload the coverage badge to S3
    # 'pytest-timeout',  # for timeout mark for tests
    # unmandatory dependencies of the package itself
    # to be able to run `python setup.py checkdocs`
    'collective.checkdocs', 'pygments',
]

with open('README.rst') as f:
    README = f.read()

setuptools.setup(
    name='actarius',
    description='Opinionated wrappers for the mlflow tracking API.',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    long_description=README,
    url='https://github.com/shaypal5/actarius',
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        INSTALL_REQUIRES
    ],
    extras_require={
        'test': TEST_REQUIRES + INSTALL_REQUIRES,
    },
    platforms=['linux', 'osx', 'windows'],
    keywords=['ml', 'mlflow', 'experiments'],
    classifiers=[
        # Trove classifiers
        # (https://pypi.python.org/pypi?%3Aaction=list_classifiers)
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Topic :: Other/Nonlisted Topic',
        'Intended Audience :: Developers',
    ],
)
