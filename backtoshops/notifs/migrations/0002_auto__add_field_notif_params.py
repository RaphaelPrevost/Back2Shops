# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Notif.params'
        db.add_column(u'notifs_notif', 'params',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Notif.params'
        db.delete_column(u'notifs_notif', 'params')


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
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        u'countries.country': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Country', 'db_table': "'country'"},
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'numcode': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'printable_name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'events.event': {
            'Meta': {'object_name': 'Event'},
            'desc': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'handler_is_private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'handler_method': ('django.db.models.fields.CharField', [], {'default': "'post'", 'max_length': '10', 'blank': 'True'}),
            'handler_url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'predefined_subject': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'predefined_template': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        u'notifs.notif': {
            'Meta': {'object_name': 'Notif'},
            'delivery_method': ('django.db.models.fields.IntegerField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notifs'", 'to': u"orm['events.Event']"}),
            'html_body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'html_head': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notifs'", 'to': u"orm['accounts.Brand']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'params': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'raw_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'notifs.notiftemplateimage': {
            'Meta': {'object_name': 'NotifTemplateImage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'notif': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'template_images'", 'null': 'True', 'to': u"orm['notifs.Notif']"})
        }
    }

    complete_apps = ['notifs']