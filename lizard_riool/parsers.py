# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from models import Put, Riool, Rioolmeting
import logging
import networkx as nx
from heapq import heappush, heappop


logger = logging.getLogger(__name__)


def convert_to_graph(pool, graph):
    """inspect the pool of objects and produce a nx.Graph

    assume the pool has been populated from a RMB file, that is:
    assume the pool only contains as many lists as there were *RIOO
    objects and that each list starts with the *RIOO object and
    continues with the measurements along that object in the same
    order as in the file.
    """

    for suf_id in pool:
        riool = pool[suf_id][0]
        reference = inspection[0].reference
        start_point = riool.point(reference, opposite=False)
        end_point = riool.point(reference, opposite=True)

        inspection = [start_point, Put(suf_id + '_start', start_point)]

        previos_coordinates = start_point
        for obj in pool[suf_id][1:]:
            obj.update_coordinates(previos_coordinates)
            previos_coordinates = obj.point
            inspection.append(obj.point, obj)

        inspection = [end_point, Put(suf_id + '_end', end_point)]
        

def examine_graph(graph, sink):
    """calculate lost water depth for each node

    starting from the given `sink` explore the graph in all possible
    directions and identify the points where the level starts going
    down, use these points to populate a todo list (or priority heap).
    from the lowest turning point virtually fill the network with
    water as long as the nodes are connected and at a level lower than
    the turning point, then continue up to identify and add to the
    todo list the following level turning points.
    """

    todo = []  # a priority queue
    done = set()  # keeping track of explored nodes

    x, y, z = graph.node[sink]['obj'].point
    heappush(todo, (z, sink))

    while todo:
        (water_level, item) = heappop(todo)
        done.add(item)

        ## pour water in the nodes at level lower than `water_level`
        ## and that are reachable from `item`.  when we reach a node
        ## at a level that is above the `water_level`, stop pouring
        ## water in the graph in that direction and mark the node as
        ## emerging.  when done pouring water, do a search for turning
        ## points starting at all emerging points and put the new
        ## turning points in the todo heap.

        ## first we pour water in the network
        reachable = graph.adj[item]
        emerging = []
        while reachable:
            candidate = reachable.pop()
            if candidate in done:
                ## do not walk back
                continue

            ## mark as examined and initialize its flooded state.
            done.add(candidate)
            obj = graph.node[candidate]['obj']
            obj.flooded = 0

            if obj.point[2] < water_level:
                ## mark candidate as under water
                obj.flooded = water_level
                reachable.extend(graph.adj[candidate])
            else:
                emerging.append(reachable)
            pass

        ## now from the emerging nodes, walk up to the turning points.
        for candidate in emerging:
            if candidate in done:
                continue

            done.add(candidate)
            obj = graph.node[candidate]['obj']

        heappush(todo, ())
        pass


def parse(file_name, pool=None):
    """parse the RxB file

    inspect the file one record at a time.  categorize objects into
    the optional pool dictionary for later further examination.
    """

    def action_for_riool(pool, obj):
        "add the object to the pool as a container for its measurements"

        pool[obj.suf_id] = [obj]

    def action_for_rioolmeting(pool, obj):
        "add the object to the owning RIOO object"

        if obj.suf_fk_edge not in pool:
            logger.warn('rioolmeting %s refers to missing riool %s' % (
                    obj.suf_id, obj.suf_fk_edge))
        else:
            pool[obj.suf_fk_edge].append(obj)

    def action_for_put(pool, obj):
        "add the object to the owning PUT object"

        pass

    classes = {
        '*ALGE': None,  # no action
        '*PUT': Put,
        '*RIOO': Riool,
        '*WAAR': None,  # no action
        '*MPUT': None,  # no action
        '*MRIO': Rioolmeting,
        }

    action = {
        '*ALGE': None,  # no action
        '*PUT': action_for_put,
        '*RIOO': action_for_riool,
        '*WAAR': None,  # no action
        '*MPUT': None,  # no action
        '*MRIO': action_for_rioolmeting,
        }

    with open(file_name) as f:
        ## using `with` makes sure the file is closed.
        for line_no, line in enumerate(f):
            line = line.strip("\r\n")
            record_type = line.split('|')[0]
            if classes.get(record_type) is None:
                continue
            obj = (classes[record_type].
                   parse_line_from_rioolbestand(line, line_no + 1))
            if obj is not None:
                if hasattr(pool, 'append'):
                    pool.append(obj)
                elif action.get(record_type) is not None and pool is not None:
                    action[record_type](pool, obj)


def main(options, args):
    """
    """

    for file_name in args:
        parse(file_name)


if __name__ == '__main__':
    from optparse import OptionParser
    usage = "usage: %prog [options] input_files..."
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    main(options, args)
