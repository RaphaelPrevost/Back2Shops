# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Notif'
        db.create_table(u'notifs_notif', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('mother_brand', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notifs', to=orm['accounts.Brand'])),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='notifs', to=orm['events.Event'])),
            ('delivery_method', self.gf('django.db.models.fields.IntegerField')()),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('html_head', self.gf('django.db.models.fields.TextField')(default='')),
            ('html_body', self.gf('django.db.models.fields.TextField')(default='')),
            ('raw_text', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal(u'notifs', ['Notif'])

        # Adding model 'NotifTemplateImage'
        db.create_table(u'notifs_notiftemplateimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('notif', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='template_images', null=True, to=orm['notifs.Notif'])),
            ('image', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100)),
        ))
        db.send_create_signal(u'notifs', ['NotifTemplateImage'])


    def backwards(self, orm):
        # Deleting model 'Notif'
        db.delete_table(u'notifs_notif')

        # Deleting model 'NotifTemplateImage'
        db.delete_table(u'notifs_notiftemplateimage')


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
        u'events.event': {
            'Meta': {'object_name': 'Event'},
            'desc': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'handler_is_private': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'handler_method': ('django.db.models.fields.CharField', [], {'default': "'post'", 'max_length': '10', 'blank': 'True'}),
            'handler_url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'notifs.notif': {
            'Meta': {'object_name': 'Notif'},
            'delivery_method': ('django.db.models.fields.IntegerField', [], {}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notifs'", 'to': u"orm['events.Event']"}),
            'html_body': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'html_head': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mother_brand': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notifs'", 'to': u"orm['accounts.Brand']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'raw_text': ('django.db.models.fields.TextField', [], {'default': "''"}),
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