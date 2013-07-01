# encoding: utf-8
#
# Copyright 2011, 2012 Nelen & Schuurmans.
#
# This file is part of lizard-riool.
#
# lizard-riool is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lizard-riool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with lizard-riool. If not, see <http://www.gnu.org/licenses/>.
#

"""Module docstring.

This serves as a long usage message.
"""

from os.path import basename, splitext
import logging
import math
import os
import shutil

from django.contrib.gis.db import models
from django.conf import settings

from sufriblib.parsers import enumerate_file

from lizard_riool.waar import WAAR


RDNEW = 28992
SRID = RDNEW

logger = logging.getLogger(__name__)

# Colors from http://www.herethere.net/~samson/php/color_gradient/

CLASSES = (
    ('A', '0%-10%',   0.00, 0.10, '00ff00'),  # green
    ('B', '10%-25%',  0.10, 0.25, '3fbf00'),
    ('C', '25%-50%',  0.25, 0.50, '7f7f00'),
    ('D', '50%-75%',  0.50, 0.75, 'bf3f00'),
    ('E', '75%-100%', 0.75, 1.01, 'ff0000'),  # red
    ('?', 'Onbekend', 1.00, 0.00, '000000'),  # black
)


def get_class_boundaries(pct):
    "Return the class and its boundaries for a given fraction."
    for klasse, _, min_pct, max_pct, _ in CLASSES:
        if pct >= min_pct and pct < max_pct:
            return klasse, min_pct, max_pct


def circular_surface(obj):
    """return section surface of obj with diam
    """

    return math.pow(obj.diam, 2) / 4.0 * math.pi


def rectangular_surface(obj):
    """return section surface of obj with height, width
    """

    return obj.height * obj.width


def failure_function(*argv, **kwargs):
    """log the failure and return None
    """

    logger.warn("invoking failure function!")


class Upload(models.Model):
    NOT_PROCESSED_YET = 1
    BEING_PROCESSED = 2
    UNSUCCESSFUL = 3
    SUCCESSFUL = 4

    STATUS_CHOICES = (
        (NOT_PROCESSED_YET, "Nog niet verwerkt"),
        (BEING_PROCESSED, "Wordt verwerkt"),
        (UNSUCCESSFUL, "Afgekeurd"),
        (SUCCESSFUL, "Goedgekeurd"))

    BASE_PATH = os.path.join(
        settings.BUILDOUT_DIR, 'var', 'lizard_riool', 'uploads')

    "An uploaded file"
    objects = models.GeoManager()
    the_file = models.FilePathField(
        path=BASE_PATH, verbose_name='File',
        max_length=400)  # Note this is including the path, and we
                         # really really don't want to run into the
                         # limit
    
    the_time = models.DateTimeField(auto_now=True, verbose_name='Time')

    status = models.IntegerField(
        choices=STATUS_CHOICES, default=1, null=True)

    def status_string(self):
        """For use in Javascript (beheer.js)"""
        return {
            1: "not_being_processed_yet",
            2: "being_processed",
            3: "with_errors",
            4: "successful"
            }.get(self.status, "unknown")

    def move_file(self, path):
        """Move file to a nice place to stay, where there won't be
        other files with accidentally identical names. Saves this
        object. Twice, if it doesn't have an id yet."""
        if not self.id:
            self.save()

        directory = os.path.join(Upload.BASE_PATH, str(self.id))

        if not os.path.exists(directory):
            os.makedirs(directory)

        newpath = os.path.join(directory, os.path.basename(path))

        shutil.move(path, newpath)
        self.the_file = newpath
        self.save()

    def delete(self):
        """Delete this Upload including the file and directory"""
        shutil.rmtree(
            os.path.join(Upload.BASE_PATH, str(self.id)),
            ignore_errors=True)

        return super(Upload, self).delete()

    @property
    def full_path(self):
        return str(self.the_file)

    @property
    def filename(self):
        return basename(self.the_file)

    @property
    def suffix(self):
        """Return extension including the ."""
        return splitext(self.the_file)[1]

    def __unicode__(self):
        return self.filename

    def find_relevant_rib(self):
        """Find an Upload with status 1 that has the same filename as this RMB,
        case insensitive, except with .RIB instead of .RMB. Return it.

        If no such Upload is found, return None.

        If this is not a .RMB file, raise ValueError."""
        if not self.filename.lower().endswith(".rmb"):
            raise ValueError("find_relevant_rib() called on a non-rmb Upload")

        filename = self.filename.lower()[:-4]

        for upload in Upload.objects.filter(status=Upload.NOT_PROCESSED_YET):
            if not upload.filename.lower().endswith(".rib"):
                continue
            if upload.filename.lower()[:-4] == filename:
                return upload

        return None

    def record_error(self, error_message, line_number=0):
        """Record error message. Does not set state yet, more errors
        may come."""
        UploadedFileError.objects.create(
            uploaded_file=self,
            line=line_number or 0,  # Save 0 if line_number is None
            error_message=error_message[:300])

    def record_errors(self, errorlist):
        """Errorlist is an iterable of sufriblib.errors.Error objects."""
        for e in errorlist:
            self.record_error(e.message, e.line_number)

    def error_description(self):
        if self.status != Upload.UNSUCCESSFUL:
            return None

        errors = list(UploadedFileError.objects.filter(
                uploaded_file=self))

        if not errors:
            return None
        if len(errors) == 1:
            return errors[0].message()
        else:
            return ("{0} fouten, eerste is: {1}"
                    .format(len(errors), errors[0].message()))

    def set_being_processed(self):
        self.status = Upload.BEING_PROCESSED
        self.save()

    def set_unsuccessful(self):
        self.status = Upload.UNSUCCESSFUL
        self.save()

    def set_successful(self):
        self.status = Upload.SUCCESSFUL
        self.save()


class UploadedFileError(models.Model):
    uploaded_file = models.ForeignKey(Upload)
    line = models.IntegerField(default=0)
    error_message = models.CharField(max_length=300)

    class Meta:
        ordering = ('uploaded_file', 'line')

    def message(self):
        if self.line > 0:
            return (
                "Regel {line}: {error_message}".
                format(line=self.line,
                       error_message=self.error_message))
        else:
            return self.error_message

    def __unicode__(self):
        return "{file}: {message}".format(
            file=self.uploaded_file.the_file,
            message=self.message())


class Sewerage(models.Model):
    """A system of sewers.

    A sewerage that is not `active`, will not be visible in the main menu.
    It is considered to be in an archived state (all results are still
    present in the database).

    """
    BASE_PATH = os.path.join(
        settings.BUILDOUT_DIR, 'var', 'lizard_riool', 'sewerages')

    name = models.CharField(max_length=128)
    rib = models.FilePathField(
        path=BASE_PATH, verbose_name='RIB File', null=True,
        max_length=400)  # Note this is including the path, and we
                         # really really don't want to run into the
                         # limit

    rmb = models.FilePathField(
        path=BASE_PATH, verbose_name='RMB File', null=True,
        max_length=400)  # Note this is including the path, and we
                         # really really don't want to run into the
                         # limit

    generated_rib = models.FilePathField(
        path=BASE_PATH, verbose_name='Generated RIB File', null=True,
        max_length=400)

    active = models.BooleanField(default=True)

    def move_files(self, rib_path, rmb_path):
        """Move file to a nice place to stay, where there won't be
        other files with accidentally identical names. Saves this
        object. Twice, if it doesn't have an id yet."""
        if not self.id:
            self.save()

        directory = os.path.join(Sewerage.BASE_PATH, str(self.id))

        if not os.path.exists(directory):
            os.makedirs(directory)

        new_rib_path = os.path.join(directory, os.path.basename(rib_path))
        shutil.move(rib_path, new_rib_path)
        self.rib = new_rib_path

        new_rmb_path = os.path.join(directory, os.path.basename(rmb_path))
        shutil.move(rmb_path, new_rmb_path)
        self.rmb = new_rmb_path

        self.save()

    def generate_rib(self):
        """When everything is saved and moved, a "result" RIB file is
        generated."""
        self.generated_rib = os.path.join(
            os.path.dirname(self.rib),
            os.path.splitext(os.path.basename(self.rmb))[0] + '_results.rib')

        with open(self.generated_rib, 'w') as rib:
            for line in self._generate_generated_rib_lines(
                enumerate_file(self.rmb)):
                rib.write(line + "\n")

        self.save()

    def _generate_generated_rib_lines(self, file_enumerator):
        for line_number, line in file_enumerator:
            if line.startswith("*ALGE"):
                yield line  # Copy *ALGE lines
            elif line.startswith("*RIOO"):
                yield line  # Copy *RIOO lines

                # After the *RIOO lines, add the relevant *WAAR lines
                sewer_code = line[6:36].strip()
                try:
                    sewer = Sewer.objects.get(
                        sewerage=self, code=sewer_code)
                    for extra_waar_line in sewer.generate_waar_lines():
                        yield extra_waar_line
                except Sewer.DoesNotExist:
                    pass  # Don't print *WAAR records for this one

    def delete(self):
        """Delete this Sewerage -- also deletes the entire directory
        that contains its files!"""
        shutil.rmtree(
            os.path.join(Sewerage.BASE_PATH, str(self.id)),
            ignore_errors=True)

        return super(Sewerage, self).delete()

    @property
    def rib_filename(self):
        return self.rib and os.path.basename(self.rib)

    @property
    def rmb_filename(self):
        return self.rmb and os.path.basename(self.rmb)

    @property
    def generated_rib_filename(self):
        return self.generated_rib and os.path.basename(self.generated_rib)

    def __unicode__(self):
        return self.name


class Manhole(models.Model):
    "A sewer manhole."
    sewerage = models.ForeignKey(Sewerage)
    code = models.CharField(max_length=30)
    sink = models.IntegerField(default=0)
    ground_level = models.FloatField(blank=True, null=True)
    the_geom = models.PointField()
    objects = models.GeoManager()

    @property
    def is_sink(self):
        "Return True if this manhole is a sink."
        return bool(self.sink)

    def __unicode__(self):
        return self.code


class Sewer(models.Model):
    "A pipe connecting two manholes."

    QUALITY_UNKNOWN = 1
    QUALITY_RELIABLE = 2
    QUALITY_UNRELIABLE = 3

    QUALITY_CHOICES = (
        (QUALITY_UNKNOWN, 'Unknown'),
        (QUALITY_RELIABLE, 'Reliable'),
        (QUALITY_UNRELIABLE, 'Unreliable'),
    )

    SHAPE_CIRCLE = 'A'
    SHAPE_RECTANGULAR = 'B'
    SHAPE_OTHER = 'Z'

    SHAPE_CHOICES = (
        (SHAPE_CIRCLE, 'Circular'),
        (SHAPE_RECTANGULAR, 'Rectangular'),
        (SHAPE_OTHER, 'Other'),
    )

    sewerage = models.ForeignKey(Sewerage)
    code = models.CharField(max_length=30)
    quality = models.IntegerField(
        choices=QUALITY_CHOICES,
        default=QUALITY_UNKNOWN,
    )
    shape = models.CharField(
        max_length=1,
        choices=SHAPE_CHOICES,
        default=SHAPE_CIRCLE,
    )
    diameter = models.FloatField()
    manhole1 = models.ForeignKey(Manhole, related_name="+")
    manhole2 = models.ForeignKey(Manhole, related_name="+")
    bob1 = models.FloatField()
    bob2 = models.FloatField()
    the_geom_length = models.FloatField()  # in meters
    the_geom = models.LineStringField()
    objects = models.GeoManager()

    @property
    def is_rectangular(self):
        return (self.shape == Sewer.SHAPE_RECTANGULAR)

    def judge_quality(self, measurements):
        """We need some measure of quality. We use:
        - The range from min(dist of measurements) to the max
          must be at least 90% of the length of this sewer
        - Over that range, there must be at least 1 measurement
          per meter

        If both those are satisfied, this sewer is reliable, otherwise
        unreliable."""
        if not measurements:
            self.quality = Sewer.QUALITY_UNKNOWN
            return

        mindist = min(m.dist for m in measurements)
        maxdist = max(m.dist for m in measurements)

        # Restrict it to only inside the sewer's length, to prevent
        # strange dists resulting in good quality
        mindist = max(0.0, mindist)
        maxdist = min(maxdist, self.the_geom_length)

        measurements_length = maxdist - mindist

        proportion = measurements_length / self.the_geom_length

        measurements_per_m = len(measurements) / measurements_length

        if proportion >= 0.9 and measurements_per_m >= 1:
            self.quality = Sewer.QUALITY_RELIABLE
        else:
            self.quality = Sewer.QUALITY_UNRELIABLE

    def generate_waar_lines(self):
        """Construct and return *WAAR records for in a RIB file.

        Each *MRIO can be classified according to its percentage flooded.
        The class boundaries are printed in the ZZI and ZZJ fields of
        the *WAAR record. Only *WAAR records that mark a change of
        class are returned.
        """

        prev_klasse = None
        for measurement in SewerMeasurement.objects.filter(
            sewer=self).order_by('dist'):
            pct = measurement.flooded_pct
            klasse, min_pct, max_pct = get_class_boundaries(pct)
            if klasse != prev_klasse:
                waar = WAAR()
                waar.ZZA = measurement.dist
                waar.ZZB = "1"
                waar.ZZE = self.code
                waar.ZZF = 'BDD'
                waar.ZZI = min_pct
                waar.ZZJ = max_pct
                waar.ZZV = 'Door Lizard Riool Toolkit'
                yield str(waar)
                prev_klasse = klasse


class SewerMeasurement(models.Model):
    "A measurement somewhere in a sewer pipe."
    sewer = models.ForeignKey(Sewer, related_name="measurements")
    # Use `dist` - `distance` clashes with the GEOS API.
    dist = models.FloatField()
    virtual = models.BooleanField(default=False)
    water_level = models.FloatField(null=True)  # Relative to NAP.
    flooded_pct = models.FloatField(null=True)
    bob = models.FloatField()   # bob <= water_level <= obb
    obb = models.FloatField()
    the_geom = models.PointField()
    objects = models.GeoManager()

    def set_water_level(self, water_level):
        # Restrict water_level so that it's in between bob and obb
        if water_level is None:
            self.water_level = None
        else:
            self.water_level = max(
                self.bob,
                min(self.obb, water_level))

    def compute_flooded_pct(self, use_sewer=None):
        if self.water_level is None:
            self.flooded_pct = None
            return

        depth = self.water_level - self.bob

        if depth <= 0.0:
            self.flooded_pct = 0
            return

        diameter = self.obb - self.bob

        if depth >= diameter:
            self.flooded_pct = 1
            return

        # Sewer to use can be passed as an argument for speed
        sewer = use_sewer or self.sewer
        if sewer.is_rectangular:
            self.flooded_pct = depth / diameter
            return

        # Assume circular
        area = math.pi * ((diameter / 2) ** 2)
        if depth == diameter / 2:
            percentage = 0.5
        elif depth < diameter / 2:
            percentage = disc_segment(
                radius=diameter / 2, height=depth) / area
        else:
            percentage = (area - disc_segment(
                    radius=diameter / 2,
                    height=diameter - depth)) / area

        self.flooded_pct = percentage


def disc_segment(radius, height):
    """Compute the area of a disc segment with height 'height' in a
    circle of radius 'radius', when height < radius"""

    assert height < radius
    assert height != 0
    assert radius != 0

    radius = float(radius)
    height = float(height)

    # Using Wikipedia, http://en.wikipedia.org/wiki/Circular_segment .

    # The angle is 2 arccos (d/R)   (and d = R-h).
    angle = 2 * math.acos((radius - height) / radius)

    # And the area is R^2/2 (angle - sin angle)
    area = ((radius ** 2) / 2) * (angle - math.sin(angle))

    return area
