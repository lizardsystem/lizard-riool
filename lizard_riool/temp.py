def temp():
    import models, parsers, logging
    reload(models)
    reload(parsers)
    import networkx as nx

    global pool
    pool = {}
    global G
    G = nx.Graph()

    parsers.parse("/home/mario/Local/office.nelen-schuurmans.nl/svn/Products/sites/almere/trunk/src/lizard-riool/lizard_riool/data/f3478.rmb", pool)
    parsers.convert_to_graph(pool, G)
    parsers.compute_lost_water_depth(G, (138700.0, 485000.0))

    parsers.compute_lost_volume(G)

    global rl
    rl = sorted(set([G.edge[k1][k2]['segment'] for (k1, k2) in G.edges() if isinstance(G.edge[k1][k2].get('obj'), models.Rioolmeting)]))    

    print [(i.volume, i.volume_lost) for i in rl]
