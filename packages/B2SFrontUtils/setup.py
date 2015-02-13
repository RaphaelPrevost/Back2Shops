# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


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
