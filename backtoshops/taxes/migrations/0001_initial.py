# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Rate'
        db.create_table(u'taxes_rate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='region', to=orm['countries.Country'])),
            ('province', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('applies_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sales.ProductCategory'], null=True, blank=True)),
            ('shipping_to_region', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='shipping_to_region', null=True, to=orm['countries.Country'])),
            ('shipping_to_province', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('rate', self.gf('django.db.models.fields.FloatField')()),
            ('apply_after', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('display_on_front', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'taxes', ['Rate'])


    def backwards(self, orm):
        # Deleting model 'Rate'
        db.delete_table(u'taxes_rate')


    models = {
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'sales.productcategory': {
            'Meta': {'object_name': 'ProductCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'taxes.rate': {
            'Meta': {'object_name': 'Rate'},
            'applies_to': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sales.ProductCategory']", 'null': 'True', 'blank': 'True'}),
            'apply_after': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'display_on_front': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'province': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'rate': ('django.db.models.fields.FloatField', [], {}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'region'", 'to': u"orm['countries.Country']"}),
            'shipping_to_province': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'shipping_to_region': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shipping_to_region'", 'null': 'True', 'to': u"orm['countries.Country']"})
        }
    }

    complete_apps = ['taxes']