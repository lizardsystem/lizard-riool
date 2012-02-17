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

from unittest import TestCase
import networkx as nx
from parsers import dfs_preorder_nodes

class Dfs_Preorder_Nodes_TestSuite(TestCase):

    def test000(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 0)
        C = (0, 2, 0)
        D = (0, 3, 0)
        E = (0, 4, 0)
        G.add_edges_from([(A,B),(B,C),(C,D),(D,E)])
        current = dfs_preorder_nodes(G, A, set(), lambda a,b: True)
        target = ([A, B, C, D, E], [])
        self.assertEqual(target, current)

    def test010(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 0)
        C = (0, 2, 0)
        D = (0, 3, 0)
        E = (0, 4, 0)
        G.add_edges_from([(A,B),(B,C),(C,D),(D,E)])
        current = dfs_preorder_nodes(G, D, set([A, B, C]), lambda a,b: True)
        target = ([D, E], [])
        self.assertEqual(target, current)

    def test020(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 0)
        C = (0, 2, 0)
        D = (0, 3, 1)
        E = (0, 4, 1)
        G.add_edges_from([(A,B),(B,C),(C,D),(D,E)])
        current = dfs_preorder_nodes(G, A, set(), 
                                     lambda a,b: b[2] <= 0)
        target = ([A, B, C, ], [(C, D)])
        self.assertEqual(target, current)

    def test030(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 1)
        C = (0, 2, 4)
        D = (0, 3, 5)
        E = (0, 4, 8)
        G.add_edges_from([(A,B),(B,C),(C,D),(D,E)])
        current = dfs_preorder_nodes(G, A, set(), 
                                     lambda p,c: c[2] - p[2] <= 1)
        target = ([A, B, ], [(B, C)])
        self.assertEqual(target, current)

    def test032(self):
        G = nx.Graph()
        A = (0, 0, 0)
        B = (0, 1, 1)
        C = (0, 2, 4)
        D = (0, 3, 5)
        E = (0, 4, 8)
        G.add_edges_from([(A,B),(B,C),(C,D),(D,E)])
        current = dfs_preorder_nodes(G, C, set([A, B]), 
                                     lambda p,c: c[2] - p[2] <= 1)
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
        G.add_edges_from([(A,B),(A,C),(C,D),(C,E)])
        current = dfs_preorder_nodes(G, A, set(), 
                                     lambda p,c: c[2] - p[2] <= 1)
        target = ([A, B, ], [(A, C)])
        self.assertEqual(target, current)
        current = dfs_preorder_nodes(G, C, set([A, B]), 
                                     lambda p,c: c[2] - p[2] <= 1)
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
        G.add_edges_from([(A,B),(A,D),(C,D),(B,C),(C,E)])
        current = dfs_preorder_nodes(G, A, set(), 
                                     lambda p,c: c[1] - p[1] <= 1)
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
        G.add_edges_from([(A,B),(A,D),(C,D),(B,C),(C,E)])
        current = dfs_preorder_nodes(G, A, set(), 
                                     lambda p,c: c[1] - p[1] <= 1)
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
        G.add_edges_from([(A,AB1),(AB1,AB2),(AB2,AB3),(AB3,AB4),(AB4,B)])
        current = dfs_preorder_nodes(G, A, set(), 
                                     lambda p,c: c[1] >= p[1])
        target = ([A, AB1, ], [(AB1, AB2)])
        self.assertEqual(target, current)


from parsers import examine_graph
from models import Put


class Examine_Graphtestsuite(TestCase):

    def test000(self):
        """
        A---B---C---D---E---F
        levels:
        5   6   5   4   6   8
        result:
        0   0   1   2   0   0
        """
        G = nx.Graph()
        nodes = [("A", Put(coords=(0,0,5))),
                 ("B", Put(coords=(0,1,6))),
                 ("C", Put(coords=(0,2,5))),
                 ("D", Put(coords=(0,3,4))),
                 ("E", Put(coords=(0,4,6))),
                 ("F", Put(coords=(0,5,8)))]
        for label, obj in nodes:
            G.add_node(label, obj=obj)
        for (p, x), (c, y) in zip(nodes, nodes[1:]):
            G.add_edge(p, c)

        examine_graph(G, "A")

        self.assertEqual(0, G.node["A"]['obj'].flooded)
        self.assertEqual(0, G.node["B"]['obj'].flooded)
        self.assertEqual(1, G.node["C"]['obj'].flooded)
        self.assertEqual(2, G.node["D"]['obj'].flooded)
        self.assertEqual(0, G.node["E"]['obj'].flooded)
        self.assertEqual(0, G.node["F"]['obj'].flooded)
