"""Contains the actual lost capacity algorithm.

First, a graph is built.

Then we compute lost capacity in the graph.

Then the numbers from the graph are stored in the relevant database models.
"""

from collections import defaultdict
from heapq import heappush, heappop
from itertools import chain

import networkx as nx


def compute_lost_capacity(saved_puts, saved_sewers, measurements_dict):
    G, sink_node = create_graph(
        saved_puts, saved_sewers, measurements_dict)
    compute_water_level(G, sink_node)
    add_lost_capacity(measurements_dict, saved_sewers, G)


def get_manhole_bobs(saved_sewers):
    """Return a dictionary put_id: lowest_bob_in_it"""
    manhole_bobs = defaultdict(list)

    for sewer in saved_sewers.values():
        manhole_bobs[sewer.manhole1.code].append(sewer.bob1)
        manhole_bobs[sewer.manhole2.code].append(sewer.bob2)

    return dict(
        (code, min(bobs))
        for code, bobs in manhole_bobs.iteritems())


def create_graph(saved_puts, saved_sewers, measurements_dict):
    """Create the networkx graph.

    Variables come from save_uploaded_data and contain:
    - saved_puts is a dictionary put_id: saved Manhole model instance
    - saved_sewers is a dictionary sewer_id: saved Sewer model instance
    - measurements_dict is a dictionary of sewer_id: *unsaved*
      SewerMeasurement model instances

    Puts are modelled as several points in the graph: the Put itself
    has a low level (the minimum of all the BOBs connected to it) and
    for each sewer, a record is added with its level equal to the BOB
    of the sewer connecting to it.
    """

    G = nx.Graph()

    manhole_bobs = get_manhole_bobs(saved_sewers)

    for sewer_id, saved_sewer in saved_sewers.items():
        if sewer_id not in measurements_dict:
            continue  # Shouldn't happen once we add virtual sewers

        manhole1 = saved_sewer.manhole1.code
        manhole2 = saved_sewer.manhole2.code

        previous = None
        # Loop over all points related to this sewer, from put to put
        # For each point, we add a node to the graph. The node is a tuple:
        #  ("put", put_id)  for puts
        #  ("sewer_end", sewer_id, "1" or "2") for sewer ends
        #  ("measurement", sewer_id, distance) for measurements
        #
        # For each node in the graph, we store the bob as the 'bob' attribute,
        # and the 'waterlevel' attribute which starts out as "None".
        for (location, bob) in chain(
            [(("put", manhole1), manhole_bobs[manhole1]),
             (("sewer_end", sewer_id, "1"), saved_sewer.bob1)],
            ((("measurement", sewer_id, sewer_measurement.dist),
              sewer_measurement.bob)
             for sewer_measurement in sorted(
                    measurements_dict[sewer_id],
                    key=lambda m: m.dist)),
            [(("sewer_end", sewer_id, "2"), saved_sewer.bob2),
             (("put", manhole2), manhole_bobs[manhole2])]
                ):
            G.add_node(location, bob=bob, waterlevel=None)
            if previous is not None:
                G.add_edge(previous, location)
            previous = location

    # Find the put ids that are sinks
    sink_ids = [manhole_id for manhole_id, manhole in saved_puts.iteritems()
                if manhole.is_sink]
    if len(sink_ids) == 0:
        # ! Should never happen
        return None, None
    elif len(sink_ids) == 1:
        sink_id = sink_ids[0]
    else:
        # There are multiple sinks. Our algorithm just uses one. We
        # use a trick: we find the lowest sink, then connect the other
        # ones to it in the graph, and return the id of the
        # lowest. This acts as if there's a secret extra pipe between
        # the different sinks.
        sink_id = min(
            sink_ids,
            key=lambda sink: G.node[("put", sink)]['bob'])

        for higher_sink_id in sink_ids:
            if higher_sink_id == sink_id:
                continue  # Itself
            G.add_edge(("put", sink_id), ("put", higher_sink_id))

    return G, ("put", sink_id)


def compute_water_level(G, sink_node):
    """Compute the lost capacity in graph G. sink must be a put-id of some
    put in the graph.

    From the sink, go up until we reach "peaks", places where the
    water level goes down. From there, fill the network with water to a level
    equal to the peak, then continue up and add to the todo list the following
    level turning points.

    Straight translation of the code by Mario Frasca to new data structures,
    see the history on Git of parsers.py."""

    todo = []  # A priority queue, guarantees that the lowest level stays first
    done = set()  # Keeping track of explored nodes

    heappush(todo, (G.node[sink_node]['bob'], sink_node))

    while todo:
        ## pour water in the nodes at level lower than `water_level`
        ## and that are reachable from `item`.  when we reach a node
        ## at a level that is above the `water_level`, stop pouring
        ## water in the graph in that direction and mark the node as
        ## emerging.  when done pouring water, do a search for turning
        ## points starting at all emerging points and put the new
        ## turning points in the todo heap.
        (water_level, current_node) = heappop(todo)

        def under_water_condition(parent, child):
            return G.node[child]['bob'] < water_level

        under_water_list, shore_node_pairs = (
            neighbouring_nodes_satisfying_condition(
                G, current_node, done, under_water_condition))

        done = done.union(under_water_list)

        for node in under_water_list:
            G.node[node]['waterlevel'] = water_level

        for shore_from, shore_to in shore_node_pairs:
            # (shore_from, shore_to) is an edge along which the bob
            # rose to be at least equal to water_level
            # From here we are "above water", and as long as we're not
            # going down, we stay that way
            def not_going_down_condition(parent, child):
                return G.node[parent]['bob'] <= G.node[child]['bob']

            going_up_list, peak_node_pairs = (
                neighbouring_nodes_satisfying_condition(
                    G, shore_to, done, not_going_down_condition))

            done = done.union(going_up_list)

            for node in going_up_list:
                G.node[node]['waterlevel'] = G.node[node]['bob']

            for peak_from, peak_to in peak_node_pairs:
                G.node[peak_from]['waterlevel'] = G.node[peak_from]['bob']
                heappush(todo, (G.node[peak_from]['bob'], peak_to))

    # There may be nodes we haven't seen yet. Maybe we should mark
    # them as being 100% underwater.


def neighbouring_nodes_satisfying_condition(G, start, visited, condition):
    """Produce nodes in a depth-first-search pre-ordering starting at
    source and skipping the already visited nodes and do so only while
    condition holds.  if condition is given, also return the list of
    edges along which the condition did not hold and where the visit
    was interrupted.

    Although condition gets two nodes as parameters ("parent" and "child"),
    the list satisfied is a list of the "child" parameters. The list
    borders is a list of (parent, child) pairs, and only holds a pair if
    none if the calls of (some_parent, child) succeeded.
    """
    # Based on http://www.ics.uci.edu/~eppstein/PADS/DFS.py
    # by D. Eppstein, July 2004.
    ##
    # networkx.algorithms.traversal.depth_first_search.dfs_labeled_edges,
    # adapted, adding the visited and condition parameters.

    visited = set(visited)  # Make a copy because we mutate it
    satisfied = []
    border = []
    stack = [(start, iter([start]))]

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


def add_lost_capacity(measurements_dict, sewerdict, G):
    for sewer_id, measurements in measurements_dict.iteritems():
        sewer = sewerdict[sewer_id]
        for measurement in measurements:
            # measurement is an unsaved instance of
            # mmodels.SewerMeasurement
            node = ("measurement", sewer_id, measurement.dist)
            measurement.set_water_level(G.node[node]['waterlevel'])
            measurement.compute_flooded_pct(use_sewer=sewer)
