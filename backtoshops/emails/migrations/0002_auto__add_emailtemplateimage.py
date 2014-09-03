# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EmailTemplateImage'
        db.create_table(u'emails_emailtemplateimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='images', null=True, to=orm['emails.EmailTemplate'])),
            ('image', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100)),
        ))
        db.send_create_signal(u'emails', ['EmailTemplateImage'])


    def backwards(self, orm):
        # Deleting model 'EmailTemplateImage'
        db.delete_table(u'emails_emailtemplateimage')


    models = {
        u'emails.emailtemplate': {
            'Meta': {'object_name': 'EmailTemplate'},
            'html_body': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'html_head': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'emails.emailtemplateimage': {
            'Meta': {'object_name': 'EmailTemplateImage'},
            'email': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'images'", 'null': 'True', 'to': u"orm['emails.EmailTemplate']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['emails']