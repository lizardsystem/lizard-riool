# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Upload'
        db.create_table('lizard_riool_upload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('the_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('the_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('lizard_riool', ['Upload'])

        # Adding model 'Put'
        db.create_table('lizard_riool_put', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('_CAA', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='caa')),
            ('_CAB', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992, db_column='cab')),
            ('_CAR', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, db_column='car')),
        ))
        db.send_create_signal('lizard_riool', ['Put'])

        # Adding model 'Riool'
        db.create_table('lizard_riool_riool', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('_AAA', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='aaa')),
            ('_AAD', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='aad')),
            ('_AAE', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992, db_column='aae')),
            ('_AAF', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='aaf')),
            ('_AAG', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992, db_column='aag')),
            ('_ACR', self.gf('django.db.models.fields.FloatField')(null=True, db_column='acr')),
            ('_ACS', self.gf('django.db.models.fields.FloatField')(null=True, db_column='acs')),
            ('_the_geom', self.gf('django.contrib.gis.db.models.fields.LineStringField')(srid=28992, db_column='the_geom')),
        ))
        db.send_create_signal('lizard_riool', ['Riool'])

        # Adding model 'Rioolmeting'
        db.create_table('lizard_riool_rioolmeting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('_ZYA', self.gf('django.db.models.fields.FloatField')(db_column='zya')),
            ('ZYB', self.gf('django.db.models.fields.CharField')(max_length=1, db_column='zyb')),
            ('_ZYE', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='zye')),
            ('ZYR', self.gf('django.db.models.fields.CharField')(max_length=1, db_column='zyr')),
            ('ZYS', self.gf('django.db.models.fields.CharField')(max_length=1, db_column='zys')),
            ('_ZYT', self.gf('django.db.models.fields.FloatField')(db_column='zyt')),
            ('_ZYU', self.gf('django.db.models.fields.IntegerField')(default=0, db_column='zyu')),
        ))
        db.send_create_signal('lizard_riool', ['Rioolmeting'])

        # Adding model 'SinkForUpload'
        db.create_table('lizard_riool_sinkforupload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'], unique=True)),
            ('sink', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Put'])),
        ))
        db.send_create_signal('lizard_riool', ['SinkForUpload'])

        # Adding model 'StoredGraph'
        db.create_table('lizard_riool_storedgraph', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rmb', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('suf_id', self.gf('django.db.models.fields.CharField')(max_length=39)),
            ('xy', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992)),
            ('x', self.gf('django.db.models.fields.FloatField')()),
            ('y', self.gf('django.db.models.fields.FloatField')()),
            ('flooded_percentage', self.gf('django.db.models.fields.FloatField')(null=True)),
        ))
        db.send_create_signal('lizard_riool', ['StoredGraph'])

        # Adding unique constraint on 'StoredGraph', fields ['rmb', 'x', 'y']
        db.create_unique('lizard_riool_storedgraph', ['rmb_id', 'x', 'y'])


    def backwards(self, orm):
        # Removing unique constraint on 'StoredGraph', fields ['rmb', 'x', 'y']
        db.delete_unique('lizard_riool_storedgraph', ['rmb_id', 'x', 'y'])

        # Deleting model 'Upload'
        db.delete_table('lizard_riool_upload')

        # Deleting model 'Put'
        db.delete_table('lizard_riool_put')

        # Deleting model 'Riool'
        db.delete_table('lizard_riool_riool')

        # Deleting model 'Rioolmeting'
        db.delete_table('lizard_riool_rioolmeting')

        # Deleting model 'SinkForUpload'
        db.delete_table('lizard_riool_sinkforupload')

        # Deleting model 'StoredGraph'
        db.delete_table('lizard_riool_storedgraph')


    models = {
        'lizard_riool.put': {
            'Meta': {'object_name': 'Put'},
            '_CAA': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'caa'"}),
            '_CAB': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '28992', 'db_column': "'cab'"}),
            '_CAR': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_column': "'car'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'upload': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Upload']"})
        },
        'lizard_riool.riool': {
            'Meta': {'object_name': 'Riool'},
            '_AAA': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'aaa'"}),
            '_AAD': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'aad'"}),
            '_AAE': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '28992', 'db_column': "'aae'"}),
            '_AAF': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'aaf'"}),
            '_AAG': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '28992', 'db_column': "'aag'"}),
            '_ACR': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_column': "'acr'"}),
            '_ACS': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_column': "'acs'"}),
            '_the_geom': ('django.contrib.gis.db.models.fields.LineStringField', [], {'srid': '28992', 'db_column': "'the_geom'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'upload': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Upload']"})
        },
        'lizard_riool.rioolmeting': {
            'Meta': {'object_name': 'Rioolmeting'},
            'ZYB': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_column': "'zyb'"}),
            'ZYR': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_column': "'zyr'"}),
            'ZYS': ('django.db.models.fields.CharField', [], {'max_length': '1', 'db_column': "'zys'"}),
            '_ZYA': ('django.db.models.fields.FloatField', [], {'db_column': "'zya'"}),
            '_ZYE': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'zye'"}),
            '_ZYT': ('django.db.models.fields.FloatField', [], {'db_column': "'zyt'"}),
            '_ZYU': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_column': "'zyu'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'upload': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Upload']"})
        },
        'lizard_riool.sinkforupload': {
            'Meta': {'object_name': 'SinkForUpload'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sink': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Put']"}),
            'upload': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Upload']", 'unique': 'True'})
        },
        'lizard_riool.storedgraph': {
            'Meta': {'unique_together': "(('rmb', 'x', 'y'),)", 'object_name': 'StoredGraph'},
            'flooded_percentage': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rmb': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Upload']"}),
            'suf_id': ('django.db.models.fields.CharField', [], {'max_length': '39'}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'xy': ('django.contrib.gis.db.models.fields.PointField', [], {'srid': '28992'}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_riool.upload': {
            'Meta': {'object_name': 'Upload'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'the_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'the_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['lizard_riool']