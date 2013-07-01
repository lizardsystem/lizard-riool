# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'StoredGraph', fields ['rmb', 'x', 'y']
        db.delete_unique('lizard_riool_storedgraph', ['rmb_id', 'x', 'y'])

        # Deleting model 'Put'
        db.delete_table('lizard_riool_put')

        # Deleting model 'SinkForUpload'
        db.delete_table('lizard_riool_sinkforupload')

        # Deleting model 'Riool'
        db.delete_table('lizard_riool_riool')

        # Deleting model 'StoredGraph'
        db.delete_table('lizard_riool_storedgraph')

        # Deleting model 'Rioolmeting'
        db.delete_table('lizard_riool_rioolmeting')


    def backwards(self, orm):
        # Adding model 'Put'
        db.create_table('lizard_riool_put', (
            ('_CAR', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, db_column='car')),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('_CAA', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='caa')),
            ('_CAB', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992, db_column='cab')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('lizard_riool', ['Put'])

        # Adding model 'SinkForUpload'
        db.create_table('lizard_riool_sinkforupload', (
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'], unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sink', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Put'])),
        ))
        db.send_create_signal('lizard_riool', ['SinkForUpload'])

        # Adding model 'Riool'
        db.create_table('lizard_riool_riool', (
            ('_AAA', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='aaa')),
            ('_ACS', self.gf('django.db.models.fields.FloatField')(null=True, db_column='acs')),
            ('_ACR', self.gf('django.db.models.fields.FloatField')(null=True, db_column='acr')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('_the_geom', self.gf('django.contrib.gis.db.models.fields.LineStringField')(srid=28992, db_column='the_geom')),
            ('_AAG', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992, db_column='aag')),
            ('_AAF', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='aaf')),
            ('_AAE', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992, db_column='aae')),
            ('_AAD', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='aad')),
        ))
        db.send_create_signal('lizard_riool', ['Riool'])

        # Adding model 'StoredGraph'
        db.create_table('lizard_riool_storedgraph', (
            ('flooded_percentage', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('rmb', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('suf_id', self.gf('django.db.models.fields.CharField')(max_length=39)),
            ('y', self.gf('django.db.models.fields.FloatField')()),
            ('xy', self.gf('django.contrib.gis.db.models.fields.PointField')(srid=28992)),
            ('x', self.gf('django.db.models.fields.FloatField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('lizard_riool', ['StoredGraph'])

        # Adding unique constraint on 'StoredGraph', fields ['rmb', 'x', 'y']
        db.create_unique('lizard_riool_storedgraph', ['rmb_id', 'x', 'y'])

        # Adding model 'Rioolmeting'
        db.create_table('lizard_riool_rioolmeting', (
            ('_ZYA', self.gf('django.db.models.fields.FloatField')(db_column='zya')),
            ('ZYB', self.gf('django.db.models.fields.CharField')(max_length=1, db_column='zyb')),
            ('ZYS', self.gf('django.db.models.fields.CharField')(max_length=1, db_column='zys')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ZYR', self.gf('django.db.models.fields.CharField')(max_length=1, db_column='zyr')),
            ('_ZYU', self.gf('django.db.models.fields.IntegerField')(default=0, db_column='zyu')),
            ('_ZYT', self.gf('django.db.models.fields.FloatField')(db_column='zyt')),
            ('upload', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Upload'])),
            ('_ZYE', self.gf('django.db.models.fields.CharField')(max_length=30, db_column='zye')),
        ))
        db.send_create_signal('lizard_riool', ['Rioolmeting'])


    models = {
        'lizard_riool.manhole': {
            'Meta': {'object_name': 'Manhole'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'ground_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sewerage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Sewerage']"}),
            'sink': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'the_geom': ('django.contrib.gis.db.models.fields.PointField', [], {})
        },
        'lizard_riool.sewer': {
            'Meta': {'object_name': 'Sewer'},
            'bob1': ('django.db.models.fields.FloatField', [], {}),
            'bob2': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'diameter': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manhole1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_riool.Manhole']"}),
            'manhole2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_riool.Manhole']"}),
            'quality': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'sewerage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Sewerage']"}),
            'shape': ('django.db.models.fields.CharField', [], {'default': "'A'", 'max_length': '1'}),
            'the_geom': ('django.contrib.gis.db.models.fields.LineStringField', [], {}),
            'the_geom_length': ('django.db.models.fields.FloatField', [], {})
        },
        'lizard_riool.sewerage': {
            'Meta': {'object_name': 'Sewerage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'rib': ('django.db.models.fields.FilePathField', [], {'max_length': '400', 'null': 'True', 'path': "'/home/remcogerlich/src/git/almere-site/var/lizard_riool/sewerages'"}),
            'rmb': ('django.db.models.fields.FilePathField', [], {'max_length': '400', 'null': 'True', 'path': "'/home/remcogerlich/src/git/almere-site/var/lizard_riool/sewerages'"})
        },
        'lizard_riool.sewermeasurement': {
            'Meta': {'object_name': 'SewerMeasurement'},
            'bob': ('django.db.models.fields.FloatField', [], {}),
            'dist': ('django.db.models.fields.FloatField', [], {}),
            'flooded_pct': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obb': ('django.db.models.fields.FloatField', [], {}),
            'sewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'measurements'", 'to': "orm['lizard_riool.Sewer']"}),
            'the_geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'virtual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'water_level': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        },
        'lizard_riool.upload': {
            'Meta': {'object_name': 'Upload'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True'}),
            'the_file': ('django.db.models.fields.FilePathField', [], {'path': "'/home/remcogerlich/src/git/almere-site/var/lizard_riool/uploads'", 'max_length': '400'}),
            'the_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'lizard_riool.uploadedfileerror': {
            'Meta': {'ordering': "('uploaded_file', 'line')", 'object_name': 'UploadedFileError'},
            'error_message': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'uploaded_file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Upload']"})
        }
    }

    complete_apps = ['lizard_riool']