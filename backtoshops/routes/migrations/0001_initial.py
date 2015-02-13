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


import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Route'
        db.create_table(u'routes_route', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mother_brand', self.gf('django.db.models.fields.related.ForeignKey')(related_name='route', on_delete=models.DO_NOTHING, to=orm['accounts.Brand'])),
            ('page_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('page_role', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('url_format', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('redirects_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['routes.Route'], null=True, blank=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'routes', ['Route'])

        # Adding model 'HtmlMeta'
        db.create_table(u'routes_htmlmeta', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('route', self.gf('django.db.models.fields.related.ForeignKey')(related_name='htmlmetas', to=orm['routes.Route'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=300)),
        ))
        db.send_create_signal(u'routes', ['HtmlMeta'])

        # Adding model 'RouteParam'
        db.create_table(u'routes_routeparam', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('route', self.gf('django.db.models.fields.related.ForeignKey')(related_name='routeparams', to=orm['routes.Route'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('is_required', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'routes', ['RouteParam'])


    def backwards(self, orm):
        # Deleting model 'Route'
        db.delete_table(u'routes_route')

        # Deleting model 'HtmlMeta'
        db.delete_table(u'routes_htmlmeta')

        # Deleting model 'RouteParam'
        db.delete_table(u'routes_routeparam')


    models = {
        u'accounts.brand': {
            'Meta': {'object_name': 'Brand'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['address.Address']", 'unique': 'True'}),
            'business_reg_num': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'tax_reg_num': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'address.address': {
            'Meta': {'object_name': 'Address'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['countries.Country']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'province_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'routes.htmlmeta': {
            'Meta': {'object_name': 'HtmlMeta'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'route': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'htmlmetas'", 'to': u"orm['routes.Route']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        u'routes.route': {
            'Meta': {'object_name': 'Route'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'route'", 'on_delete': 'models.DO_NOTHING', 'to': u"orm['accounts.Brand']"}),
            'page_role': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'page_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'redirects_to': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['routes.Route']", 'null': 'True', 'blank': 'True'}),
            'url_format': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'routes.routeparam': {
            'Meta': {'object_name': 'RouteParam'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'route': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'routeparams'", 'to': u"orm['routes.Route']"})
        }
    }

    complete_apps = ['routes']
