# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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


import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        db.alter_column('shippings_carrier', 'flag', self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=50))

    def backwards(self, orm):
        db.alter_column('shippings_carrier', 'flag', self.gf('django.db.models.fields.CharField')(max_length=50, blank=False))

    models = {
        u'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'flag': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.customshippingrate': {
            'Meta': {'object_name': 'CustomShippingRate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seller': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.Brand']"}),
            'shipment_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'shipping_rate': ('django.db.models.fields.FloatField', [], {}),
            'total_order_lower': ('django.db.models.fields.FloatField', [], {}),
            'total_order_type': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'total_order_upper': ('django.db.models.fields.FloatField', [], {})
        },
        u'shippings.customshippingrateinshipping': {
            'Meta': {'object_name': 'CustomShippingRateInShipping'},
            'custom_shipping_rate': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.CustomShippingRate']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shipping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Shipping']"})
        },
        u'shippings.flatrateinshipping': {
            'Meta': {'object_name': 'FlatRateInShipping'},
            'flat_rate': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shipping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Shipping']"})
        },
        u'shippings.service': {
            'Meta': {'object_name': 'Service'},
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'services'", 'to': u"orm['shippings.Carrier']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'shippings.serviceinshipping': {
            'Meta': {'object_name': 'ServiceInShipping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Service']"}),
            'shipping': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shippings.Shipping']"})
        },
        u'shippings.shipping': {
            'Meta': {'object_name': 'Shipping'},
            'allow_group_shipment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'allow_pickup': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'handling_fee': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickup_voids_handling_fee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shipping_calculation': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }

    complete_apps = ['shippings']
