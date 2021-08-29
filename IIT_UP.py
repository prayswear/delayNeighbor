import sys

from pyscipopt import Model

from util import *


def iit_up(G, delays):
    partition = {}
    max_sub_delays = {}
    index = 0
    partition[index] = partition_for_single_layer(G.copy(), delays[index])
    max_sub_delays[index] = {}
    for hm in partition[index].keys():
        max_delay = 0
        for node in partition[index][hm]:
            if not hm == node and G[hm][node]["delay"] > max_delay:
                max_delay = G[hm][node]["delay"]
        max_sub_delays[index][hm] = max_delay
    index += 1
    while index < len(delays):
        current_layer_partition = partition_for_single_layer(G.copy(), delays[index],
                                                             list(partition[index - 1].keys()),
                                                             max_sub_delays[index - 1])
        partition[index] = {}
        for key in current_layer_partition.keys():
            partition[index][key] = []
            for value in current_layer_partition[key]:
                partition[index][key] += partition[index - 1][value]
        max_sub_delays[index] = {}
        for hm in partition[index].keys():
            max_delay = 0
            for node in partition[index][hm]:
                if not hm == node and G[hm][node]["delay"] > max_delay:
                    max_delay = G[hm][node]["delay"]
            max_sub_delays[index][hm] = max_delay
        index += 1
    return partition


def partition_for_single_layer(G, T, nodes=None, delays_up=None):
    if not nodes == None:
        G = G.subgraph(nodes).copy()
    if not delays_up == None:
        for node in G.nodes:
            edges_to_remove = []
            for neighbor in G.adj[node]:
                if G[node][neighbor]["delay"] > (T - delays_up[node]):
                    edges_to_remove.append((node, neighbor))
            G.remove_edges_from(edges_to_remove)
    else:
        remove_edges_by_delay(G, T)
    partition = {}
    dominators = MDS_relaxation(G)
    for hm in dominators:
        partition[hm] = set()
        partition[hm].add(hm)
        G.nodes[hm]["dominator"] = True
    dominatees = set(G.nodes).difference(set(dominators))
    for node in dominatees:
        G.nodes[node]["dominator"] = False
    for node in G.nodes:
        remove_list = []
        for neighbor in G.adj[node]:
            if G.nodes[node]["dominator"] == G.nodes[neighbor]["dominator"]:
                remove_list.append((node, neighbor))
        G.remove_edges_from(remove_list)
    for node in dominatees:
        neighbors = list(G.adj[node])
        min_delay = sys.maxsize
        choosed_node = -1
        for neighbor in neighbors:
            if G[node][neighbor]["delay"] < min_delay:
                min_delay = G[node][neighbor]["delay"]
                choosed_node = neighbor
        partition[choosed_node].add(node)
    return partition


def MDS_relaxation(graph):
    mds = []
    model = Model("MDS_relaxation")
    varDict = {}
    for node in graph.nodes:
        varDict[node] = model.addVar(str(node), lb=0, ub=1)
    for node in graph.nodes:
        total = varDict[node]
        for neighbor in graph.adj[node]:
            total = total + varDict[neighbor]
        model.addCons(total >= 1)
    model.setObjective(sum(varDict.values()))
    # model.hideOutput()
    model.optimize()
    for key in varDict.keys():
        if model.getVal(varDict[key]) > 0:
            mds.append(key)
    return mds
