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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with lizard-riool.  If not, see <http://www.gnu.org/licenses/>.
#

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

    assume the pool dictionary has been populated from a RMB file,
    that is: assume the pool values are lists, as many as there were
    *RIOO objects, and that each list starts with the *RIOO object and
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

    heappush(todo, (graph.node[sink]['obj'].z, sink))

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
            lambda p, c: graph.node[c]['obj'].z < water_level)

        logger.debug("nodes under water: %s" % under_water)
        logger.debug("links where water ends: %s" % shore_nodes)

        done = done.union(under_water)
        for i in under_water:
            graph.node[i]['obj'].flooded = water_level - graph.node[i]['obj'].z

        for shore_from, shore_node in shore_nodes:
            logger.debug("done=%s" % done)
            going_up, peak_nodes = dfs_preorder_nodes(
                graph, shore_node, done,
                lambda p, c: graph.node[c]['obj'].z >= graph.node[p]['obj'].z)

            logger.debug("nodes visited going up: %s" % going_up)
            logger.debug("links where level decreases: %s" % peak_nodes)

            done = done.union(going_up)
            for i in going_up:
                graph.node[i]['obj'].flooded = 0

            for i_from, i_to in peak_nodes:
                graph.node[i_from]['obj'].flooded = 0
                heappush(todo, (graph.node[i_from]['obj'].z, i_to))


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
    source and skipping the already visited nodes and do so only while
    condition holds.  if condition is given, also return the list of
    edges along which the condition did not hold and where the visit
    was interrupted.
    """
    # Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    # by D. Eppstein, July 2004.
    ##
    # networkx.algorithms.traversal.depth_first_search.dfs_labeled_edges,
    # adapted, adding the visited and condition parameters.

    visited = set(visited)
    satisfied = []
    border = []
    stack = [(source, iter([source]))]
    while stack:
        parent, children = stack.pop()
        for child in children:
            if child in visited:
                continue
            if condition(parent, child):
                visited.add(child)
                satisfied.append(child)
                stack.append((child, iter(sorted(G[child]))))
            else:
                border.append((parent, child))
    return satisfied, [(p, c) for p, c in border 
                       if c not in set(satisfied)]


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
