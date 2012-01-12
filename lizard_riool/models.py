# encoding: utf-8

# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from django.contrib.gis.db import models
from django.contrib.gis.geos import LineString, Point

RDNEW = 28992
SRID = RDNEW


class Put(models.Model):
    "*PUT record"
    CAA = models.CharField(
        help_text="Knooppuntreferentie",
        max_length=30)
    __CAB = models.PointField(
        db_column='CAB',
        help_text="Knooppuntcoördinaat",
        srid=SRID)

    @property
    def CAB(self):
        return self.__CAB

    @CAB.setter
    def CAB(self, value):
        x, y = value.split('/')
        self.__CAB = Point(float(x), float(y))

    def __unicode__(self):
        return self.CAA


class Riool(models.Model):
    "*RIOO record"
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


class Rioolmeting(models.Model):
    "*MRIO record"
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
