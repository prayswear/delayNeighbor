import random

import math
import matplotlib.pyplot as plt
import networkx as nx


def symmetrify_paths(shortest_paths):
    for u in shortest_paths:
        for v in shortest_paths[u]:
            shortest_paths[u][v] = list(reversed(shortest_paths[v][u]))
    return shortest_paths


def full_connect(topo, delay_dict):
    network_size = len(topo.nodes)
    for u in range(network_size):
        v = u + 1
        while v < network_size:
            topo.add_edge(u, v, delay=delay_dict[u][v])
            v += 1
    return topo


def graph_generater(size, weight_range, seed=0):
    G = nx.barabasi_albert_graph(size, 1, seed)
    random.seed(seed)
    for i, j in G.edges:
        G[i][j]["delay"] = random.uniform(weight_range[0], weight_range[1])
    delay_dict = dict(nx.shortest_path_length(G, weight="delay"))
    for i in range(size):
        j = i + 1
        while j < size:
            G.add_edge(i, j, delay=delay_dict[i][j])
            j += 1
    return G


def graph_generater1(scale):
    G = nx.barabasi_albert_graph(scale, 1, 0)
    random.seed(1)
    for i, j in G.edges:
        G[i][j]["delay"] = random.uniform(0, 10)
    length_dict = dict(nx.shortest_path_length(G, weight="delay"))
    for i in range(scale):
        for j in range(scale):
            if not i == j:
                G.add_edge(i, j, delay=length_dict[i][j])
    return G


def remove_edges_by_delay(G, T):
    edges_to_remove = []
    for u, v in G.edges:
        if G[u][v]["delay"] > T:
            edges_to_remove.append((u, v))
    G.remove_edges_from(edges_to_remove)
    return G


def show_partition(partition):
    hm_set = set()
    for i in range(len(partition))[::-1]:
        print("level " + str(i) + " has " + str(len(partition[i])) + " hms")
        # print(str(len(partition[i])) + "\t", end="")
        for hm in partition[i]:
            hm_set.add(hm)
    # print("Total: " + str(len(hm_set)))
    # print(str(len(hm_set)))


def degree_distribution(G, node_list=None, draw=True):
    if node_list == None:
        node_list = list(G.nodes)
    degree_dict = {}
    for node in node_list:
        degree = G.degree(node)
        if degree in degree_dict.keys():
            degree_dict[degree] += 1
        else:
            degree_dict[degree] = 1
    if draw:
        plt.scatter([math.log(x) for x in degree_dict], [math.log(x) for x in degree_dict.values()], s=10)
        plt.show()
    return degree_dict


def random_insert_and_delete_edges(graph, k, seed=0):
    graph_new = graph.copy()
    nodes = graph_new.nodes
    count = 0
    while count < k:
        edges = list(graph_new.edges)
        random.seed(seed)
        v_i, v_j = random.sample(nodes, 2)
        if not v_i in graph_new.adj[v_j]:
            graph_new.add_edge(v_i, v_j)
            edge = random.choice(edges)
            graph_new.remove_edges_from([edge])
            count += 1
        seed += 1
    return graph_new

def inheritdoc(cls):
    """Decorator that inherits docstring from the overridden method of the
    superclass.

    Parameters
    ----------
    cls : Class
        The superclass from which the method docstring is inherit

    Notes
    -----
    This decorator requires to specify the superclass the contains the method
    (with the same name of the method to which this decorator is applied) whose
    docstring is to be replicated. It is possible to implement more complex
    decorators which identify the superclass automatically. There are examples
    available in the Web (e.g., http://code.activestate.com/recipes/576862/),
    however, the increased complexity leads to issues of interactions with
    other decorators.
    This implementation is simple, easy to understand and works well with
    Icarus code.
    """

    def _decorator(function):
        # This assignment is needed to maintain a reference to the superclass
        sup = cls
        name = function.__name__
        function.__doc__ = eval('sup.%s.__doc__' % name)
        return function

    return _decorator

def path_links(path):
    """Convert a path expressed as list of nodes into a path expressed as a
    list of edges.

    Parameters
    ----------
    path : list
        List of nodes

    Returns
    -------
    path : list
        List of edges
    """
    return [(path[i], path[i + 1]) for i in range(len(path) - 1)]


def degree_preserving_rewiring(graph, k, seed=0):
    graph_new = graph.copy()
    count = 0
    while count < k:
        edges = list(graph_new.edges)
        random.seed(seed)
        edge1, edge2 = random.sample(edges, 2)
        # print(edge1, edge2)
        v_i, v_j = edge1
        v_h, v_k = edge2
        if v_i in edge2 or v_j in edge2:
            seed += 1
            continue
        if not v_i in graph_new.adj[v_k] and not v_j in graph_new.adj[v_h]:
            graph_new.remove_edges_from([edge1, edge2])
            # print("rm " + str(edge1) + " " + str(edge2))
            graph_new.add_edges_from([(v_i, v_k), (v_j, v_h)])
            # print("add " + str(v_i), str(v_k), str(v_j), str(v_h))
            count += 1
        seed += 1
    return graph_new
