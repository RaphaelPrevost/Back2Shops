import os, sys

from distutils.core import setup
from setuptools.command import install

from B2SCrypto import __version__

setup(
    name='hnIAB',
    version=__version__,
    author='BacktoShops',
    author_email='backtoshops@lbga.fr',
    packages=['B2SCrypto'],
    license='LICENSE.txt',
    description='Packages used to encrypt backtoshops request, decrypt backtoshops response',
    long_description=open('README.txt').read(),
    install_requires=[
        'M2Crypto',
        ],
    )
