import logging

logger = logging.getLogger(__name__)


class WAAR(object):
    "Utility class to construct SUFRIB/SUFRMB *WAAR records."

    __ZZA = " " * 6
    __ZZB = " " * 1
    __ZZC = " " * 1
    __ZZD = " " * 2
    __ZZE = " " * 30
    __ZZF = " " * 3
    __ZZG = " " * 5
    __ZZH = " " * 2
    __ZZI = " " * 15
    __ZZJ = " " * 15
    __ZZK = " " * 2
    __ZZL = " " * 2
    __ZZM = " " * 1
    __ZZN = " " * 11
    __ZZO = " " * 20
    __ZZP = " " * 120
    __ZZQ = " " * 15
    __ZZR = " " * 1
    __ZZS = " " * 30
    __ZZT = " " * 30
    __ZZU = " " * 30
    __ZZV = " " * 30

    @property
    def ZZA(self):
        return self.__ZZA

    @ZZA.setter
    def ZZA(self, value):
        self.__ZZA = "%-6.2f" % value
        self.__check_length("ZZA")

    @property
    def ZZB(self):
        return self.__ZZB

    @ZZB.setter
    def ZZB(self, value):
        self.__ZZB = str(value)
        self.__check_length("ZZB")

    @property
    def ZZE(self):
        return self.__ZZE

    @ZZE.setter
    def ZZE(self, value):
        self.__ZZE = value.ljust(len(WAAR.__ZZE))
        self.__check_length("ZZE")

    @property
    def ZZF(self):
        return self.__ZZF

    @ZZF.setter
    def ZZF(self, value):
        self.__ZZF = value.ljust(len(WAAR.__ZZF))
        self.__check_length("ZZF")

    @property
    def ZZI(self):
        return self.__ZZI

    @ZZI.setter
    def ZZI(self, value):
        self.__ZZI = "%-15.0f" % (value * 100)
        self.__check_length("ZZI")

    @property
    def ZZJ(self):
        return self.__ZZJ

    @ZZJ.setter
    def ZZJ(self, value):
        self.__ZZJ = "%-15.0f" % (value * 100)
        self.__check_length("ZZJ")

    @property
    def ZZV(self):
        return self.__ZZV

    @ZZV.setter
    def ZZV(self, value):
        self.__ZZV = value.ljust(len(WAAR.__ZZV))
        self.__check_length("ZZV")

    def __check_length(self, attr):
        "Check length of instance attribute."
        obj_length = len(getattr(self, "_WAAR__" + attr))
        cls_length = len(getattr(WAAR, "_WAAR__" + attr))
        if obj_length != cls_length:
            msg = "*WAAR.%s has wrong length: %d instead of %d."
            logger.error(msg % (attr, obj_length, cls_length))

    def __str__(self):
        return (
            "*WAAR"
            + "|" + self.__ZZA
            + "|" + self.__ZZB
            + "|" + self.__ZZC
            + "|" + self.__ZZD
            + "|" + self.__ZZE
            + "|" + self.__ZZF
            + "|" + self.__ZZG
            + "|" + self.__ZZH
            + "|" + self.__ZZI
            + "|" + self.__ZZJ
            + "|" + self.__ZZK
            + "|" + self.__ZZL
            + "|" + self.__ZZM
            + "|" + self.__ZZN
            + "|" + self.__ZZO
            + "|" + self.__ZZP
            + "|" + self.__ZZQ
            + "|" + self.__ZZR
            + "|" + self.__ZZS
            + "|" + self.__ZZT
            + "|" + self.__ZZU
            + "|" + self.__ZZV
        )
