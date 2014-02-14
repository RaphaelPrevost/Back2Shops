from distutils.core import setup

from B2SProtocol import __version__

setup(
    name='B2SProtocol',
    version=__version__,
    author='BacktoShops',
    author_email='backtoshops@lbga.fr',
    packages=['B2SProtocol'],
    license='LICENSE.txt',
    description='Packages to define backtoshops protocol between servers',
    long_description=open('README.txt').read(),
    install_requires=[
        'enum==0.4.4',
        ],
     )
