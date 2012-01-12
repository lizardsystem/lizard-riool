# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from models import Put, Riool, Rioolmeting
import getopt
import logging
import sys

logger = logging.getLogger(__name__)
logger.setLevel('INFO')

handlers = {
    '*MRIO': 'RioolmetingHandler',
    '*PUT' : 'PutHandler',
    '*RIOO': 'RioolHandler',
}


class PutHandler(object):

    @staticmethod
    def handle(record):
        logger.debug("Parsing a *PUT record")
        record = ' ' + record
        put = Put()
        put.CAA = record[6:6 + 30].strip()
        put.CAB = record[37:37 + 19]
        put.save()
        return put


class RioolHandler(object):

    @staticmethod
    def handle(record):
        logger.debug("Parsing a *RIOO record")
        record = ' ' + record
        riool = Riool()
        riool.AAA = record[7:7 + 30]
        riool.AAD = record[89:89 + 30]
        riool.AAE = record[120:120 + 19]
        riool.AAF = record[140:140 + 30]
        riool.AAG = record[171:171 + 19]
        riool.ACR = record[623:623 + 6]
        riool.ACS = record[630:630 + 6]
        riool.save()
        return riool


class RioolmetingHandler(object):

    @staticmethod
    def handle(record):
        logger.debug("Parsing a *MRIO record")
        record = ' ' + record
        meting = Rioolmeting()
        meting.ZYA = record[7:7 + 8]
        meting.ZYB = record[16:16 + 1]
        meting.ZYE = record[18:18 + 30].strip()
        meting.ZYR = record[98:98 + 1]
        meting.ZYS = record[100:100 + 1]
        meting.ZYT = record[102:102 + 10]
        meting.ZYU = record[113:113 + 3]
        meting.save()
        return meting


def process(file):
    ""
    with open(file) as f:
        for line in f:
            for record, handler in handlers.iteritems():
                if line.startswith(record):
                    globals()[handler].handle(line)


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
        process(arg)

if __name__ == '__main__':
    main()
