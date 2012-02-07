# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from models import Put, Riool, Rioolmeting
import getopt
import logging
import sys

logger = logging.getLogger(__name__)

handlers = {
    '*MRIO': 'RioolmetingHandler',
#    '*PUT' : 'PutHandler',
    '*RIOO': 'RioolHandler',
}


class Handler(object):

    @classmethod
    def check_record_length(cls, record):
        if len(record.splitlines()[0]) != cls.RECORD_LENGTH:
            raise Exception("Unexpected record length")


class PutHandler(Handler):

    RECORD_LENGTH = 498

    @classmethod
    def handle(cls, i, record):
        logger.debug("Parsing a *PUT record")
        cls.check_record_length(record)
        record = ' ' + record
        put = Put()
        put.CAA = record[6:6 + 30].strip()
        put.CAB = record[37:37 + 19]
        put.save()
        return put


class RioolHandler(Handler):

    RECORD_LENGTH = 635

    @classmethod
    def handle(cls, i, record):
        logger.debug("Parsing a *RIOO record")
        cls.check_record_length(record)
        record = ' ' + record
        riool = Riool()
        riool.AAA = record[7:7 + 30].strip()
        riool.AAD = record[89:89 + 30].strip()
        riool.AAE = record[120:120 + 19].strip()
        riool.AAF = record[140:140 + 30].strip()
        riool.AAG = record[171:171 + 19].strip()
        riool.ACR = record[623:623 + 6].strip()
        riool.ACS = record[630:630 + 6].strip()
        riool.save()
        return riool


class RioolmetingHandler(Handler):

    RECORD_LENGTH = 270

    @classmethod
    def handle(cls, i, record):
        logger.debug("Parsing a *MRIO record")
        cls.check_record_length(record)
        record = ' ' + record
        meting = Rioolmeting()
        meting.ZYA = record[7:7 + 8]
        meting.ZYB = record[16:16 + 1]
        meting.ZYE = record[18:18 + 30]
        meting.ZYR = record[98:98 + 1]
        meting.ZYS = record[100:100 + 1]
        meting.ZYT = record[102:102 + 10]
        meting.ZYU = record[113:113 + 3]
        meting.save()
        return meting


def parse(file):
    ""
    with open(file) as f:
        for i, line in enumerate(f):
            for record, handler in handlers.iteritems():
                if line.startswith(record):
                    globals()[handler].handle(i + 1, line)


def main():
    """

    http://www.artima.com/weblogs/viewpost.jsp?thread=4829
    """

    # parse command-line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)

    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)

    # process arguments
    for arg in args:
        parse(arg)

if __name__ == '__main__':
    main()
