# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.core.management import call_command


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CountryXCurrency'
        db.create_table('country_x_currency', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['countries.Country'])),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=3)),
        ))
        db.send_create_signal(u'countries', ['CountryXCurrency'])

        # Adding unique constraint on 'CountryXCurrency', fields ['country', 'currency']
        db.create_unique('country_x_currency', ['country_id', 'currency'])

        # Load data
        call_command("loaddata", "countries/country_x_currency.json")


    def backwards(self, orm):
        # Removing unique constraint on 'CountryXCurrency', fields ['country', 'currency']
        db.delete_unique('country_x_currency', ['country_id', 'currency'])

        # Deleting model 'CountryXCurrency'
        db.delete_table('country_x_currency')


    models = {
        u'countries.caprovince': {
            'Meta': {'ordering': "('name',)", 'object_name': 'CaProvince', 'db_table': "'ca_province'"},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'countries.countryxcurrency': {
            'Meta': {'ordering': "('country',)", 'unique_together': "(('country', 'currency'),)", 'object_name': 'CountryXCurrency', 'db_table': "'country_x_currency'"},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['countries.Country']"}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'countries.usstate': {
            'Meta': {'ordering': "('name',)", 'object_name': 'UsState', 'db_table': "'usstate'"},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['countries']
