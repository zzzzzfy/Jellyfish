import random
from collections import defaultdict

class JellyfishNet:
	def __init__(self, num_switches, num_switch_ports, num_servers, num_server_ports):
		self.num_switches = num_switches
		self.num_switch_ports = num_switch_ports
		self.switch_graph = defaultdict(set)
		self.open_switches = set(range(num_switches))
		self.all_switches = set(range(num_switches))
		self.construct_random_network()

		self.num_servers = num_servers
		self.num_server_ports = num_server_ports
		self.all_servers = set(range(num_servers))
		self.server_to_switch = {}
		self.attach_servers();

	def connect(self, switch1, switch2):
		self.switch_graph[switch1].add(switch2)
		self.switch_graph[switch2].add(switch1)

		if len(self.switch_graph[switch1]) == self.num_switch_ports:
			self.open_switches.remove(switch1)
		if len(self.switch_graph[switch2]) == self.num_switch_ports:
			self.open_switches.remove(switch2)

	def disconnect(self, switch1, switch2):
		if len(self.switch_graph[switch1]) == self.num_switch_ports:
			self.open_switches.add(switch1)
		if len(self.switch_graph[switch2]) == self.num_switch_ports:
			self.open_switches.add(switch2)

		self.switch_graph[switch1].remove(switch2)
		self.switch_graph[switch2].remove(switch1)

	def rand_node(self, candidates, _except):
		candidates = list(candidates)
		a = random.choice(candidates)
		while a == _except:
			a = random.choice(candidates)
		return a

	def construct_random_network(self):
		while len(self.open_switches) > 2 :
			switch1, switch2 = random.sample(self.open_switches, 2)
			self.connect(switch1, switch2)

		while len(self.open_switches) == 1:
			switch = list(self.open_switches)[0]
			if (self.num_switch_ports - len(self.switch_graph[switch])) == 1:
				rand_neighbor = random.choice(list(self.switch_graph[switch]))
				self.disconnect(switch, rand_neighbor)
			
			other1 = self.rand_node(self.all_switches, switch)
			other2 = self.rand_node(self.switch_graph[other1], switch)
			self.disconnect(other1, other2)
			self.connect(other1, switch)
			self.connect(other2, switch)

	def attach_servers(self):
		if self.num_servers > self.num_switches * self.num_server_ports:
			print("Not enough switches to support server capacity")
			raise(Exception())
		switches = list(range(self.num_switches * self.num_server_ports))
		random.shuffle(switches)
		for i in range(self.num_servers):
			self.server_to_switch[i] = switches[i] // self.num_server_ports

	def generate_server_traffic(self):
		self.server_sender_traffic = defaultdict(int)
		candidates = self.all_servers.copy()
		for sender in self.all_servers:
			receiver = self.rand_node(candidates, sender)
			self.server_sender_traffic[sender] = receiver
			candidates.remove(receiver)
		return self.server_sender_traffic

def BFS(graph, src, dst, limit):
    paths = []
    paths_queue = [[src]]

    while len(paths_queue) > 0:
        path = paths_queue.pop(0)
        node = path[-1]
        if node == dst:
            paths.append(path)
            if len(paths) >= limit:
                break
        else:
            for neighbor in [n_ for n_ in graph[node] if n_ not in path]:
                paths_queue.append(path + [neighbor])
    return paths

def init_counter(counter, switch_graph):
	for src, neighbor in switch_graph.items():
		for dst in neighbor:
			counter[str(src) + '-' + str(dst)] = 0

ecmp_8_way = {}
ecmp_64_way = {}
shortest_8_way = {}

def update_path(path, counter):
	last = -1
	for i in path:
		if last != -1:
			switch1 = last
			switch2 = i
			'''
			if switch2 < switch1:
				switch2 = last
				switch1 = i
			'''
			counter[str(switch1) + '-' + str(switch2)] = 1 + counter[str(switch1) + '-' + str(switch2)]
		last = i

def update_paths(paths):
	length = len(paths[0])
	cnt = 0
	for path in paths:
		if len(path) == length:
			if cnt < 8:
				update_path(path, ecmp_8_way)
			if cnt < 64:
				update_path(path, ecmp_64_way)
		if cnt < 8:
			update_path(path, shortest_8_way)
		cnt = cnt + 1

switches = 212
switch_links = 13
servers = 686
server_ports = 23

jf = JellyfishNet(switches, switch_links, servers, server_ports)
sender_traffic = jf.generate_server_traffic()

init_counter(ecmp_8_way, jf.switch_graph)
init_counter(ecmp_64_way, jf.switch_graph)
init_counter(shortest_8_way, jf.switch_graph)

for sender, receiver in sender_traffic.items():
		sender_switch = jf.server_to_switch[sender]
		receiver_switch = jf.server_to_switch[receiver]
		if sender_switch == receiver_switch:
			continue
		paths = BFS(jf.switch_graph, sender_switch, receiver_switch, 64)
		update_paths(paths)
		
print(len(sender_traffic))

import matplotlib.pyplot as plt

plt.plot(sorted(shortest_8_way.values()), color='blue', label="8 Shortest Paths")
plt.plot(sorted(ecmp_64_way.values()), color='red', label='64-way ECMP')
plt.plot(sorted(ecmp_8_way.values()), color='green', label='8-way ECMP')
plt.title("Figure 9 Replication")
plt.ylabel('# Distinct Paths Link is on')
plt.xlabel('Rank of Link')
plt.legend(loc=2)
fig_path = 'figure9.png'
plt.savefig(fig_path)
