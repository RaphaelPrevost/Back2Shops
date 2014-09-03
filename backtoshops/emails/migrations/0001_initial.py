# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EmailTemplate'
        db.create_table(u'emails_emailtemplate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('html_head', self.gf('django.db.models.fields.TextField')(default='')),
            ('html_body', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal(u'emails', ['EmailTemplate'])


    def backwards(self, orm):
        # Deleting model 'EmailTemplate'
        db.delete_table(u'emails_emailtemplate')


    models = {
        u'emails.emailtemplate': {
            'Meta': {'object_name': 'EmailTemplate'},
            'html_body': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'html_head': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['emails']