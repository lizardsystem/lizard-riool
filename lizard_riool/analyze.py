"Exploration of data and algorithms."


def node_to_sink(g, node, sink, tops, paths=[]):
    """Algorithm to find the maximum barrier from node to sink.
    """

    try:
        # We are interested in a path, not
        # necessarily the shortest path.
        path = nx.shortest_path(g, node, sink)
    except nx.NetworkXNoPath:
        return

    paths.append(path)

    if node == sink:
        tops.append(None)
        return

    max_height = -float('Inf')
    for i in range(1, len(path)):
        n = path[i - 1]
        m = path[i]
        height = max(g.node[n][m], g.node[m][n])
        if height > max_height:
            max_height = height
            max_edge = (n, m)

    tops.append(max_height)
    g.remove_edge(*max_edge)
    node_to_sink(g, node, sink, tops, paths)


def hiding_script():
    from models import Riool
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    import networkx as nx

# Only 1 network is assumed.

    G = nx.Graph()

    for riool in Riool.objects.all():
        G.add_edge(riool.AAD, riool.AAF)
        G.node[riool.AAD][riool.AAF] = riool.ACR
        G.node[riool.AAF][riool.AAD] = riool.ACS


# Adapt to your needs
    sink = '228/1'

# Find lowest barrier
    for node in G.nodes():
        tops = []
        node_to_sink(G.copy(), node, sink, tops)
        G.node[node]['top'] = min(tops)

# Assign colors for visualisation
    for n, m in G.edges():
        if G.node[n][m] >= G.node[n]['top'] and G.node[m][n] >= G.node[m]['top']:
            G[n][m]['color'] = 'green'
        elif G.node[n][m] < G.node[n]['top'] and G.node[m][n] < G.node[m]['top']:
            G[n][m]['color'] = 'red'
        elif G.node[n]['top'] == G.node[m][n] or G.node[m]['top'] == G.node[n][m]:
            G[n][m]['color'] = 'orange'
        elif (G.node[n][m] >= G.node[n]['top'] and G.node[m][n] < G.node[m]['top']
              or G.node[m][n] >= G.node[m]['top'] and G.node[n][m] < G.node[n]['top']):
            G[n][m]['color'] = 'yellow'
        else:
            G[n][m]['color'] = 'black'

################################################

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    putten = {}

    for riool in Riool.objects.all():

        string = riool.the_geom

        x = []
        y = []
        z = []

        point = string[0]
        x.append(point[0])
        y.append(point[1])
        z.append(riool.ACR)

        point = string[1]
        x.append(point[0])
        y.append(point[1])
        z.append(riool.ACS)

        color = G[riool.AAD][riool.AAF]['color']

        ax.plot(x, y, z, color)

        putten[riool.AAD] = (riool.AAE.x, riool.AAE.y, riool.ACR)
        putten[riool.AAF] = (riool.AAG.x, riool.AAG.y, riool.ACS)

    foo = {}

    for riool in Riool.objects.all():

        xyz = (riool.AAE.x, riool.AAE.y, riool.ACR)
        if riool.AAD in foo:
            foo[riool.AAD].append(xyz)
        else:
            foo[riool.AAD] = [xyz]

        xyz = (riool.AAG.x, riool.AAG.y, riool.ACS)
        if riool.AAF in foo:
            foo[riool.AAF].append(xyz)
        else:
            foo[riool.AAF] = [xyz]

    for value in foo.itervalues():
        x = []
        y = []
        z = []
        for n, k in enumerate(value[:-1]):
            x.append(value[n][0])
            y.append(value[n][1])
            z.append(value[n][2])
            x.append(value[n + 1][0])
            y.append(value[n + 1][1])
            z.append(value[n + 1][2])
        if len(x) > 0:
            ax.plot(x, y, z, 'k:')

    G = nx.Graph()

    for riool in Riool.objects.all():
        G.add_edge(riool.AAD, riool.AAF)
        G.node[riool.AAD][riool.AAF] = riool.ACR
        G.node[riool.AAF][riool.AAD] = riool.ACS

    xyz = putten[sink]
    ax.plot([xyz[0]], [xyz[1]], [xyz[2]], 'x')

    plt.legend()
    plt.show()
