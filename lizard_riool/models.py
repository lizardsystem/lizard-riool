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
    def filename(self):
        return basename(self.the_file.name)

    @property
    def suffix(self):
        return splitext(self.the_file.name)[1]

    def __unicode__(self):
        return self.filename


class RioolBestandObject(object):
    "Common behaviour to all sewage objects"

    @classmethod
    def check_record_length(cls, record):
        # S.rstrip("\r\n") will remove any EOL terminator (not just Windows)
        if len(record.rstrip("\r\n")) != cls.suf_record_length:
            raise Exception("Unexpected record length")

    @classmethod
    def check_field_count(cls, record):
        field_count = record.count("|") + 1
        if field_count != cls.suf_fields_count:
            raise Exception("Record defines %s fields, %s expects %s" %
                (field_count, cls.suf_record_type, cls.suf_fields_count))

    @classmethod
    def parse_line_from_rioolbestand(cls, record, line_number):
        logger.debug("line %d starting with '%s...'" %
                     (line_number, record[:32]))
        cls.check_record_length(record)
        cls.check_field_count(record)
        record = ' ' + record  # makes counting positions easier
        dbobj = cls()
        for name, start, length in cls.suf_fields:
            try:
                setattr(dbobj, name, record[start:start + length])
            except ValueError:
                logger.warning("can't set attribute %s from string '%s'" % (
                        name, record[start:start + length]))
                return None
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
        ]

    objects = models.GeoManager()
    upload = models.ForeignKey('Upload')
    __CAA = models.CharField(
        db_column='caa',
        help_text="Knooppuntreferentie",
        max_length=30,
        verbose_name='CAA',
        )
    __CAB = models.PointField(
        db_column='cab',
        help_text="Knooppuntcoördinaat",
        srid=SRID,
        verbose_name='CAB',
        )

    def __init__(self, *args, **kwargs):
        """initialize object with optional properties
        """
        coords = kwargs.get('coords')
        if coords is not None:
            del kwargs['coords']
        super(Put, self).__init__(*args, **kwargs)
        if coords is not None:
            self.__CAB = Point(coords[0], coords[1])
            self.z = coords[2]

    @property
    def CAA(self):
        return self.__CAA

    @CAA.setter
    def CAA(self, value):
        self.__CAA = value.strip()

    @property
    def CAB(self):
        return self.__CAB

    @CAB.setter
    def CAB(self, value):
        x, y = value.split('/')
        self.__CAB = Point(float(x), float(y))

    @property
    def suf_id(self):
        "constant unique id"
        return self.CAA

    @property
    def point(self):
        return numpy.array((self.__CAB.x, self.__CAB.y, self.z))

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
        ('ABC', 400, 4),
        ('ACC', 405, 4),
        ('ACR', 623, 6),
        ('ACS', 630, 6),
        ]

    objects = models.GeoManager()
    upload = models.ForeignKey('Upload')
    __AAA = models.CharField(
        db_column='aaa',
        help_text="Strengreferentie",
        max_length=30,
        verbose_name='AAA',
        )
    __AAD = models.CharField(
        db_column='aad',
        help_text="Knooppuntreferentie 1",
        max_length=30,
        verbose_name='AAD',
        )
    __AAE = models.PointField(
        db_column='aae',
        help_text="Knooppuntcoördinaat knooppunt 1",
        srid=SRID,
        verbose_name='AAE',
        )
    __AAF = models.CharField(
        db_column='aaf',
        help_text="Knooppuntreferentie 2",
        max_length=30,
        verbose_name='AAF',
        )
    __AAG = models.PointField(
        db_column='aag',
        help_text="Knooppuntcoördinaat knooppunt 2",
        srid=SRID,
        verbose_name='AAG',
        )
    __ACR = models.FloatField(
        db_column='acr',
        help_text="BOB bij beginknoop absoluut",
        null=True,
        verbose_name='ACR',
        )
    __ACS = models.FloatField(
        db_column='acs',
        help_text="BOB bij eindknoop absoluut",
        null=True,
        verbose_name='ACS',
        )
    __the_geom = models.LineStringField(
        db_column='the_geom',
        help_text="LineString AAE -> AAG",
        srid=SRID,
        verbose_name='the_geom',
        )
    ACA = models.CharField(
        db_column='aca',
        help_text="vorm",
        max_length=2)
    ACB = models.CharField(
        db_column='acb',
        help_text="hoogte",
        max_length=4)
    ACC = models.CharField(
        db_column='acc',
        help_text="breedte",
        max_length=4)

    @property
    def AAA(self):
        return self.__AAA

    @AAA.setter
    def AAA(self, value):
        self.__AAA = value.strip()

    @property
    def AAD(self):
        return self.__AAD

    @AAD.setter
    def AAD(self, value):
        self.__AAD = value.strip()

    @property
    def AAE(self):
        return self.__AAE

    @AAE.setter
    def AAE(self, value):
        x, y = value.split('/')
        self.__AAE = Point(float(x), float(y))

    @property
    def AAF(self):
        return self.__AAF

    @AAF.setter
    def AAF(self, value):
        self.__AAF = value.strip()

    @property
    def AAG(self):
        return self.__AAG

    @AAG.setter
    def AAG(self, value):
        x, y = value.split('/')
        self.__AAG = Point(float(x), float(y))

    @property
    def ACR(self):
        return self.__ACR

    @ACR.setter
    def ACR(self, value):
        try:
            self.__ACR = float(value)
        except ValueError:
            self.__ACR = None

    @property
    def ACS(self):
        return self.__ACS

    @ACS.setter
    def ACS(self, value):
        try:
            self.__ACS = float(value)
        except ValueError:
            self.__ACS = None

    @property
    def the_geom(self):
        return self.__the_geom

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
        return numpy.array((self.__AAE.x, self.__AAE.y, (self.__ACR or 0)))

    @property
    def suf_fk_point2(self):
        "end point, a 3D object"
        return numpy.array((self.__AAG.x, self.__AAG.y, (self.__ACS or 0)))

    @property
    def form(self):
        return {'A': 'circular',
                'B': 'rectangular',
                }.get(self.ACA.strip(), 'unknown')

    @property
    def height(self):
        return int(self.ACB)

    @property
    def width(self):
        try:
            return int(self.ACC)
        except:
            return self.height

    @property
    def length(self):
        line_vector = (self.suf_fk_point2 - self.suf_fk_point1)[: 2]
        return math.sqrt(sum(line_vector * line_vector))

    @property
    def diam(self):
        if self.form == 'circular':
            if self.height != self.width:
                logger.warn("circular object with different height, width")
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
    def distance(self):
        return 0

    def save(self, *args, **kwargs):
        self.__the_geom = LineString(self.__AAE, self.__AAG)
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
    __ZYA = models.FloatField(
        db_column='zya',
        help_text="Afstand")
    ZYB = models.CharField(
        db_column='zyb',
        help_text="Referentie",
        max_length=1)
    ZYE = models.CharField(
        db_column='zye',
        help_text="ID",  # id of the referenced object
        max_length=30)
    ZYR = models.CharField(
        db_column='zyr',
        help_text="Type meting",
        max_length=1)
    ZYS = models.CharField(
        db_column='zys',
        help_text="Eenheid meetwaarde",
        max_length=1)
    __ZYT = models.FloatField(
        db_column='zyt',
        help_text="Meetwaarde")
    __ZYU = models.IntegerField(
        db_column='zyu',
        default=0,
        help_text="Macht van de vermenigvuldigingsfactor 10")

    def __unicode__(self):
        return self.suf_id

    @property
    def suf_id(self):
        "constant unique id"
        return '%s:%08.2f' % (self.suf_fk_edge, self.distance)

    @property
    def suf_fk_edge(self):
        return self.ZYE.strip()

    @property
    def distance(self):
        return self.__ZYA

    @property
    def reference(self):
        return int(self.ZYB.strip())

    @property
    def value(self):
        return self.__ZYT * 10 ** self.__ZYU

    @property
    def z(self):
        return self.point[2]

    @property
    def measurement_type(self):
        "combined codes for type and unit"
        return self.ZYR + self.ZYS

    @property
    def ZYA(self):
        return self.__ZYA

    @ZYA.setter
    def ZYA(self, value):
        self.__ZYA = float(value)

    @property
    def ZYT(self):
        return self.__ZYT

    @ZYT.setter
    def ZYT(self, value):
        self.__ZYT = float(value)

    @property
    def ZYU(self):
        return self.__ZYU

    @ZYU.setter
    def ZYU(self, value):
        try:
            self.__ZYU = int(value)
        except ValueError:
            self.__ZYU = 0

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
                self.measurement_type, self.distance, self.value))

        prev_distance = math.sqrt(sum(pow(prev - base, 2)))

        if self.measurement_type == 'AE':
            # Slope|Degrees
            self.point = prev + (
                self.distance - prev_distance) * numpy.array((
                direction[0], direction[1], math.sin(self.value / 180.0 * math.pi)))
        elif self.measurement_type == 'AF':
            # Slope|Percent
            self.point = prev + (
                self.distance - prev_distance) * numpy.array((
                direction[0], direction[1], self.value))
        elif self.measurement_type == 'BB':
            ## Absolute|metres (useful internally, not used by customer)
            self.point = numpy.array(tuple(
                    (base + self.distance * direction)[:2])
                                     + (self.value,))
        elif self.measurement_type == 'CB':
            # Relative|metres
            ## offset is relative to an ideal straight start-end
            ## connection
            self.point = (base
                          + self.distance * direction
                          + numpy.array((0, 0, self.value)))
        else:
            logger.warning("unrecognized, not supported")
            pass

        logger.debug("updated to %s" % self.point)


class Rioolwaarneming(RioolBestandObject):
    "*WAAR record"
    suf_record_length = 399
    suf_fields_count = 23
    suf_record_type = '*WAAR'
    suf_id = None

    def __unicode__(self):
        return self.suf_id
