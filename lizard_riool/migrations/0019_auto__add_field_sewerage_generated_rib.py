# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Sewerage.generated_rib'
        db.add_column('lizard_riool_sewerage', 'generated_rib',
                      self.gf('django.db.models.fields.FilePathField')(max_length=400, null=True, path='/home/remcogerlich/src/git/almere-site/var/lizard_riool/sewerages'),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Sewerage.generated_rib'
        db.delete_column('lizard_riool_sewerage', 'generated_rib')


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
            'generated_rib': ('django.db.models.fields.FilePathField', [], {'max_length': '400', 'null': 'True', 'path': "'/home/remcogerlich/src/git/almere-site/var/lizard_riool/sewerages'"}),
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