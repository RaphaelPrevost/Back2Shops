from distutils.core import setup

from B2SFrontUtils import __version__

setup(
    name='B2SFrontUtils',
    version=__version__,
    author='BacktoShops',
    author_email='backtoshops@lbga.fr',
    packages=['B2SFrontUtils'],
    # The data is too large, so put it on env/data manually.
    # data_files=[('data', ['B2SFrontUtils/data/GeoLite2-City.mmdb',
    #                       'B2SFrontUtils/data/GeoLite2-Country.mmdb'])],
    license='LICENSE.txt',
    description='Packages to define api access and redis cache proxy used by front servers',
    long_description=open('README.txt').read(),
    install_requires=[
        'enum==0.4.4',
        'ujson==1.33',
        'gevent==1.0.1',
        'Unidecode==0.04.16',
        'geoip2==0.6.0',
        ],
     )
