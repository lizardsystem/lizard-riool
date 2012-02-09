# encoding: utf-8

# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point
from os.path import basename, splitext
import logging

RDNEW = 28992
SRID = RDNEW

logger = logging.getLogger(__name__)


class Upload(models.Model):
    "An uploaded file"
    the_file = models.FileField(upload_to='upload')
    the_time = models.DateTimeField(auto_now=True)

    @property
    def filename(self):
        return basename(self.the_file.name)

    @property
    def suffix(self):
        return splitext(self.the_file.name)[1]

    def __unicode__(self):
        return self.filename


class RioolBestandObject(models.Model):
    "Common behaviour to all sewage objects"

    @classmethod
    def check_record_length(cls, record):
        if len(record.strip("\n\r")) != cls.suf_record_length:
            raise Exception("Unexpected record length")

    @classmethod
    def check_fields_count(cls, record):
        field_count = record.count("|") + 1
        if field_count != cls.suf_fields_count:
            raise Exception("record defines %s fields, %s expects %s" %
                (field_count, cls.suf_record_type, cls.suf_fields_count))

    @classmethod
    def parse_line_from_rioolbestand(cls, record):
        logger.debug("Parsing a " + cls.suf_record_type + " record")
        cls.check_record_length(record)
        cls.check_field_count(record)
        record = ' ' + record  # makes counting positions easier
        dbobj = cls()
        for name, start, length in cls.suf_fields:
            setattr(dbobj, name, record[start:start + length])
        return dbobj


class Put(RioolBestandObject):
    "*PUT record"

    suf_record_length = 498
    suf_fields_count = 40
    suf_record_type = '*PUT'
    suf_fields = [
        ('CAA', 6, 30),
        ('CAB', 37, 19),
        ]

    CAA = models.CharField(
        help_text="Knooppuntreferentie",
        max_length=30)
    __CAB = models.PointField(
        db_column='CAB',
        help_text="Knooppuntcoördinaat",
        srid=SRID)

    @property
    def suf_id(self):
        return self.CAA

    @property
    def point(self):
        return self.__CAB

    @property
    def CAB(self):
        return self.__CAB

    @CAB.setter
    def CAB(self, value):
        x, y = value.split('/')
        self.__CAB = Point(float(x), float(y))

    def __unicode__(self):
        return self.CAA


class Riool(RioolBestandObject):
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
        ('ACR', 623, 6),
        ('ACS', 630, 6),
        ]
    AAA = models.CharField(
        help_text="Strengreferentie",
        max_length=30)
    AAD = models.CharField(
        help_text="Knooppuntreferentie 1",
        max_length=30)
    __AAE = models.PointField(
        db_column='AAE',
        help_text="Knooppuntcoördinaat knooppunt 1",
        srid=SRID)
    AAF = models.CharField(
        help_text="Knooppuntreferentie 2",
        max_length=30)
    __AAG = models.PointField(
        db_column='AAG',
        help_text="Knooppuntcoördinaat knooppunt 2",
        srid=SRID)
    __ACR = models.FloatField(
        db_column='ACR',
        help_text="BOB bij beginknoop absoluut",
        null=True)
    __ACS = models.FloatField(
        db_column='ACS',
        help_text="BOB bij eindknoop absoluut",
        null=True)
    __the_geom = models.LineStringField(
        db_column='the_geom',
        help_text="LineString AAE -> AAG",
        srid=SRID)

    @property
    def suf_id(self):
        return self.AAA

    @property
    def suf_fk_node1(self):
        return self.AAD

    @property
    def suf_fk_node2(self):
        return self.AAF

    @property
    def suf_fk_point1(self):
        return self.__AAE

    @property
    def suf_fk_point2(self):
        return self.__AAG

    @property
    def AAE(self):
        return self.__AAE

    @AAE.setter
    def AAE(self, value):
        x, y = value.split('/')
        self.__AAE = Point(float(x), float(y))

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

    def save(self, *args, **kwargs):
        self.__the_geom = LineString(self.__AAE, self.__AAG)
        super(Riool, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.AAA


class Rioolmeting(RioolBestandObject):
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
    __ZYA = models.FloatField(
        db_column='ZYA',
        help_text="Afstand")
    ZYB = models.CharField(
        help_text="Referentie",
        max_length=1)
    ZYE = models.CharField(
        help_text="ID",
        max_length=30)
    ZYR = models.CharField(
        help_text="Type meting",
        max_length=1)
    ZYS = models.CharField(
        help_text="Eenheid meetwaarde",
        max_length=1)
    __ZYT = models.FloatField(
        db_column='ZYT',
        help_text="Meetwaarde")
    __ZYU = models.IntegerField(
        db_column='ZYU',
        default=0,
        help_text="Macht van de vermenigvuldigingsfactor 10")

    @property
    def ZYA(self):
        return self.__ZYA

    @ZYA.setter
    def ZYA(self, value):
        self.__ZYA = float(value)

    @property
    def ZYT(self):
        return self.__ZYT * 10 ** self.__ZYU

    @ZYT.setter
    def ZYT(self, value):
        self.__ZYT = float(value)

    @property
    def ZYU(self):
        return self.__ZYU

    @ZYU.setter
    def ZYU(self, value):
        self.__ZYU = int(value)


class Rioolwaarneming(RioolBestandObject):
    "*WAAR record"
    suf_record_length = 399
    suf_fields_count = 23
    suf_record_type = '*WAAR'
