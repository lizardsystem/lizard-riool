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

from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point
from os.path import basename, splitext
import logging
import math
import numpy

RDNEW = 28992
SRID = RDNEW

logger = logging.getLogger(__name__)


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
    "An uploaded file"
    objects = models.GeoManager()
    the_file = models.FileField(upload_to='upload', verbose_name='File')
    the_time = models.DateTimeField(auto_now=True, verbose_name='Time')

    @property
    def full_path(self):
        return str(self.the_file.file)

    @property
    def filename(self):
        return basename(self.the_file.name)

    @property
    def suffix(self):
        return splitext(self.the_file.name)[1]

    def __unicode__(self):
        return self.filename


class RioolBestandObject(object):
    "Common behaviour to all sewage objects"

    def __eq__(self, other):
        return self.suf_id == other.suf_id

    def __cmp__(self, other):
        if self.suf_id < other.suf_id:
            return -1
        elif self.suf_id > other.suf_id:
            return 1
        else:
            return 0

    @classmethod
    def check_record_length(cls, record, line_number):
        # S.rstrip("\r\n") will remove any EOL terminator (not just Windows)
        if len(record.rstrip("\r\n")) != cls.suf_record_length:
            raise Exception("line %d: Unexpected record length" % line_number)

    @classmethod
    def check_field_count(cls, record, line_number):
        field_count = record.count("|") + 1
        if field_count != cls.suf_fields_count:
            raise Exception("line %d: Record defines %s fields, %s expects %s" %
                (line_number, field_count, cls.suf_record_type, cls.suf_fields_count))

    @classmethod
    def parse_line_from_rioolbestand(cls, record, line_number):
        logger.debug("line %d starting with '%s...'" %
                     (line_number, record[:32]))
        cls.check_record_length(record, line_number)
        cls.check_field_count(record, line_number)
        record = ' ' + record  # makes counting positions easier
        dbobj = cls()
        for name, start, length in cls.suf_fields:
            try:
                setattr(dbobj, name, record[start:start + length])
            except ValueError:
                msg = "line %d can't set attribute %s from string '%s'" % (
                    line_number, name, record[start:start + length])
                logger.error(msg)

                # Do not hide errors, because a database
                # transaction has to be rolled back.
                raise ValueError(msg)
        return dbobj

    def update_coordinates(self, base, direction, prev):
        """override this function if xyz information of `self` is
        related to the immediately preceding object from the input
        file
        """

        pass

    def add_to_graph(self, graph):
        """add this object to a networkx graph

        this object can be a node or an edge
        """

        pass


class Put(RioolBestandObject, models.Model):
    "*PUT record"

    suf_record_length = 498
    suf_fields_count = 40
    suf_record_type = '*PUT'
    suf_fields = [
        ('CAA', 6, 30),
        ('CAB', 37, 19),
        ('CAR', 184, 2),
        ]

    objects = models.GeoManager()
    upload = models.ForeignKey('Upload')
    _CAA = models.CharField(
        db_column='caa',
        help_text="Knooppuntreferentie",
        max_length=30,
        verbose_name='CAA',
        )
    _CAB = models.PointField(
        db_column='cab',
        help_text="Knooppuntcoördinaat",
        srid=SRID,
        verbose_name='CAB',
        )
    _CAR = models.CharField(
        blank=False,
        db_column='car',
        help_text="Knooppunttype",
        max_length=2,
        null=True,
        verbose_name='CAR',
        )

    def __init__(self, *args, **kwargs):
        """initialize object with optional properties
        """
        suf_id = kwargs.get('suf_id')
        coords = kwargs.get('coords')
        if suf_id is not None:
            del kwargs['suf_id']
        if coords is not None:
            del kwargs['coords']
        super(Put, self).__init__(*args, **kwargs)
        if suf_id is not None:
            self.CAA = suf_id
        if coords is not None:
            self._CAB = Point(coords[0], coords[1])
            self.z = coords[2]

    @property
    def CAA(self):
        return self._CAA

    @CAA.setter
    def CAA(self, value):
        self._CAA = value.strip()

    @property
    def CAB(self):
        return self._CAB

    @CAB.setter
    def CAB(self, value):
        x, y = value.split('/')
        self._CAB = Point(float(x), float(y))

    @property
    def CAR(self):
        return self._CAR

    @CAR.setter
    def CAR(self, value):
        value = value.strip()
        self._CAR = value if value != '' else None

    @property
    def suf_id(self):
        "constant unique id"
        return self.CAA

    @property
    def point(self):
        return numpy.array((self.CAB.x, self.CAB.y, self.z))

    def __unicode__(self):
        return self.CAA

    class Meta:
        verbose_name_plural = "Putten"


class Riool(RioolBestandObject, models.Model):
    "*RIOO record"

    suf_record_length = 635
    suf_fields_count = 49
    suf_record_type = '*RIOO'
    suf_fields = [
        ('AAA', 7, 30),
        ('AAD', 89, 30),
        ('AAE', 120, 19),
        ('AAF', 140, 30),
        ('AAG', 171, 19),
        ('ACA', 397, 2),
        ('ACB', 400, 4),
        ('ACC', 405, 4),
        ('ACR', 623, 6),
        ('ACS', 630, 6),
        ]

    objects = models.GeoManager()
    upload = models.ForeignKey('Upload')
    _AAA = models.CharField(
        db_column='aaa',
        help_text="Strengreferentie",
        max_length=30,
        verbose_name='AAA',
        )
    _AAD = models.CharField(
        db_column='aad',
        help_text="Knooppuntreferentie 1",
        max_length=30,
        verbose_name='AAD',
        )
    _AAE = models.PointField(
        db_column='aae',
        help_text="Knooppuntcoördinaat knooppunt 1",
        srid=SRID,
        verbose_name='AAE',
        )
    _AAF = models.CharField(
        db_column='aaf',
        help_text="Knooppuntreferentie 2",
        max_length=30,
        verbose_name='AAF',
        )
    _AAG = models.PointField(
        db_column='aag',
        help_text="Knooppuntcoördinaat knooppunt 2",
        srid=SRID,
        verbose_name='AAG',
        )
    _ACR = models.FloatField(
        db_column='acr',
        help_text="BOB bij beginknoop absoluut",
        null=True,
        verbose_name='ACR',
        )
    _ACS = models.FloatField(
        db_column='acs',
        help_text="BOB bij eindknoop absoluut",
        null=True,
        verbose_name='ACS',
        )
    _the_geom = models.LineStringField(
        db_column='the_geom',
        help_text="LineString AAE -> AAG",
        srid=SRID,
        verbose_name='the_geom',
        )

    @property
    def AAA(self):
        return self._AAA

    @AAA.setter
    def AAA(self, value):
        self._AAA = value.strip()

    @property
    def AAD(self):
        return self._AAD

    @AAD.setter
    def AAD(self, value):
        self._AAD = value.strip()

    @property
    def AAE(self):
        return self._AAE

    @AAE.setter
    def AAE(self, value):
        x, y = value.split('/')
        self._AAE = Point(float(x), float(y))

    @property
    def AAF(self):
        return self._AAF

    @AAF.setter
    def AAF(self, value):
        self._AAF = value.strip()

    @property
    def AAG(self):
        return self._AAG

    @AAG.setter
    def AAG(self, value):
        x, y = value.split('/')
        self._AAG = Point(float(x), float(y))

    @property
    def ACR(self):
        if self._ACR:
            return self._ACR
        else:
            # If SUFRMB, try to find the value in the
            # corresponding SUFRIB, and vice versa.
            # Quick fix: retrieve the most recent
            # value from the database.
            try:
                riool = Riool.objects.\
                    filter(_AAA=self.AAA).\
                    filter(_ACR__isnull=False).\
                    order_by('upload__the_time')[0:1].get()
                return riool._ACR
            except Riool.DoesNotExist:
                return 0  # Or None?

    @ACR.setter
    def ACR(self, value):
        try:
            self._ACR = float(value)
        except ValueError:
            self._ACR = None

    @property
    def ACS(self):
        if self._ACS:
            return self._ACS
        else:
            # If SUFRMB, try to find the value in the
            # corresponding SUFRIB, and vice versa.
            # Quick fix: retrieve the most recent
            # value from the database.
            try:
                riool = Riool.objects.\
                    filter(_AAA=self.AAA).\
                    filter(_ACS__isnull=False).\
                    order_by('upload__the_time')[0:1].get()
                return riool._ACS
            except Riool.DoesNotExist:
                return 0  # Or None?

    @ACS.setter
    def ACS(self, value):
        try:
            self._ACS = float(value)
        except ValueError:
            self._ACS = None

    @property
    def the_geom(self):
        return self._the_geom

    @property
    def suf_id(self):
        "constant unique id"
        return self.AAA

    @property
    def suf_fk_node1(self):
        return self.AAD

    @property
    def suf_fk_node2(self):
        return self.AAF

    @property
    def suf_fk_point1(self):
        "start point, a 3D object"
        return numpy.array((self.AAE.x, self.AAE.y, (self.ACR or 0)))

    @property
    def suf_fk_point2(self):
        "end point, a 3D object"
        return numpy.array((self.AAG.x, self.AAG.y, (self.ACS or 0)))

    @property
    def form(self):
        return {'A': 'circular',
                'B': 'rectangular',
                }.get(self.ACA.strip(), 'unknown')

    @property
    def height(self):
        "height in metres (ACB is in millimetres)"
        try:
            return int(self.ACB) / 1000.0
        except ValueError:
            return self.width

    @property
    def width(self):
        "width in metres (ACC is in millimetres)"
        try:
            return int(self.ACC) / 1000.0
        except ValueError:
            logger.warn("object %s has no width" % self.suf_id)
            return None

    @property
    def length(self):
        line_vector = (self.suf_fk_point2 - self.suf_fk_point1)[: 2]
        return math.sqrt(sum(line_vector * line_vector))

    @property
    def diam(self):
        if self.form == 'circular':
            if self.height != self.width:
                logger.warn("circular object with different height (%s) and width (%s)" % (self.height, self.width))
            return self.height
        else:
            raise TypeError("accessing diam of non circular object")

    @property
    def section_surface(self):
        fun = {'A': circular_surface,
               'B': rectangular_surface,
                }.get(self.ACA.strip(), failure_function)
        return fun(self) or 0.0

    @property
    def volume(self):
        return self.length * self.section_surface

    def section_water_surface(self, flooded):
        "the area of the section of the water rotting in the pipe"

        if flooded > self.diam:
            area = self.section_surface
        elif flooded > self.diam / 2.0:
            R = self.diam / 2.0
            r = flooded - R
            area = R * R * math.acos(r / R) - r * math.sqrt(R * R - r * r)
        else:
            R = self.diam / 2.0
            h = flooded
            area = R * R * math.acos((R - h) / R) - (R - h) * math.sqrt(2 * R * h - h * h)
        return area

    def suf_fk_node(self, which=None, opposite=False):
        """return the id of either end point

        if not explicitly specified which end point to consider, look
        for the `reference` field.  a *MRIO object might have set it,
        based on the end point used during inspection.
        """

        if not opposite:
            return {1: self.suf_fk_node1,
                    2: self.suf_fk_node2}.get(which or getattr(self, 'reference'))
        else:
            return {1: self.suf_fk_node2,
                    2: self.suf_fk_node1}.get(which or getattr(self, 'reference'))

    def point(self, which, opposite):
        """return the coordinates of either end point
        """

        if opposite:
            which = 3 - which
        return {1: self.suf_fk_point1,
                2: self.suf_fk_point2}[which]

    @property
    def direction(self):
        "2D direction of segment"
        line_vector = (self.suf_fk_point2 - self.suf_fk_point1)[: 2]
        result = line_vector / self.length
        logger.debug("direction of segment is %s" % result)
        return result

    @property
    def dist(self):  # GeoDjango already has 'distance'
        return 0

    def get_knooppuntcoordinaten(self, knooppuntreferentie):
        if self.AAD == knooppuntreferentie:
            return self.AAE
        elif self.AAF == knooppuntreferentie:
            return self.AAG
        else:
            return None

    def get_knooppuntbob(self, knooppuntreferentie):
        if self.AAD == knooppuntreferentie:
            return self.ACR
        elif self.AAF == knooppuntreferentie:
            return self.ACS
        else:
            return None

    def save(self, *args, **kwargs):
        self._the_geom = LineString(self._AAE, self._AAG)
        super(Riool, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.AAA

    class Meta:
        verbose_name_plural = "Riolen"


class Rioolmeting(RioolBestandObject, models.Model):
    "*MRIO record"

    suf_record_length = 270
    suf_fields_count = 20
    suf_record_type = '*MRIO'
    suf_fields = [
        ('ZYA', 7, 8),
        ('ZYB', 16, 1),
        ('ZYE', 18, 30),
        ('ZYR', 98, 1),
        ('ZYS', 100, 1),
        ('ZYT', 102, 10),
        ('ZYU', 113, 3),
        ]

    objects = models.GeoManager()
    upload = models.ForeignKey('Upload')
    _ZYA = models.FloatField(
        db_column='zya',
        help_text="Afstand")
    ZYB = models.CharField(
        db_column='zyb',
        help_text="Referentie",
        max_length=1)
    _ZYE = models.CharField(
        db_column='zye',
        help_text="ID", # id of the referenced object
        max_length=30)
    ZYR = models.CharField(
        db_column='zyr',
        help_text="Type meting",
        max_length=1)
    ZYS = models.CharField(
        db_column='zys',
        help_text="Eenheid meetwaarde",
        max_length=1)
    _ZYT = models.FloatField(
        db_column='zyt',
        help_text="Meetwaarde")
    _ZYU = models.IntegerField(
        db_column='zyu',
        default=0,
        help_text="Macht van de vermenigvuldigingsfactor 10")

    def __unicode__(self):
        return self.suf_id

    @property
    def ZYE(self):
        return self._ZYE

    @ZYE.setter
    def ZYE(self, value):
        self._ZYE = value.strip()

    @property
    def suf_id(self):
        "constant unique id"
        return '%s:%08.2f' % (self.suf_fk_edge, self.dist)

    @property
    def suf_fk_edge(self):
        return self.ZYE

    @property
    def dist(self):  # GeoDjango already has 'distance'
        return self.ZYA

    @property
    def reference(self):
        return int(self.ZYB.strip())

    @property
    def value(self):
        return self.ZYT * 10 ** self.ZYU

    @property
    def z(self):
        return self.point[2]

    @property
    def measurement_type(self):
        "combined codes for type and unit"
        return self.ZYR + self.ZYS

    @property
    def ZYA(self):
        return self._ZYA

    @ZYA.setter
    def ZYA(self, value):
        self._ZYA = float(value)

    @property
    def ZYT(self):
        return self._ZYT

    @ZYT.setter
    def ZYT(self, value):
        self._ZYT = float(value)

    @property
    def ZYU(self):
        return self._ZYU

    @ZYU.setter
    def ZYU(self, value):
        try:
            self._ZYU = int(value)
        except ValueError:
            self._ZYU = 0

    def save(self, *args, **kwargs):
        ## Not sure whether we want to save these into the database.
        ## It takes a long time, because it involves many records.
        pass

    def update_coordinates(self, base, direction, prev):
        """compute 3D coordinates of self

        the 3D coordinates of self can be specified in quite a few
        different ways. we do not support all of them.

        TODO: check and fix the calculation.
        """

        logger.debug("examining measurement %s:%s:%s" % (
                self.measurement_type, self.dist, self.value))

        prev_dist = math.sqrt(sum(pow(prev[:2] - base[:2], 2)))

        if self.measurement_type == 'AE':
            # Slope|Degrees
            self.point = prev + (
                self.dist - prev_dist) * numpy.array((
                direction[0], direction[1], math.tan(self.value / 180.0 * math.pi)))
        elif self.measurement_type == 'AF':
            # Slope|Percent
            self.point = prev + (
                self.dist - prev_dist) * numpy.array((
                direction[0], direction[1], self.value / 100.0))
        elif self.measurement_type == 'BB':
            ## Absolute|metres (useful internally, not used by customer)
            self.point = numpy.array(tuple(
                    (base + self.dist * direction)[:2])
                                     + (self.value,))
        elif self.measurement_type == 'CB':
            # Relative|metres
            ## offset is relative to an ideal straight start-end
            ## connection
            self.point = (base
                          + self.dist * direction
                          + numpy.array((0, 0, self.value)))
        else:
            logger.warning("unrecognized, not supported")
            pass

        logger.debug("updated to %s" % self.point)
