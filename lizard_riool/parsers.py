# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from models import Put, Riool, Rioolmeting
import logging
import math
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
        reference = pool[suf_id][1].reference  # choice
        start_point = riool.point(reference, opposite=False)
        end_point = riool.point(reference, opposite=True)
        logger.debug("id of line / start-end: %s / %s-%s" % (suf_id, start_point, end_point))

        graph.add_node(tuple(start_point),
                       obj=Put(suf_id=riool.suf_fk_node(reference,
                                                        opposite=False),
                               coords=start_point))
        graph.add_node(tuple(end_point),
                       obj=Put(suf_id=riool.suf_fk_node(reference,
                                                        opposite=True),
                               coords=end_point))

        prev_point = start_point
        direction = (end_point - start_point)
        logger.debug("vector of this segment is %s" % direction)
        direction = direction / math.sqrt(sum(pow(direction[:2], 2)))
        logger.debug("'2D-unit' vector of this segment is %s" % direction)

        for obj in pool[suf_id][1:]:
            obj.update_coordinates(start_point, direction, prev_point)
            graph.add_node(tuple(obj.point),
                           obj=obj)
            logger.debug("adding edge %s-%s" % (prev_point, obj.point))
            graph.add_edge(tuple(prev_point), tuple(obj.point),
                           obj=obj, segment=riool)
            prev_point = obj.point

        logger.debug("connecting to opposite manhole")
        logger.debug("adding edge %s-%s" % (obj.point, end_point))
        graph.add_edge(tuple(obj.point), tuple(end_point),
                       obj=None, segment=riool)


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

        logger.debug("%s is a start point" % (item, ))

        ## pour water in the nodes at level lower than `water_level`
        ## and that are reachable from `item`.  when we reach a node
        ## at a level that is above the `water_level`, stop pouring
        ## water in the graph in that direction and mark the node as
        ## emerging.  when done pouring water, do a search for turning
        ## points starting at all emerging points and put the new
        ## turning points in the todo heap.

        ## first we pour water in the network
        under_water, shore_nodes = dfs_preorder_nodes(
            graph, item, done,
            lambda p, c: graph.node[c]['obj'].point[2] < water_level)

        logger.debug("nodes under water: %s" % under_water)
        logger.debug("nodes reached by water: %s" % shore_nodes)

        done.add(item)
        done = done.union(under_water)
        for i in under_water:
            graph.node[i]['obj'].flooded = water_level

        for shore_node in shore_nodes:
            going_up, peak_nodes = dfs_preorder_nodes(
                graph, shore_node, done,
                lambda p, c: (graph.node[c]['obj'].point[2] >= 
                              graph.node[p]['obj'].point[2]))

            logger.debug("nodes visited going up: %s" % going_up)
            logger.debug("nodes that form a peak: %s" % peak_nodes)

            done = done.union(going_up)
            for i in going_up:
                graph.node[i]['obj'].flooded = 0

            for i in peak_nodes:
                graph.node[i]['obj'].flooded = 0
                heappush(todo, (i[2], i))


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


def dfs_preorder_nodes(G, source, visited, condition):
    """Produce nodes in a depth-first-search pre-ordering starting at
    source and skipping the already visited nodes and while condition
    holds.
    """
    # Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    # by D. Eppstein, July 2004.
    ##
    # networkx.algorithms.traversal.depth_first_search.dfs_labeled_edges,
    # adapted, adding the visited and condition parameters.

    nodes = [source]
    visited = set(visited)
    visited.discard(source)
    satisfied = []
    border = []
    for start in nodes:
        if start in visited:
            continue
        stack = [(start, iter(G[start]))]
        while stack:
            parent, children = stack[-1]
            try:
                child = next(children)
                if child not in visited:
                    visited.add(child)
                    if condition(parent, child):
                        satisfied.append(child)
                        stack.append((child, iter(G[child])))
                    else:
                        border.append(child)
            except StopIteration:
                stack.pop()
    return satisfied, border


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
