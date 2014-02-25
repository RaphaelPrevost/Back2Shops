from distutils.core import setup

from B2SUtils import __version__

setup(
    name='B2SUtils',
    version=__version__,
    author='BacktoShops',
    author_email='backtoshops@lbga.fr',
    packages=['B2SUtils'],
    license='LICENSE.txt',
    description='Packages to provide some utils functions for backtoshops',
    long_description=open('README.txt').read(),
    install_requires=[
       'psycopg2==2.5.1',
       'pypgwrap==0.1.4',
       'gevent==0.13.8',
       'gevent-psycopg2==0.0.3',
       'ujson==1.33',
        ],
     )
