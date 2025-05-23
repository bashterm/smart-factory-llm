import json
from copy import deepcopy
from itertools import product
import matplotlib.pyplot as plt
import networkx as nx

import lib.utilities as util
from lib.scenario import Machine
from lib.layout import Layout

class Factory(Layout):

  __slots__ = ('machines', 'floorplan', 'factory_map', 'cell_graph', 'timesteps', 'cell_to_input', 'cell_to_output', 'agent_limit')

  def __init__(self, machines: list[Machine], floorplan: list[list[str]], timesteps: int, agent_limit: int):
    self.machines = machines
    self.floorplan = deepcopy(floorplan)
    self.factory_map = floorplan
    self.timesteps = timesteps
    self.agent_limit = agent_limit

    self._init_factory()

  def _init_factory(self):
    for m in self.machines:
      self.add_tile(m.get_input(),  'i')
      self.add_tile(m.get_output(), 'o')
      for pt in m.get_chassis(): self.add_tile(pt, 'c') 
      self.add_tile(m.position, 'a')

    self._create_factory_graph()

    self.cell_to_input  = {m.get_input():m  for m in self.machines}
    self.cell_to_output = {m.get_output():m for m in self.machines}

  @staticmethod
  def from_layout(layout: Layout):
    return Factory(layout.machines, deepcopy(layout.floorplan), layout.timesteps, layout.agent_limit)
     
     
  def add_tile(self, pt: util.Point, tile: str):
    """
    Add a tile to the factory map

    Parameters:
    - pt (util.Point): The point with x and y coordinates at which to add the tile to the map
    - c (str): A single character string representing the tile type to be added
    """
    if pt is not None:
      self.factory_map[pt.y][pt.x] = tile

  def cell_blocked(self, pt):
    if pt.x < 0 or pt.y < 0: return True
    if pt.y >= len(self.factory_map) or pt.x >= len(self.factory_map[0]): return True
    if self.factory_map[pt.y][pt.x] in ('c', 'a'): return True
    return False

  def _create_factory_graph(self):

    self.cell_graph = nx.Graph()

    # Add nodes and self-loop edges
    for x, y in product(range(len(self.factory_map[0])), range(len(self.factory_map))):
      pt = util.Point(x, y)
      if self.cell_blocked(pt): continue 
      
      self.cell_graph.add_node(pt, ctype=self.factory_map[pt.y][pt.x])
      self.cell_graph.add_edge(pt, pt) # Add a self-edge to allow tokens to loop

    # Add edges to neighbours
    for x, y in product(range(len(self.factory_map[0])), range(len(self.factory_map))):
      pt = util.Point(x, y)
      if self.cell_blocked(pt): continue 
      
      for dx, dy in [(0,1),(1,0),(0,-1),(-1,0)]:
        adj_pt = util.Point(x + dx, y + dy)
        if self.cell_blocked(adj_pt): continue
        self.cell_graph.add_edge(pt, adj_pt)
    
    show_graph = False

    def node_color(ctype):
      match ctype:
        case '.':
          return "#f2f2f2"
        case 'i':
          return '#d6f2f5'
        case 'o':
          return '#fff3bb'
        case 'a' | 'c':
          return "#d5d5d5"
        case _:
          return 'black'


    if show_graph:
      fig = plt.figure()
      nx.draw(self.cell_graph, 
              pos        = {n:(n.x, n.y) for n in self.cell_graph.nodes()},
              node_color = [node_color(self.factory_map[pt.y][pt.x]) for pt in self.cell_graph.nodes()],
              edgecolors = "k")

      plt.show()



  def cell_to_input_machine(self, cell):
    return self.cell_to_input.get(cell, None)

  def cell_to_output_machine(self, cell):
    return self.cell_to_output.get(cell, None)
      
  def print_factory_map(self):
    """
    Print the factory map to standard output
    """
    for row in reversed(self.factory_map):
      print("".join(row))

  def export_factory(self, vis_map_path: str):
    vis = {"fmap":    self.factory_map[::-1],
           "inputs":  {m.machine_id: [m.get_input().x,  m.get_input().y]  for m in self.machines if m.get_input() is not None},
           "outputs": {m.machine_id: [m.get_output().x, m.get_output().y] for m in self.machines if m.get_output() is not None},
           "anchors": {m.machine_id: [m.position.x,          m.position.y]          for m in self.machines}}

    with open(vis_map_path, "w") as file:
      json.dump(vis, file) 