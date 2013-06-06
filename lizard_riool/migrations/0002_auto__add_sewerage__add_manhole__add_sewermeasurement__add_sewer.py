# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Sewerage'
        db.create_table('lizard_riool_sewerage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rib', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('rmb', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('lizard_riool', ['Sewerage'])

        # Adding model 'Manhole'
        db.create_table('lizard_riool_manhole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('sink', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('the_geom', self.gf('django.contrib.gis.db.models.fields.PointField')()),
        ))
        db.send_create_signal('lizard_riool', ['Manhole'])

        # Adding model 'SewerMeasurement'
        db.create_table('lizard_riool_sewermeasurement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sewer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Sewer'])),
            ('distance', self.gf('django.db.models.fields.FloatField')()),
            ('virtual', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('water_level', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('flooded_pct', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('bob', self.gf('django.db.models.fields.FloatField')()),
            ('obb', self.gf('django.db.models.fields.FloatField')()),
            ('the_geom', self.gf('django.contrib.gis.db.models.fields.PointField')()),
        ))
        db.send_create_signal('lizard_riool', ['SewerMeasurement'])

        # Adding model 'Sewer'
        db.create_table('lizard_riool_sewer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sewerage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['lizard_riool.Sewerage'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('diameter', self.gf('django.db.models.fields.FloatField')()),
            ('manhole1', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['lizard_riool.Manhole'])),
            ('manhole2', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['lizard_riool.Manhole'])),
            ('bob1', self.gf('django.db.models.fields.FloatField')()),
            ('bob2', self.gf('django.db.models.fields.FloatField')()),
            ('the_geom', self.gf('django.contrib.gis.db.models.fields.LineStringField')()),
        ))
        db.send_create_signal('lizard_riool', ['Sewer'])


    def backwards(self, orm):
        # Deleting model 'Sewerage'
        db.delete_table('lizard_riool_sewerage')

        # Deleting model 'Manhole'
        db.delete_table('lizard_riool_manhole')

        # Deleting model 'SewerMeasurement'
        db.delete_table('lizard_riool_sewermeasurement')

        # Deleting model 'Sewer'
        db.delete_table('lizard_riool_sewer')


    models = {
        'lizard_riool.manhole': {
            'Meta': {'object_name': 'Manhole'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sink': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'the_geom': ('django.contrib.gis.db.models.fields.PointField', [], {})
        },
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
        'lizard_riool.sewer': {
            'Meta': {'object_name': 'Sewer'},
            'bob1': ('django.db.models.fields.FloatField', [], {}),
            'bob2': ('django.db.models.fields.FloatField', [], {}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'diameter': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manhole1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_riool.Manhole']"}),
            'manhole2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['lizard_riool.Manhole']"}),
            'sewerage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Sewerage']"}),
            'the_geom': ('django.contrib.gis.db.models.fields.LineStringField', [], {})
        },
        'lizard_riool.sewerage': {
            'Meta': {'object_name': 'Sewerage'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rib': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'rmb': ('django.db.models.fields.files.FileField', [], {'max_length': '100'})
        },
        'lizard_riool.sewermeasurement': {
            'Meta': {'object_name': 'SewerMeasurement'},
            'bob': ('django.db.models.fields.FloatField', [], {}),
            'distance': ('django.db.models.fields.FloatField', [], {}),
            'flooded_pct': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obb': ('django.db.models.fields.FloatField', [], {}),
            'sewer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['lizard_riool.Sewer']"}),
            'the_geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'virtual': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'water_level': ('django.db.models.fields.FloatField', [], {'null': 'True'})
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