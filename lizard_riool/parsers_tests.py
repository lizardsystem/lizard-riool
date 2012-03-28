#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# pylint: disable=C0111
#
# Copyright (C) 2012 Nelen & Schuurmans
#
# This package is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this package. If not, see <http://www.gnu.org/licenses/>.

import networkx as nx
from parsers import dfs_preorder_nodes


import unittest


class TestCase(unittest.TestCase):
    def setUp(self):
        import logging
        logging.getLogger().setLevel(logging.INFO)


class Dfs_Preorder_Nodes_TestSuite(TestCase):

    def test000(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 0)
        C = (0, 2, 0)
        D = (0, 3, 0)
        E = (0, 4, 0)
        G.add_edges_from([(A, B), (B, C), (C, D), (D, E)])
        current = dfs_preorder_nodes(G, A, set(), lambda a, b: True)
        target = ([A, B, C, D, E], [])
        self.assertEqual(target, current)

    def test010(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 0)
        C = (0, 2, 0)
        D = (0, 3, 0)
        E = (0, 4, 0)
        G.add_edges_from([(A, B), (B, C), (C, D), (D, E)])
        current = dfs_preorder_nodes(G, D, set([A, B, C]), lambda a, b: True)
        target = ([D, E], [])
        self.assertEqual(target, current)

    def test020(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 0)
        C = (0, 2, 0)
        D = (0, 3, 1)
        E = (0, 4, 1)
        G.add_edges_from([(A, B), (B, C), (C, D), (D, E)])
        current = dfs_preorder_nodes(G, A, set(),
                                     lambda a, b: b[2] <= 0)
        target = ([A, B, C, ], [(C, D)])
        self.assertEqual(target, current)

    def test030(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 1)
        C = (0, 2, 4)
        D = (0, 3, 5)
        E = (0, 4, 8)
        G.add_edges_from([(A, B), (B, C), (C, D), (D, E)])
        current = dfs_preorder_nodes(G, A, set(),
                                     lambda p, c: c[2] - p[2] <= 1)
        target = ([A, B, ], [(B, C)])
        self.assertEqual(target, current)

    def test032(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 1)
        C = (0, 2, 4)
        D = (0, 3, 5)
        E = (0, 4, 8)
        G.add_edges_from([(A, B), (B, C), (C, D), (D, E)])
        current = dfs_preorder_nodes(G, C, set([A, B]),
                                     lambda p, c: c[2] - p[2] <= 1)
        target = ([C, D, ], [(D, E)])
        self.assertEqual(target, current)

    def test100(self):
        """
        A--B
        |
        C--D
        |
        E
        """
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 1)
        C = (1, 0, 2)
        D = (1, 1, 3)
        E = (2, 0, 4)
        G.add_edges_from([(A, B), (A, C), (C, D), (C, E)])
        current = dfs_preorder_nodes(G, A, set(),
                                     lambda p, c: c[2] - p[2] <= 1)
        target = ([A, B, ], [(A, C)])
        self.assertEqual(target, current)
        current = dfs_preorder_nodes(G, C, set([A, B]),
                                     lambda p, c: c[2] - p[2] <= 1)
        target = ([C, D, ], [(C, E)])
        self.assertEqual(target, current)

    def test110(self):
        """
        A--B
        |  |
        D--C--E

        can't reach E.  D is first seen as unreachable from A, then is
        reached from C.
        """
        G = nx.Graph()
        A = ("A", 0)
        B = ("B", 1)
        C = ("C", 2)
        D = ("D", 3)
        E = ("E", 4)
        G.add_edges_from([(A, B), (A, D), (C, D), (B, C), (C, E)])
        current = dfs_preorder_nodes(G, A, set(),
                                     lambda p, c: c[1] - p[1] <= 1)
        target = ([A, B, C, D], [(C, E)])
        self.assertEqual(target, current)

    def test120(self):
        """
        A--B
        |  |
        D--C--E

        can't reach neither D nor E.
        D can't be reached from A and C
        """
        G = nx.Graph()
        A = ("A", 0)
        B = ("B", 1)
        C = ("C", 2)
        D = ("D", 8)
        E = ("E", 4)
        G.add_edges_from([(A, B), (A, D), (C, D), (B, C), (C, E)])
        current = dfs_preorder_nodes(G, A, set(),
                                     lambda p, c: c[1] - p[1] <= 1)
        target = ([A, B, C], [(A, D), (C, D), (C, E)])
        self.assertEqual(target, current)

    def test200(self):
        """A-AB1-AB2-AB3-AB4-B
        """
        G = nx.Graph()
        A = ("A", 10)
        AB1 = ("AB1", 10.01)
        AB2 = ("AB2", 09.90)
        AB3 = ("AB3", 10.00)
        AB4 = ("AB4", 10.05)
        B = ("B", 10.1)
        G.add_edges_from([(A, AB1), (AB1, AB2), (AB2, AB3), (AB3, AB4), (AB4, B)])
        current = dfs_preorder_nodes(G, A, set(),
                                     lambda p, c: c[1] >= p[1])
        target = ([A, AB1, ], [(AB1, AB2)])
        self.assertEqual(target, current)


from parsers import compute_lost_water_depth
from models import Put


class Compute_Lost_Water_Depth_TestSuite(TestCase):

    def test000(self):
        """
        A---B---C---D---E---F
        levels:
        5   6   5   4   6   8
        result:
        0   0   1   2   0   0
        """
        G = nx.Graph()
        nodes = [("A", Put(coords=(0, 0, 5))),
                 ("B", Put(coords=(0, 1, 6))),
                 ("C", Put(coords=(0, 2, 5))),
                 ("D", Put(coords=(0, 3, 4))),
                 ("E", Put(coords=(0, 4, 6))),
                 ("F", Put(coords=(0, 5, 8)))]
        for label, obj in nodes:
            G.add_node(label, obj=obj)
        for (p, x), (c, y) in zip(nodes, nodes[1:]):
            G.add_edge(p, c)

        compute_lost_water_depth(G, "A")

        self.assertEqual(0, G.node["A"]['obj'].flooded)
        self.assertEqual(0, G.node["B"]['obj'].flooded)
        self.assertEqual(1, G.node["C"]['obj'].flooded)
        self.assertEqual(2, G.node["D"]['obj'].flooded)
        self.assertEqual(0, G.node["E"]['obj'].flooded)
        self.assertEqual(0, G.node["F"]['obj'].flooded)

    def test010(self):
        """
        A---B---C---D---E---F
        levels:
        7   6   5   4   6   8
        result:
        0   1   2   3   1   0
        """
        G = nx.Graph()
        nodes = {"A": Put(coords=(0, 0, 7)),
                 "B": Put(coords=(0, 1, 6)),
                 "C": Put(coords=(0, 2, 5)),
                 "D": Put(coords=(0, 3, 4)),
                 "E": Put(coords=(0, 4, 6)),
                 "F": Put(coords=(0, 5, 8)),
                 }
        for label, obj in nodes.items():
            G.add_node(label, obj=obj)
        labels = sorted(nodes)
        for p, c in zip(labels, labels[1:]):
            G.add_edge(p, c)

        compute_lost_water_depth(G, "A")

        self.assertEqual(0, G.node["A"]['obj'].flooded)
        self.assertEqual(1, G.node["B"]['obj'].flooded)
        self.assertEqual(2, G.node["C"]['obj'].flooded)
        self.assertEqual(3, G.node["D"]['obj'].flooded)
        self.assertEqual(1, G.node["E"]['obj'].flooded)
        self.assertEqual(0, G.node["F"]['obj'].flooded)


from parsers import parse
from models import Riool, Rioolmeting


class Parse_TestSuite(TestCase):

    def test000(self):
        "file is read into dictionary and keys are correct"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        target = ['6400001', '6400002', '6400003', '6400004', '6400005', '6400006']
        current = sorted(pool.keys())
        self.assertEqual(target, current)

    def test010(self):
        "file is read into dictionary and values have correct length"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        target = [5, 5, 3, 3, 3, 5]
        current = [len(pool[k]) for k in sorted(pool.keys())]
        self.assertEqual(target, current)

    def test020(self):
        "file is read into dictionary and first values are Riool objects"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        target = [Riool] * len(pool)
        current = [pool[k][0].__class__ for k in sorted(pool.keys())]
        self.assertEqual(target, current)

    def test030(self):
        "file is read into dictionary and all subsequent values are Rioolmeting objects"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        target = [[Rioolmeting] * len(pool[k][1:]) for k in sorted(pool.keys())]
        current = [[i.__class__ for i in pool[k][1:]] for k in sorted(pool.keys())]
        self.assertEqual(target, current)


from parsers import convert_to_graph


class Convert_To_Graph_TestSuite(TestCase):

    def test000(self):
        "nodes are 3D tuples"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        convert_to_graph(pool, G)

        target = [tuple] * len(G.node)
        current = [i.__class__ for i in G.node]
        self.assertEqual(target, current)

        target = [2] * len(G.node)
        current = [len(i) for i in G.node]
        self.assertEqual(target, current)

    def test001(self):
        "we empty graph before we populate it"

        pool = {}
        G = nx.Graph()
        G.add_node('abc')
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        convert_to_graph(pool, G)

        target = [tuple] * len(G.node)
        current = [i.__class__ for i in G.node]
        self.assertEqual(target, current)

    def test010(self):
        "graph associates nodes with 'obj'"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        convert_to_graph(pool, G)

        target = [True] * len(G.node)
        current = ['obj' in G.node[i] for i in G.node]
        self.assertEqual(target, current)

    def test012(self):
        "graph nodes have a Put or a Rioolmeting 'obj'"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        convert_to_graph(pool, G)

        target = [True] * len(G.node)
        current = [G.node[i]['obj'].__class__ in [Put, Rioolmeting]
                   for i in G.node]
        self.assertEqual(target, current)

    def test020(self):
        "graph nodes have a Put or a Rioolmeting 'obj'"

        self.maxDiff = None
        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        convert_to_graph(pool, G)

        target = [(3.0, 0.0), (3.0, 5.0), (0.0, 1.0),
                  (3.2000000000000002, 7.4000000000000004),
                  (1.6000000000000001, 6.2000000000000002),
                  (4.0, 0.0), (2.4000000000000004, 6.7999999999999998),
                  (0.0, 6.0), (0.0, 4.0), (0.0, 5.0),
                  (2.0, 0.0), (4.0, 5.0),
                  (6.0, 5.0), (2.0, 5.0), (0.0, 2.0),
                  (0.80000000000000004, 5.5999999999999996),
                  (0.0, 3.0), (0.0, 0.0), (5.0, 0.0),
                  (5.0, 5.0), (0.0, 7.0),
                  (1.0, 5.0), (1.0, 0.0), (4.0, 8.0),
                  (0.0, 8.0)]

        current = G.node.keys()
        self.assertEqual(sorted(target), sorted(current))

        manholes = sorted([k for k in G.node if isinstance(G.node[k]['obj'], Put)])
        self.assertEqual([(0.0, 0.0), (0.0, 5.0), (0.0, 8.0),
                          (3.0, 5.0), (4.0, 8.0),
                          (5.0, 0.0), (6.0, 5.0)],
                         manholes)

        self.assertEqual([(0.0, 1.0), (1.0, 0.0)],
                         G.edge[(0.0, 0.0)].keys())
        self.assertEqual([(0.0, 6.0),
                          (0.80000000000000004, 5.5999999999999996),
                          (0.0, 4.0),
                          (1.0, 5.0)],
                         G.edge[(0.0, 5.0)].keys())
        self.assertEqual([(0.0, 7.0)],
                         G.edge[(0.0, 8.0)].keys())
        self.assertEqual([(4.0, 5.0), (2.0, 5.0)],
                         G.edge[(3.0, 5.0)].keys())
        self.assertEqual([(3.2000000000000002, 7.4000000000000004)],
                         G.edge[(4.0, 8.0)].keys())
        self.assertEqual([(4.0, 0.0)],
                         G.edge[(5.0, 0.0)].keys())
        self.assertEqual([(5.0, 5.0)],
                         G.edge[(6.0, 5.0)].keys())

    def test200(self):
        "watering a less complex network"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478.rmb", pool)
        convert_to_graph(pool, G)
        self.assertEqual([-4.5, -2.4029999999999996, -1.28], [i.z for i in pool['6400001'][1:]])
        self.assertEqual([-4.0, -2.8452994616207485, -4.0], [i.z for i in pool['6400002'][1:]])
        self.assertEqual([-1.8, -1.2000000000000002, -1.3000000000000003], [i.z for i in pool['6400003'][1:]])
        self.assertEqual([0.0, 1.046], [i.z for i in pool['6400004'][1:]])


class Compute_Lost_Water_Depth_TestSuite(TestCase):

    def test000(self):
        "watering a simple network"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        convert_to_graph(pool, G)

        compute_lost_water_depth(G, (0.0, 0.0))

        target = [((0.0, 0.0), 0.0, 0),

                  ((0.0, 1.0), 2.0, 0),
                  ((0.0, 2.0), 0.0, 2.0),
                  ((0.0, 3.0), 1.0, 1.0),
                  ((0.0, 4.0), 2.0, 0),
                  ((0.0, 5.0), 3.0, 0),

                  ((0.0, 6.0), 4.0, 0),
                  ((0.0, 7.0), 3.0, 1.0),
                  ((0.0, 8.0), 4.0, 0),

                  ((0.8, 5.6), 4.0, 0),
                  ((1.6, 6.2), 3.0, 1.0),
                  ((2.4000000000000004, 6.8), 3.0, 1.0),
                  ((3.2, 7.4), 3.0, 1.0),
                  ((4.0, 8.0), 4.0, 0),

                  ((1.0, 0.0), 2.0, 0),
                  ((2.0, 0.0), 1.0, 1.0),
                  ((3.0, 0.0), 2.0, 0),
                  ((4.0, 0.0), 3.0, 0),
                  ((5.0, 0.0), 3.0, 0),

                  ((1.0, 5.0), 4.0, 0),
                  ((2.0, 5.0), 3.0, 1.0),
                  ((3.0, 5.0), 4.0, 0),

                  ((4.0, 5.0), 4.2, 0),
                  ((5.0, 5.0), 4.6, 0),
                  ((6.0, 5.0), 5.0, 0),
                  ]

        current = [(n, G.node[n]['obj'].z, G.node[n]['obj'].flooded)
                   for n in sorted(G.node)]

        self.assertEqual(sorted(target), current)

    def test100(self):
        "watering a complex network"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/4F1 asfalt werk.RMB", pool)
        convert_to_graph(pool, G)
        manholes = sorted([k for k in G.node if isinstance(G.node[k]['obj'], Put)])
        compute_lost_water_depth(G, (138736.31, 485299.37))

    def test200(self):
        "watering a simple network, ZYB == 2 strings"

        pool = {}
        G = nx.Graph()
        parse("lizard_riool/data/f3478_2zyb2.rmb", pool)
        convert_to_graph(pool, G)
        sink = (138700.00, 485000.00)  # 64D0001
        compute_lost_water_depth(G, sink)
        target = [0, 0, 0]
        current = [
            pool['6400001'][1].flooded,
            pool['6400001'][2].flooded,
            pool['6400001'][3].flooded
            ]
        self.assertEqual(target, current)

from parsers import string_of_riool_to_string_of_rioolmeting


class String_Of_Riool_To_String_Of_Rioolmeting_TestSuite(TestCase):

    def test000(self):
        "raise error on an inconsistent request"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        self.assertRaises(KeyError,
                          string_of_riool_to_string_of_rioolmeting,
                          pool,
                          ['6400001', '6400003', '6400004'])

    def test010(self):
        "simple case: everything read in same direction"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        target = []
        target.extend(pool['6400002'][1:])
        target.extend(pool['6400003'][1:])
        target.extend(pool['6400004'][1:])
        current = string_of_riool_to_string_of_rioolmeting(pool, ['6400002', '6400003', '6400004'])
        self.assertEqual(target, current)

    def test020(self):
        "less simple case: everything read in opposite direction"

        pool = {}
        parse("lizard_riool/data/f3478-bb.rmb", pool)
        target = []
        target.extend(pool['6400002'][1:])
        target.extend(pool['6400003'][1:])
        target.extend(pool['6400004'][1:])
        target.reverse()
        current = string_of_riool_to_string_of_rioolmeting(pool, ['6400004', '6400003', '6400002'])
        self.assertEqual(target, current)

    def test030(self):
        "testing a ZYB == 2 string"

        pool = {}
        parse("lizard_riool/data/f3478.rmb", pool)
        mrios = string_of_riool_to_string_of_rioolmeting(pool, ['6400001', '6400002', '6400003', '6400004'])
        self.assertEqual(['6400004:00001.50', '6400004:00000.75'], [mrios[-2].suf_id, mrios[-1].suf_id])

