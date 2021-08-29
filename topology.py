import networkx as nx
import random


def get_graph(size, degree, seed):
    return ba_graph(size, degree, seed)


def ba_graph(size, degree, seed):
    random.seed(seed)
    return nx.barabasi_albert_graph(size, degree, seed)
