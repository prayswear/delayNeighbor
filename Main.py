import networkx as nx
import matplotlib.pyplot as plt
import random
import collections
import sys
from util import *
from IIT_UP import iit_up
from nrs import *
from workload import StationaryWorkload
import simpy
from policies import LruCache


class Config():
    def __init__(self):
        self.MIN_LINK_DELAY = 2
        self.MAX_LINK_DELAY = 10
        self.LINK_DELAY_RANGE = (self.MIN_LINK_DELAY, self.MAX_LINK_DELAY)
        self.USER_LINK_DELAY = 0
        self.SERVICE_LEVELS = [0, 1, 2]
        self.MAX_LEVEL = self.SERVICE_LEVELS[-1]
        self.DELAY_BOUNDS = [10, 25, 50]
        self.CACHE_SIZE = 10
        self.PROCESSING_CAPACITIES = [10, 10, 10]
        self.NETWORK_SIZE = 100
        self.N_CONTENT = self.NETWORK_SIZE * 10
        self.N_WARMUP = 5000
        self.N_REQUEST = 10000
        self.ALPHA = 0.9
        self.RATE = 500
        self.SEED = 1
        self.EXP_LEVEL = 1
        self.LOAD_TIME = 100


class Network(object):
    def __init__(self, topology, config):
        self.topology = topology
        self.config = config
        self.shortest_path = symmetrify_paths(dict(nx.all_pairs_dijkstra_path(topology)))
        self.delay_dict = dict(nx.shortest_path_length(topo, weight="delay"))
        self.partition = {}
        self.lnmrs_dict = {}  # {(pos,level)):LNMRS}
        self.lnmrs_partition = {}  # {(pos,level):[pos]}
        self.lnmrs_belongness = {}  # {(pos,level):pos}
        self.content_source = {}  # {content_id:pos}
        self.delay_neighbors = {}  # {(pos,level):[pos]}
        self.total_request = 0
        self.success_request = 0

    def get_lnmrs(self, pos, level):
        return self.lnmrs_dict[self.lnmrs_belongness[(pos, level)]]

    def partition_area(self):
        # 划分解析域
        self.fc_topo = full_connect(self.topology.copy(), self.delay_dict)
        self.partition = iit_up(self.fc_topo, self.config.DELAY_BOUNDS)

    def init_lnmrs(self):
        for level in self.config.SERVICE_LEVELS[::-1]:
            for hm in self.partition[level]:
                server = LNMRS(hm, level)
                self.lnmrs_dict[(hm, level)] = server
                self.lnmrs_partition[(hm, level)] = self.partition[level][hm]
                for u in self.partition[level][hm]:
                    self.lnmrs_belongness[(u, level)] = (hm, level)

    def set_cache(self):
        # 设置缓存
        for n in self.fc_topo.nodes:
            self.fc_topo.nodes[n]['cache_size'] = self.config.CACHE_SIZE
        self.cache = {node: LruCache(self.fc_topo.nodes[node]['cache_size']) for node in self.fc_topo.nodes}

    def place_content(self):
        # 放置内容
        for n in self.fc_topo.nodes:
            self.fc_topo.nodes[n]['content'] = []
        for c in range(1, self.config.N_CONTENT + 1):
            node = random.choice(self.fc_topo.nodes)
            node['content'].append(c)
            self.content_source[c] = node

    def register_contents(self):
        for n in self.fc_topo.nodes:
            for c in self.fc_topo.nodes[n]['content']:
                for level in self.config.SERVICE_LEVELS:
                    lnmrs = self.get_lnmrs(n, level)
                    lnmrs.register(c, n)

    def init_events(self):
        workload = StationaryWorkload(self.fc_topo, self.config.N_CONTENT,
                                      self.config.ALPHA, rate=self.config.RATE,
                                      n_warmup=self.config.N_WARMUP, n_measured=self.config.N_REQUEST,
                                      seed=self.config.SEED)
        self.events = workload.single_level_events(self.config.EXP_LEVEL)

    def start_simulate(self):
        self.env = simpy.Environment()
        for event in self.events:
            self.env.process(self.process_event(event))
        self.env.run()

    def cooperate_resolve(self, pos, level, lnmrs):

        pass

    def find_global_closest(self, pos, level):
        neighbors = []
        for p, l in self.lnmrs_dict.keys():
            if l == level and p != pos and self.delay_dict[pos][p] < self.config.DELAY_BOUNDS[level]:
                neighbors.append(p)
        neighbors = sorted(neighbors, key=lambda x: self.delay_dict[pos][x])
        return neighbors

    # 全局最近的邻居
    def generate_delay_neighbor_global(self):
        for pos, level in self.lnmrs_dict.keys():
            self.delay_neighbors[(pos, level)] = self.find_global_closest(pos, level)

    # 在本地查询则添加负载，负载在load_time ms后不计
    def lnmrs_load(self, lnmrs):
        lnmrs.current_load += 1
        yield self.env.timeout(self.config.LOAD_TIME)
        lnmrs.current_load -= 1

    def put_cache(self, node, content):
        if self.content_source[content] == node:
            return None
        # 如果是命中的是缓存，进行热度提升或替换
        return self.cache[node].put(content)

    # 从邻居处解析
    def process_event(self, event):
        # 0: not process; 1: success; 2: refused;
        process_flag = 0
        clock = event['timestamp']
        # 延迟到发生时间
        yield self.env.timeout(event['timestamp'])
        # 获取解析系统
        lnmrs = self.get_lnmrs(event['pos'], event['level'])
        # 传输请求到解析系统
        t_req = self.delay_dict[event['pos']][lnmrs.pos]
        clock += t_req
        yield self.env.timeout(t_req)
        # 解析
        nas = []
        if lnmrs.current_load <= self.config.PROCESSING_CAPACITIES[event['level']]:
            nas = lnmrs.resolve(event['content'])
            # 获取解析用时
            t_single_point = 0
            clock += t_single_point
            self.env.process(self.lnmrs_load(lnmrs))
            yield self.env.timeout(t_single_point)
            process_flag = 1
        else:
            process_flag = 2
        # 返回结果
        t_resp = self.delay_dict[event['pos']][lnmrs.pos]
        clock += t_resp
        yield self.env.timeout(t_resp)
        # 替换本地缓存
        delete_content = self.put_cache(event['pos'], event['content'])
        if delete_content is not None:
            lnmrs.deregister(delete_content, event['pos'])
        lnmrs.register(event['content'], event['pos'])
        hit_flag = False
        if process_flag == 1:
            hit_flag = (len(nas) > 0)
        print(event, process_flag, hit_flag, self.env.now - event['timestamp'])

        if event['log']:
            if process_flag == 1 and hit_flag == True:
                self.success_request += 1
            self.total_request += 1


if __name__ == '__main__':
    sys.setrecursionlimit(100000)
    # 配置
    config = Config()
    # 生成机房拓扑
    topo = nx.barabasi_albert_graph(config.NETWORK_SIZE, 1, seed=config.SEED)
    for u, v in topo.edges:
        topo[u][v]["delay"] = random.uniform(*config.LINK_DELAY_RANGE)

    # 初始化网络
    network = Network(topo, config)
    network.partition_area()
    network.set_cache()
    network.place_content()
    network.init_lnmrs()
    network.register_contents()
    network.init_events()
    network.start_simulate()
    print(network.total_request)
    print(network.success_request / network.total_request)

    # TODO 简化排队模型，固定1ms，1秒内不超过xx，超过则拒绝（或转发走） OK
    # TODO 节点加缓存和LRU替换算法 OK
    # TODO 加LCE策略？
