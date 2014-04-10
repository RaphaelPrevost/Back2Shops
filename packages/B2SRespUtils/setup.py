from distutils.core import setup

from B2SRespUtils import __version__

setup(
    name='B2SRespUtils',
    version=__version__,
    author='BacktoShops',
    author_email='backtoshops@lbga.fr',
    packages=['B2SRespUtils'],
    license='LICENSE.txt',
    description='Packages to provide some utils functions to generate response',
    long_description=open('README.txt').read(),
    install_requires=[
       'Jinja2==2.7.1',
       'WeasyPrint==0.19.2',
       'ujson==1.33'
        ],
     )

