from copy              import copy
from itertools         import pairwise
from json              import dumps
from numpy             import chararray

import lib.utilities   as util

class Visualizer:

  def __init__(self, factory_map, installations, num_agents, prefix=""):

    self.ncols               = factory_map.ncols
    self.nrows               = factory_map.nrows
    self.map                 = chararray((self.nrows, self.ncols), itemsize=1, unicode=True)
    self.map[:]              = "."
    self.installation_input  = {}
    self.installation_output = {}
    self.installation_label  = {}

    # Construct map
    for junction in factory_map.junctions:
      self.set_pt(junction.cell, "!")

    for road in factory_map.roads:
      for u,v in pairwise(road.path):
        self.set_pt(u, util.direction_of_v_from_u(u, v))
      self.set_pt(road.path[-1], util.direction_of_v_from_u(road.path[-1], road.junction_en.cell))

    for cell in factory_map.workstation_cells:
      self.set_pt(cell, "t")

    for cell in factory_map.machine_cells:
      self.set_pt(cell, "#")

    # Installation information
    i_map = copy(installations.workstations)
    i_map.update(installations.machines)

    self.i_input  = {xid:x.input_cell.to_tuple()  for xid,x in i_map.items() if x.input_cell}
    self.i_output = {xid:x.output_cell.to_tuple() for xid,x in i_map.items() if x.output_cell}
    self.i_label  = {xid:x.label_cell.to_tuple()  for xid,x in i_map.items()}

    self.token_to_color = {}

    with open(f"{prefix}tmp/map.json", "w") as f:
      map_info = {"map"                 : self.serialize_map(),
                  "installation_input"  : self.i_input,
                  "installation_output" : self.i_output,
                  "installation_label"  : self.i_label,
                  "num_agents"          : num_agents}       
      f.write(dumps(map_info, indent=2))

  def generate_state(self, agents):

    pos   = {agent.id: [agent.cell.x, agent.cell.y] for agent in agents}
    cargo = {agent.id: dict(agent.cargo)            for agent in agents}

    state_info     = {"pos":   pos,
                      "cargo": cargo}


    with open("tmp/state.json", "w") as f:      
      f.write(dumps(state_info, indent=2))

  def set_pt(self, pt, val):
    self.map[self.nrows - pt.y - 1][pt.x] = val

  def serialize_map(self):
    return ["".join(row) for row in self.map]

  def print_map(self):
    for row in self.serialize_map():
      print(row)
