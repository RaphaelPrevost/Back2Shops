#!/usr/bin/env python
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


from django.conf import settings


def iso_flag(iso, flag_path=u''):
	"""
	Returns a full path to the ISO 3166-1 alpha-2 country code flag image.

	``flag_path`` is given in the form
	``'<path relative to media root>/%s.gif'``
	and is appended to ``settings.MEDIA_URL``

	if a valid flag_path is not given trys to use
	``settings.COUNTRIES_FLAG_PATH``
	defaults to ``'flags/%s.gif'``

	"""
	if not settings.MEDIA_URL:
		return u''
	deafult = u'-'
	if not iso:
		iso = deafult
	else:
		iso = iso.lower().strip()
	try:
		flag_name = flag_path % iso
	except (ValueError, TypeError):
		flag_path = getattr(settings, 'COUNTRIES_FLAG_PATH', u'flags/%s.gif')
		try:
			flag_name = flag_path % iso
		except (ValueError, TypeError):
			return u''
	return u''.join((settings.MEDIA_URL, flag_name))
